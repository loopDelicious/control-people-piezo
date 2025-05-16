from typing import ClassVar, Final, Mapping, Optional, Sequence, cast

from typing_extensions import Self
from viam.proto.app.robot import ComponentConfig
from viam.proto.common import ResourceName
from viam.resource.base import ResourceBase
from viam.resource.easy_resource import EasyResource
from viam.resource.types import Model, ModelFamily
from viam.services.generic import *
from viam.utils import ValueTypes, struct_to_dict
from viam.services.vision import VisionClient
from viam.components.generic import Generic as GenericComponent
from viam.components.camera import Camera
import asyncio
from threading import Event
from viam.logging import getLogger

LOGGER = getLogger("piezo-alarm")

class PeoplePiezo(Generic, EasyResource):

    MODEL: ClassVar[Model] = Model(
        ModelFamily("joyce", "control-people-piezo"), "people-piezo"
    )

    running = None
    task = None
    event = Event()

    @classmethod
    def new(
        cls, config: ComponentConfig, dependencies: Mapping[ResourceName, ResourceBase]
    ) -> Self:
        """This method creates a new instance of this Generic service.
        The default implementation sets the name from the `config` parameter and then calls `reconfigure`.

        Args:
            config (ComponentConfig): The configuration for this resource
            dependencies (Mapping[ResourceName, ResourceBase]): The dependencies (both implicit and explicit)

        Returns:
            Self: The resource
        """
        return super().new(config, dependencies)

    @classmethod
    def validate_config(cls, config: ComponentConfig) -> Sequence[str]:
        """This method allows you to validate the configuration object received from the machine,
        as well as to return any implicit dependencies based on that `config`.

        Args:
            config (ComponentConfig): The configuration for this resource

        Returns:
            Sequence[str]: A list of implicit dependencies
        """
        attrs = struct_to_dict(config.attributes)
        required_dependencies = ["vision", "generic", "camera"]
        implicit_dependencies = []

        for component in required_dependencies:
            if component not in attrs or not isinstance(attrs[component], str):
                raise ValueError(f"{component} is required and must be a string")
            else:
                implicit_dependencies.append(attrs[component])
        return implicit_dependencies

    def reconfigure(
        self, config: ComponentConfig, dependencies: Mapping[ResourceName, ResourceBase]
    ):
        """This method allows you to dynamically update your service when it receives a new `config` object.

        Args:
            config (ComponentConfig): The new configuration
            dependencies (Mapping[ResourceName, ResourceBase]): Any dependencies (both implicit and explicit)
        """
        attrs = struct_to_dict(config.attributes)
        vision_resource = dependencies.get(VisionClient.get_resource_name(str(attrs.get("vision"))))
        self.vision = cast(VisionClient, vision_resource)
        piezo_resource = dependencies.get(GenericComponent.get_resource_name(str(attrs.get("generic"))))
        self.piezo = cast(GenericComponent, piezo_resource)
        camera_resource = dependencies.get(Camera.get_resource_name(str(attrs.get("camera"))))
        self.camera_name = cast(Camera, camera_resource).name

        if self.running is None:
            self.start()
        else:
            self.logger.info("Already running control logic.")

        return super().reconfigure(config, dependencies)
    
    def start(self):
       loop = asyncio.get_event_loop()
       self.task = loop.create_task(self.control_loop())
       self.event.clear()

    def stop(self):
        self.event.set()
        if self.task is not None:
            self.task.cancel()

    async def control_loop(self):
        while not self.event.is_set():
            await self.on_loop()
            await asyncio.sleep(0)

    async def on_loop(self):
        try:
            self.logger.info("Executing control logic")

            self.person_detected_last_time = False  # Initialize state tracking

            N = 100
            for i in range(N):
                try:
                    self.logger.info(f"Iteration {i+1}/{N}")
                    detections = await self.vision.get_detections_from_camera(self.camera_name)
                    self.logger.info(f"Raw Detections: {detections}")

                    found = False
                    for d in detections:
                        self.logger.info(f"Detection: class_name={d.class_name}, confidence={d.confidence}")
                        if d.confidence > 0.8 and d.class_name.lower() == "person":
                            found = True
                            break

                    if found and not self.person_detected_last_time:
                        self.logger.info("New person detected! Buzzing.")
                        await self.piezo.do_command({
                            "sound_buzzer": {
                                "frequency": 1200,
                                "duration": 1.5,
                                "duty_cycle": 0.7
                            }
                        })
                    elif not found and self.person_detected_last_time:
                        self.logger.info("Person no longer detected.")

                    self.person_detected_last_time = found

                except Exception as e:
                    self.logger.error(f"Error during loop iteration: {e}")

                await asyncio.sleep(1)

        except Exception as err:
            self.logger.error(err)
        await asyncio.sleep(10)


    def __del__(self):
        self.stop()

    async def close(self):
        self.stop()

    async def do_command(
        self,
        command: Mapping[str, ValueTypes],
        *,
        timeout: Optional[float] = None,
        **kwargs
    ) -> Mapping[str, ValueTypes]:

        result = {key: False for key in command.keys()}
        for name, args in command.items():
            if name == "action" and args == "start":
                self.start()
                result[name] = True
            if name == "action" and args == "stop":
                self.stop()
                result[name] = True
        return result

