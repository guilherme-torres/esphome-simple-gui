import os
import json
import subprocess
from string import Template
from src.utils import generate_password, list_serial_ports, dict_to_yaml
from flask import Flask, redirect, render_template, request, url_for
from flask_alembic import Alembic
from src.database.db import db
from src.models import Device, Component
from src.forms import SwitchGPIOForm


basic_config_template = """
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

dirname = "esphome_files"

alembic = Alembic()

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config['SECRET_KEY'] = "super-secret-key"

db.init_app(app)
alembic.init_app(app)

def update_device_yaml_file(file_path: str, device_instance: Device):
    basic_config_yaml_str = Template(basic_config_template).substitute(
        name=device_instance.name, platform=device_instance.platform, board=device_instance.board, wifi_ssid=device_instance.wifi_ssid,
        wifi_password=device_instance.wifi_password, ota_password="" if device_instance.ota_password is None else device_instance.ota_password,
        ap_ssid=device_instance.ap_ssid, ap_password=device_instance.ap_password
    )

    if os.path.exists(file_path):
        os.remove(file_path)

    with open(device_instance.config_file, 'w') as yaml_file:
        yaml_file.write(basic_config_yaml_str.strip() + "\n")

    components = device_instance.components
    print("componentes:", components)
    if len(components) > 0:
        switches = db.session.execute(db.select(Component).filter_by(
            component_type="switch", device_id=device_instance.id)).scalars().all()
        switch_dict = {
            "switch": []
        }
        for switch_component in switches:
            config_json = json.loads(switch_component.config_json)
            switch_dict["switch"].append({
                "platform": switch_component.platform,
                "name": switch_component.name,
                **config_json,
            })
        with open(device_instance.config_file, "a") as yaml_file:
            yaml_file.write("\n" + dict_to_yaml(switch_dict))

@app.route("/create-device", methods=["POST"])
def create_device():
    print(request.form)
    if not os.path.exists(dirname):
        os.mkdir(dirname)

    file_dir = os.path.join(dirname, f"{request.form.get("deviceName")}.yaml")

    device_exist = db.session.execute(db.select(Device).filter_by(config_file=file_dir)).scalar_one_or_none()

    if device_exist:
        print("O dispositivo já existe!", device_exist)
        return redirect(url_for("list_devices"))
    
    ap_ssid = f'{request.form.get("deviceName").title()} Fallback Hotspot'
    ap_password = generate_password()

    device = Device(
        name=request.form.get("deviceName"),
        platform=request.form.get("platform"),
        board=request.form.get("board"),
        wifi_ssid=request.form.get("wifiSsid"),
        wifi_password=request.form.get("wifiPassword"),
        ota_password=request.form.get("otaPassword"),
        config_file=file_dir,
        ap_ssid=ap_ssid,
        ap_password=ap_password,
    )

    db.session.add(device)
    db.session.commit()

    update_device_yaml_file(file_path=device.config_file, device_instance=device)
    
    return redirect(url_for("list_devices"))

@app.route("/")
def list_devices():
    devices = db.session.execute(db.select(Device)).scalars().all()
    print(devices)
    return render_template("index.html", devices=devices)

@app.route("/delete-device/<int:device_id>", methods=["POST"])
def delete_device(device_id):
    device = db.session.get(Device, device_id)
    if device:
        config_file_path = device.config_file
        print("deletendo dispositivo do bd", device)
        db.session.delete(device)
        db.session.commit()
        print("deletando arquivo de configuração do dispositivo")
        if os.path.exists(config_file_path):
            os.remove(config_file_path)
    return redirect(url_for("list_devices"))

@app.route("/edit-device/<int:device_id>", methods=["GET", "POST"])
def edit_device(device_id):
    device = db.session.get(Device, device_id)
    form = SwitchGPIOForm()
    form.pin.data = "GPIO5"

    if device is None:
        print("dispositivo não encontrado")
        return redirect(url_for("list_devices"))

    if request.method == "POST":
        print("dados do formulário:", request.form)
        old_config_file = device.config_file
        file_dir = os.path.join(dirname, f"{request.form.get("deviceName")}.yaml")

        device_exist = db.session.execute(db.select(Device).filter_by(config_file=file_dir)).scalar_one_or_none()

        if device_exist:
            if device_exist.id != device_id:
                print("Um dispositivo com esse nome já existe!", device_exist)
                return redirect(url_for("edit_device", device_id=device_id))

        ap_ssid = f'{request.form.get("deviceName").title()} Fallback Hotspot'

        device.name = request.form.get("deviceName")
        device.platform = request.form.get("platform")
        device.board = request.form.get("board")
        device.wifi_ssid = request.form.get("wifiSsid")
        device.wifi_password = request.form.get("wifiPassword")
        device.ota_password = request.form.get("otaPassword")
        device.config_file = file_dir
        device.ap_ssid = ap_ssid

        db.session.commit()
        print("dispositivo atualizado com sucesso no bd")
        print("atualizando arquivo de configuração do dispositivo...")
        update_device_yaml_file(file_path=old_config_file, device_instance=device)
        
        return redirect(url_for("list_devices"))
    return render_template("edit-device.html", device=device, form=form)

@app.route("/upload-config/<int:device_id>", methods=["POST"])
def upload_config(device_id):
    device = db.session.get(Device, device_id)
    if device:
        print("fazendo upload para o dispositivo", device.config_file)
        serial_port = request.form.get("serial_port")
        if serial_port:
            print("porta", serial_port)
            process = subprocess.Popen(
                ["esphome", "run", device.config_file, "--device", serial_port],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )
            for line in process.stdout:
                print(line, end="")
            return redirect(url_for("list_devices"))
        print("porta serial não selecionada")
        return redirect(url_for("list_devices"))
    print("dispositivo não encontrado")
    return redirect(url_for("list_devices"))

@app.route("/available-ports")
def list_available_ports():
    return list_serial_ports()

@app.route("/add-component/<int:device_id>", methods=["POST"])
def add_component(device_id):
    device = db.session.get(Device, device_id)
    if device is None:
        print("dispositivo não encontrado")
        return redirect(url_for("list_devices"))
    print(f"adicionar componente no dispositivo #{device_id}")
    component_dict = request.form.to_dict()
    print(component_dict)
    name = component_dict.pop("componentName")
    component_type = component_dict.pop("componentType")
    platform = component_dict.pop("componentPlatform")
    config_json = json.dumps(component_dict)
    component = Component(
        component_type=component_type,
        platform=platform,
        name=name,
        config_json=config_json,
        device_id=device_id,
    )
    db.session.add(component)
    db.session.commit()
    update_device_yaml_file(file_path=device.config_file, device_instance=device)
    return redirect(url_for("edit_device", device_id=device_id))

@app.route("/delete-component/<int:device_id>/<int:component_id>", methods=["POST"])
def delete_component(device_id, component_id):
    component = db.session.get(Component, component_id)
    if component:
        print("deletando componente", component)
        device = component.device
        db.session.delete(component)
        db.session.commit()
        update_device_yaml_file(file_path=device.config_file, device_instance=device)
    return redirect(url_for("edit_device", device_id=device_id))
