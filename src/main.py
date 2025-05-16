import asyncio
from viam.module.module import Module
try:
    from models.people_piezo import PeoplePiezo
except ModuleNotFoundError:
    # when running as local module with run.sh
    from .models.people_piezo import PeoplePiezo


if __name__ == '__main__':
    asyncio.run(Module.run_from_registry())
