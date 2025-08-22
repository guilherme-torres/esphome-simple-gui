import os
import subprocess
from string import Template
from src.utils import generate_password
import yaml
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
    ssid: "$ap_name Fallback Hotspot"
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

# def dict_to_yaml(obj):
#     return yaml.dump(obj, sort_keys=False)

# with open(file_dir, "a") as yaml_file:
#     yaml_file.write("\n" + dict_to_yaml(component))

alembic = Alembic()

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"

db.init_app(app)
alembic.init_app(app)

@app.route("/", methods=["GET", "POST"])
def create_device():
    if request.method == "POST":
        print(request.form)
        if not os.path.exists(dirname):
            os.mkdir(dirname)

        file_dir = os.path.join(dirname, f"{request.form.get("deviceName")}.yaml")

        device_exist = db.session.execute(db.select(Device).filter_by(config_file=file_dir)).scalar_one_or_none()

        if device_exist:
            print("O dispositivo já existe!", device_exist)
            return render_template("index.html")

        basic_config_yaml_str = Template(basic_config_template).substitute(
            name=request.form.get("deviceName"), platform=request.form.get("platform").lower(), board=request.form.get("board"), wifi_ssid=request.form.get("wifiSsid"),
            wifi_password=request.form.get("wifiPassword"), ota_password=request.form.get("otaPassword"),
            ap_name=request.form.get("deviceName").title(), ap_password=generate_password()
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
        )

        db.session.add(device)
        db.session.commit()
        
        return redirect(url_for("list_devices"))
    return render_template("index.html")

@app.route("/devices")
def list_devices():
    devices = db.session.execute(db.select(Device)).scalars().all()
    print(devices)
    return render_template("devices.html", devices=devices)

# process = subprocess.Popen(
#     ["esphome", "run", file_dir, "--device", "/dev/ttyUSB0"],
#     stdout=subprocess.PIPE,
#     stderr=subprocess.STDOUT,
#     text=True
# )

# for line in process.stdout:
#     print(line, end="")