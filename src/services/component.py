import json
from flask import Request, redirect, url_for
from src.repositories.component import ComponentRepository
from src.repositories.device import DeviceRepository
from src.services.device import DeviceService


class ComponentService:
    def __init__(
        self,
        component_repository: ComponentRepository,
        device_repository: DeviceRepository,
        device_service: DeviceService,
    ):
        self.component_repository = component_repository
        self.device_repository = device_repository
        self.device_service = device_service


    def create_component(self, device_id, request: Request):
        device = self.device_repository.get(device_id)
        if device is None:
            print("dispositivo não encontrado")
            return redirect(url_for("list_devices"))
        print(f"adicionar componente no dispositivo #{device_id}")
        component_dict = request.form
        print(component_dict)
        component_type = component_dict.get("componentType")
        match component_type:
            case "servo":
                servo_component_data = {
                    "component_type": component_type,
                    "config_json": json.dumps({
                        "id": component_dict.get("servo_id"),
                        "output": component_dict.get("output_id"),
                    }),
                    "device_id": device_id,
                }
                output_component_data = {
                    "component_type": "output",
                    "config_json": json.dumps({
                        "platform": component_dict.get("platform"),
                        "id": component_dict.get("output_id"),
                        "pin": component_dict.get("pin"),
                        "frequency": f'{component_dict.get("frequency")} Hz',
                    }),
                    "device_id": device_id,
                }
                number_component_data = {
                    "component_type": "number",
                    "config_json": json.dumps({
                        "platform": "template",
                        "name": component_dict.get("name"),
                        "min_value": component_dict.get("min_value", type=int),
                        "initial_value": component_dict.get("initial_value", type=int),
                        "max_value": component_dict.get("max_value", type=int),
                        "step": component_dict.get("step", type=int),
                        "optimistic": True,
                        "set_action": {
                            "then": [
                                {
                                    "servo.write": {
                                        "id": component_dict.get("servo_id"),
                                        "level": f"!lambda return x / {float(component_dict.get('max_value'))};"
                                    },
                                },
                            ]
                        },
                    }),
                    "device_id": device_id,
                }
                self.component_repository.create_all([
                    servo_component_data,
                    output_component_data,
                    number_component_data,
                ])
            case "switch":
                switch_component_data = {
                    "component_type": component_type,
                    "config_json": json.dumps({
                        "platform": component_dict.get("platform"),
                        "name": component_dict.get("name"),
                        "pin": {
                            "number": component_dict.get("pin"),
                            "inverted": True if component_dict.get("inverted") == "y" else False,
                        }
                    }),
                    "device_id": device_id,
                }
                self.component_repository.create(switch_component_data)
            case "sensor":
                sensor_component_data = {
                    "component_type": component_type,
                    "config_json": json.dumps({
                        "platform": component_dict.get("platform"),
                        "pin": component_dict.get("pin"),
                        "model": component_dict.get("model"),
                        "temperature": {
                            "name": component_dict.get("temperature_name")
                        },
                        "humidity": {
                            "name": component_dict.get("humidity_name")
                        },
                        "update_interval": f'{component_dict.get("update_interval")}s',
                    }),
                    "device_id": device_id,
                }
                self.component_repository.create(sensor_component_data)
            case "binary_sensor":
                binary_sensor_component_data = {
                    "component_type": component_type,
                    "config_json": json.dumps({
                        "platform": component_dict.get("platform"),
                        "name": component_dict.get("name"),
                        "pin": {
                            "number": component_dict.get("pin"),
                            "inverted": True if component_dict.get("inverted") == "y" else False,
                        },
                        **({"device_class": component_dict.get("device_class")} if component_dict.get("device_class") else {}),
                    }),
                    "device_id": device_id,
                }
                self.component_repository.create(binary_sensor_component_data)
        print("atualizando arquivo de configuração...")
        self.device_service.update_device_config(
            config_file=device.config_file, device_instance=device
        )
        return redirect(url_for("edit_device", device_id=device_id))
    

    def delete_component(self, device_id, component_id):
        component = self.component_repository.delete(component_id)
        if component:
            device = self.device_repository.get(device_id)
            print("atualizando arquivo de configuração...")
            self.device_service.update_device_config(
                config_file=device.config_file, device_instance=device
            )
        return redirect(url_for("edit_device", device_id=device_id))
    

    def update_component(self, device_id, component_id, request: Request):
        component = self.component_repository.get(component_id)
        if component:
            form_data = request.form
            component_type = form_data.get("componentType")
            match component_type:
                case "sensor":
                    data = {
                        "config_json": json.dumps({
                            "platform": form_data.get("platform"),
                            "pin": form_data.get("pin"),
                            "model": form_data.get("model"),
                            "temperature": {
                                "name": form_data.get("temperature_name")
                            },
                            "humidity": {
                                "name": form_data.get("humidity_name")
                            },
                            "update_interval": f'{form_data.get("update_interval")}s',
                        })
                    }
                    self.component_repository.update(component_id, data)
                case "switch":
                    data = {
                        "config_json": json.dumps({
                            "platform": form_data.get("platform"),
                            "name": form_data.get("name"),
                            "pin": {
                                "number": form_data.get("pin"),
                                "inverted": True if form_data.get("inverted") == "y" else False,
                            }
                        })
                    }
                    self.component_repository.update(component_id, data)
                case "binary_sensor":
                    data = {
                        "config_json": json.dumps({
                            "platform": form_data.get("platform"),
                            "name": form_data.get("name"),
                            "pin": {
                                "number": form_data.get("pin"),
                                "inverted": True if form_data.get("inverted") == "y" else False,
                            },
                            **({"device_class": form_data.get("device_class")} if form_data.get("device_class") else {}),
                        })
                    }
                    self.component_repository.update(component_id, data)
            device = self.device_repository.get(device_id)
            print("atualizando arquivo de configuração...")
            self.device_service.update_device_config(
                config_file=device.config_file, device_instance=device
            )
        return redirect(url_for("edit_device", device_id=device_id))
