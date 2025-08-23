import os
import subprocess
from string import Template
from src.utils import generate_password
from flask import Flask, redirect, render_template, request, url_for
from flask_alembic import Alembic
from src.database.db import db
from src.models import Device, Component


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

# adicionar componente a configuração

# component = {
#     "switch": [
#         {
#             "platform": "gpio",
#             "name": "lampada",
#             "pin": "GPIO5"
#         }
#     ]
# }

# with open(file_dir, "a") as yaml_file:
#     yaml_file.write("\n" + dict_to_yaml(component))

alembic = Alembic()

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"

db.init_app(app)
alembic.init_app(app)

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

    basic_config_yaml_str = Template(basic_config_template).substitute(
        name=request.form.get("deviceName"), platform=request.form.get("platform").lower(), board=request.form.get("board"), wifi_ssid=request.form.get("wifiSsid"),
        wifi_password=request.form.get("wifiPassword"), ota_password=request.form.get("otaPassword", ""),
        ap_ssid=ap_ssid, ap_password=ap_password
    )

    with open(file_dir, 'w') as yaml_file:
        yaml_file.write(basic_config_yaml_str.strip() + "\n")

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
    return redirect(url_for("list_devices"))

@app.route("/edit-device/<int:device_id>", methods=["GET", "POST"])
def edit_device(device_id):
    device = db.session.get(Device, device_id)

    if device is None:
        print("dispositivo não encontrado")
        return redirect(url_for("list_devices"))

    if request.method == "POST":
        print("dados do formulário:", request.form)
        file_dir = os.path.join(dirname, f"{request.form.get("deviceName")}.yaml")

        device_exist = db.session.execute(db.select(Device).filter_by(config_file=file_dir)).scalar_one_or_none()

        if device_exist:
            if device_exist.id != device_id:
                print("Um dispositivo com esse nome já existe!", device_exist)
                return redirect(url_for("edit_device", device_id=device_id))

        ap_ssid = f'{request.form.get("deviceName").title()} Fallback Hotspot'

        basic_config_yaml_str = Template(basic_config_template).substitute(
            name=request.form.get("deviceName"), platform=request.form.get("platform").lower(), board=request.form.get("board"), wifi_ssid=request.form.get("wifiSsid"),
            wifi_password=request.form.get("wifiPassword"), ota_password=request.form.get("otaPassword", ""),
            ap_ssid=ap_ssid, ap_password=device.ap_password
        )

        os.remove(device.config_file)

        with open(file_dir, 'w') as yaml_file:
            yaml_file.write(basic_config_yaml_str.strip() + "\n")

        device.name = request.form.get("deviceName")
        device.platform = request.form.get("platform")
        device.board = request.form.get("board")
        device.wifi_ssid = request.form.get("wifiSsid")
        device.wifi_password = request.form.get("wifiPassword")
        device.ota_password = request.form.get("otaPassword")
        device.config_file = file_dir
        device.ap_ssid = ap_ssid

        db.session.commit()
        print("dispositivo atualizado com sucesso")
        
        return redirect(url_for("list_devices"))
    return render_template("edit-device.html", device=device)

# process = subprocess.Popen(
#     ["esphome", "run", file_dir, "--device", "/dev/ttyUSB0"],
#     stdout=subprocess.PIPE,
#     stderr=subprocess.STDOUT,
#     text=True
# )

# for line in process.stdout:
#     print(line, end="")