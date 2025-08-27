import os
import json
from string import Template
from flask import Request, redirect, render_template, url_for
from src.repositories.device import DeviceRepository
from src.repositories.component import ComponentRepository
from src.config import Config
from src.utils import generate_password, dict_to_yaml


class DeviceService:
    def __init__(
        self,
        device_repository: DeviceRepository,
        component_repository: ComponentRepository
    ):
        self.device_repository = device_repository
        self.component_repository = component_repository
        self.config = Config()
        self.device_config_template = """
esphome:
  name: $name

$platform:
  board: $board

# Enable logging
logger:

# Enable Home Assistant API
api:
  password: "$ota_password"

ota:
  - platform: esphome
    password: "$ota_password"

wifi:
  ssid: "$wifi_ssid"
  password: "$wifi_password"

  # Enable fallback hotspot (captive portal) in case wifi connection fails
  ap:
    ssid: "$ap_ssid"
    password: "$ap_password"

captive_portal:
"""

    def update_device_config(self, config_file, device_instance):
        device_config = Template(self.device_config_template).substitute(
            name=device_instance.name,
            platform=device_instance.platform,
            board=device_instance.board,
            wifi_ssid=device_instance.wifi_ssid,
            wifi_password=device_instance.wifi_password,
            ota_password=(
                "" if device_instance.ota_password is None else device_instance.ota_password
            ),
            ap_ssid=device_instance.ap_ssid,
            ap_password=device_instance.ap_password,
        )
        if os.path.exists(config_file):
            os.remove(config_file)
        with open(device_instance.config_file, "w") as yaml_file:
            yaml_file.write(device_config.strip() + "\n")
        components = device_instance.components
        print("componentes:", components)
        if len(components) > 0:
            # switch
            switches = self.component_repository.filter_by({
                "component_type": "switch",
                "device_id": device_instance.id,
            })
            if len(switches) > 0:
                switch_dict = {"switch": []}
                for switch_component in switches:
                    config_json = json.loads(switch_component.config_json)
                    switch_dict["switch"].append(config_json)
                with open(device_instance.config_file, "a") as yaml_file:
                    yaml_file.write("\n" + dict_to_yaml(switch_dict))
            # sensor
            sensors = self.component_repository.filter_by({
                "component_type": "sensor",
                "device_id": device_instance.id,
            })
            if len(sensors) > 0:
                sensor_dict = {"sensor": []}
                for sensor_component in sensors:
                    config_json = json.loads(sensor_component.config_json)
                    sensor_dict["sensor"].append(config_json)
                with open(device_instance.config_file, "a") as yaml_file:
                    yaml_file.write("\n" + dict_to_yaml(sensor_dict))
            # number
            numbers = self.component_repository.filter_by({
                "component_type": "number",
                "device_id": device_instance.id,
            })
            if len(numbers) > 0:
                number_dict = {"number": []}
                for number_component in numbers:
                    config_json = json.loads(number_component.config_json)
                    number_dict["number"].append(config_json)
                with open(device_instance.config_file, "a") as yaml_file:
                    yaml_file.write("\n" + dict_to_yaml(number_dict))
            # servo
            servos = self.component_repository.filter_by({
                "component_type": "servo",
                "device_id": device_instance.id,
            })
            if len(servos) > 0:
                servo_dict = {"servo": []}
                for sensor_component in servos:
                    config_json = json.loads(sensor_component.config_json)
                    servo_dict["servo"].append(config_json)
                with open(device_instance.config_file, "a") as yaml_file:
                    yaml_file.write("\n" + dict_to_yaml(servo_dict))
            # output
            outputs = self.component_repository.filter_by({
                "component_type": "output",
                "device_id": device_instance.id,
            })
            if len(outputs) > 0:
                output_dict = {"output": []}
                for output_component in outputs:
                    config_json = json.loads(output_component.config_json)
                    output_dict["output"].append(config_json)
                with open(device_instance.config_file, "a") as yaml_file:
                    yaml_file.write("\n" + dict_to_yaml(output_dict))


    def create_device(self, request: Request):
        if not os.path.exists(self.config.esphome_dir):
            os.mkdir(self.config.esphome_dir)
        config_file = os.path.join(self.config.esphome_dir, f"{request.form.get("deviceName")}.yaml")
        device_exist = self.device_repository.find_one({"config_file": config_file})
        if device_exist:
            print("O dispositivo já existe!", device_exist)
            return redirect(url_for("list_devices"))
        ap_ssid = f'{request.form.get("deviceName").title()} Fallback Hotspot'
        ap_password = generate_password()
        data = {
            "name": request.form.get("deviceName"),
            "platform": request.form.get("platform"),
            "board": request.form.get("board"),
            "wifi_ssid": request.form.get("wifiSsid"),
            "wifi_password": request.form.get("wifiPassword"),
            "ota_password": request.form.get("otaPassword"),
            "config_file": config_file,
            "ap_ssid": ap_ssid,
            "ap_password": ap_password,
        }
        device = self.device_repository.create(data)
        self.update_device_config(config_file=device.config_file, device_instance=device)
        return redirect(url_for("list_devices"))
    

    def list_devices(self):
        devices = self.device_repository.list_all()
        print(devices)
        return render_template("index.html", devices=devices)
    

    def delete_device(self, device_id):
        print("deletendo dispositivo do bd", device_id)
        device = self.device_repository.delete(device_id)
        if device:
            config_file = device.config_file
            print("deletando arquivo de configuração do dispositivo", config_file)
            if os.path.exists(config_file):
                os.remove(config_file)
        return redirect(url_for("list_devices"))
    

    def update_device(self, device_id, request: Request):
        device = self.device_repository.get(device_id)
        if device is None:
            print("dispositivo não encontrado")
            return redirect(url_for("list_devices"))
        if request.method == "POST":
            print("dados do formulário:", request.form)
            old_config_file = device.config_file
            new_config_file = os.path.join(self.config.esphome_dir, f"{request.form.get("deviceName")}.yaml")
            device_exist = self.device_repository.find_one({"config_file": new_config_file})
            if device_exist:
                if device_exist.id != device_id:
                    print("Um dispositivo com esse nome já existe!", device_exist)
                    return redirect(url_for("edit_device", device_id=device_id))
            ap_ssid = f'{request.form.get("deviceName").title()} Fallback Hotspot'
            data = {
                "name": request.form.get("deviceName"),
                "platform": request.form.get("platform"),
                "board": request.form.get("board"),
                "wifi_ssid": request.form.get("wifiSsid"),
                "wifi_password": request.form.get("wifiPassword"),
                "ota_password": request.form.get("otaPassword"),
                "config_file": new_config_file,
                "ap_ssid": ap_ssid,
            }
            print("atualizando dispositivo")
            device = self.device_repository.update(device_id, data)
            print("atualizando arquivo de configuração do dispositivo...")
            self.update_device_config(config_file=old_config_file, device_instance=device)
            return redirect(url_for("list_devices"))
        return render_template("edit-device.html", device=device)
