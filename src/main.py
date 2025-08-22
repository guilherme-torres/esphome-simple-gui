import os
import subprocess
from string import Template
from utils import generate_password
import yaml
from flask import Flask, render_template

# configuração básica

data = {
    "device_name": "quarto",
    "platform": "ESP8266",
    "board": "nodemcuv2",
    "wifi": {"ssid": "brisa-Marka", "password": "gugu100317"},
    "ota": {"password": ""},
}

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

basic_config_yaml_str = Template(basic_config_template).substitute(
    name=data["device_name"], platform=data["platform"].lower(), board=data["board"], wifi_ssid=data["wifi"]["ssid"],
    wifi_password=data["wifi"]["password"], ota_password=data["ota"]["password"],
    ap_name=data["device_name"].title(), ap_password=generate_password()
)

dirname = "esphome_files"

if not os.path.exists(dirname):
    os.mkdir(dirname)

file_dir = os.path.join(dirname, f"{data["device_name"]}.yaml")

with open(file_dir, 'w') as yaml_file:
    yaml_file.write(basic_config_yaml_str.strip() + "\n")


# adicionar componente a configuração

component = {
    "switch": [
        {
            "platform": "gpio",
            "name": "lampada",
            "pin": "GPIO5"
        }
    ]
}

def dict_to_yaml(obj):
    return yaml.dump(obj, sort_keys=False)

with open(file_dir, "a") as yaml_file:
    yaml_file.write("\n" + dict_to_yaml(component))


app = Flask(__name__)

@app.route("/")
def main():
    return render_template("index.html")

# process = subprocess.Popen(
#     ["esphome", "run", file_dir, "--device", "/dev/ttyUSB0"],
#     stdout=subprocess.PIPE,
#     stderr=subprocess.STDOUT,
#     text=True
# )

# for line in process.stdout:
#     print(line, end="")