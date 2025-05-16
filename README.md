# Module control-people-piezo

Control module to trigger a piezo buzzer when a person is detected on a webcam.

## Model joyce:control-people-piezo:people-piezo

Trigger a piezo buzzer when a person is detected on a webcam!

### Configuration

The following attribute template can be used to configure this model:

```json
{
  "camera": <string>,
  "generic": <string>,
  "vision": <string>
}
```

#### Attributes

The following attributes are available for this model:

| Name      | Type   | Inclusion | Description                                |
| --------- | ------ | --------- | ------------------------------------------ |
| `camera`  | string | Required  | Name of the camera in the Viam app         |
| `generic` | string | Required  | Name of the piezo buzzer in the Viam app   |
| `vision`  | string | Required  | Name of the vision service in the Viam app |

#### Example Configuration

```json
{
  "camera": "camera-1",
  "generic": "generic-1",
  "vision": "people-detector"
}
```
