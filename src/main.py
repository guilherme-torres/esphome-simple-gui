from string import Template
from utils import generate_password

data = {
    "device_name": "quarto",
    "platform": "ESP8266",
    "board": "nodemcuv2",
    "wifi": {"ssid": "teste", "password": "teste123"},
    "ota": {"password": "1234"},
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

with open(f"{data["device_name"]}.yaml", 'w') as yaml_file:
    yaml_file.write(basic_config_yaml_str.strip() + "\n")
