import os
import json
import subprocess
import threading
from string import Template
from flask import Flask, redirect, render_template, request, url_for, jsonify, render_template_string
from flask_alembic import Alembic
from flask_socketio import SocketIO
from src.database.db import db
from src.models import Device, Component
from src.forms import SwitchGPIOForm, SensorDhtForm, ServoForm
from src.utils import generate_password, list_serial_ports, dict_to_yaml


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
app.config["SECRET_KEY"] = "super-secret-key"

db.init_app(app)
alembic.init_app(app)

socketio = SocketIO(app)


def update_device_yaml_file(file_path: str, device_instance: Device):
    basic_config_yaml_str = Template(basic_config_template).substitute(
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

    if os.path.exists(file_path):
        os.remove(file_path)

    with open(device_instance.config_file, "w") as yaml_file:
        yaml_file.write(basic_config_yaml_str.strip() + "\n")

    components = device_instance.components
    print("componentes:", components)
    if len(components) > 0:
        # switch
        switches = (
            db.session.execute(
                db.select(Component).filter_by(
                    component_type="switch", device_id=device_instance.id
                )
            )
            .scalars()
            .all()
        )
        if len(switches) > 0:
            switch_dict = {"switch": []}
            for switch_component in switches:
                config_json = json.loads(switch_component.config_json)
                switch_dict["switch"].append(config_json)
            with open(device_instance.config_file, "a") as yaml_file:
                yaml_file.write("\n" + dict_to_yaml(switch_dict))

        # sensor
        sensors = (
            db.session.execute(
                db.select(Component).filter_by(
                    component_type="sensor", device_id=device_instance.id
                )
            )
            .scalars()
            .all()
        )
        if len(sensors) > 0:
            sensor_dict = {"sensor": []}
            for sensor_component in sensors:
                config_json = json.loads(sensor_component.config_json)
                sensor_dict["sensor"].append(config_json)
            with open(device_instance.config_file, "a") as yaml_file:
                yaml_file.write("\n" + dict_to_yaml(sensor_dict))

        # number
        numbers = (
            db.session.execute(
                db.select(Component).filter_by(
                    component_type="number", device_id=device_instance.id
                )
            )
            .scalars()
            .all()
        )
        if len(numbers) > 0:
            number_dict = {"number": []}
            for number_component in numbers:
                config_json = json.loads(number_component.config_json)
                number_dict["number"].append(config_json)
            with open(device_instance.config_file, "a") as yaml_file:
                yaml_file.write("\n" + dict_to_yaml(number_dict))

        # servo
        servos = (
            db.session.execute(
                db.select(Component).filter_by(
                    component_type="servo", device_id=device_instance.id
                )
            )
            .scalars()
            .all()
        )
        if len(servos) > 0:
            servo_dict = {"servo": []}
            for sensor_component in servos:
                config_json = json.loads(sensor_component.config_json)
                servo_dict["servo"].append(config_json)
            with open(device_instance.config_file, "a") as yaml_file:
                yaml_file.write("\n" + dict_to_yaml(servo_dict))

        # output
        outputs = (
            db.session.execute(
                db.select(Component).filter_by(
                    component_type="output", device_id=device_instance.id
                )
            )
            .scalars()
            .all()
        )
        if len(outputs) > 0:
            output_dict = {"output": []}
            for output_component in outputs:
                config_json = json.loads(output_component.config_json)
                output_dict["output"].append(config_json)
            with open(device_instance.config_file, "a") as yaml_file:
                yaml_file.write("\n" + dict_to_yaml(output_dict))


@app.route("/create-device", methods=["POST"])
def create_device():
    print(request.form)
    if not os.path.exists(dirname):
        os.mkdir(dirname)

    file_dir = os.path.join(dirname, f"{request.form.get("deviceName")}.yaml")

    device_exist = db.session.execute(
        db.select(Device).filter_by(config_file=file_dir)
    ).scalar_one_or_none()

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

    if device is None:
        print("dispositivo não encontrado")
        return redirect(url_for("list_devices"))

    if request.method == "POST":
        print("dados do formulário:", request.form)
        old_config_file = device.config_file
        file_dir = os.path.join(dirname, f"{request.form.get("deviceName")}.yaml")

        device_exist = db.session.execute(
            db.select(Device).filter_by(config_file=file_dir)
        ).scalar_one_or_none()

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


@socketio.on("start_upload")
def handle_upload(data):
    device_id = data["device_id"]
    serial_port = data["serial_port"]

    device = db.session.get(Device, device_id)
    if not device:
        socketio.emit("log", {"line": "[Erro] Dispositivo não encontrado."})
        return
    
    def run_command():
        command = ["esphome", "run", device.config_file, "--device", serial_port]
        # command = ["ping", "-c", "5", "google.com"]
        process = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
        )
        for line in iter(process.stdout.readline, ""):
            socketio.emit("log", {"line": line, "device_id": device_id})
        process.stdout.close()
        process.wait()
    
    threading.Thread(target=run_command).start()


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
    component_dict = request.form
    print(component_dict)
    component_type = component_dict.get("componentType")
    # config_json = json.dumps(component_dict)
    match component_type:
        case "servo":
            servo_component = Component(
                component_type=component_type,
                config_json=json.dumps({
                    "id": component_dict.get("servo_id"),
                    "output": component_dict.get("output_id"),
                }),
                device_id=device_id,
            )
            output_component = Component(
                component_type="output",
                config_json=json.dumps({
                    "platform": component_dict.get("platform"),
                    "id": component_dict.get("output_id"),
                    "pin": component_dict.get("pin"),
                    "frequency": f'{component_dict.get("frequency")} Hz',
                }),
                device_id=device_id,
            )
            number_component = Component(
                component_type="number",
                config_json=json.dumps({
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
                device_id=device_id,
            )
            db.session.add(servo_component)
            db.session.add(output_component)
            db.session.add(number_component)
            db.session.commit()
        case "switch":
            component = Component(
                component_type=component_type,
                config_json=json.dumps({
                    "platform": component_dict.get("platform"),
                    "name": component_dict.get("name"),
                    "pin": component_dict.get("pin"),
                }),
                device_id=device_id,
            )
            db.session.add(component)
            db.session.commit()
        case "sensor":
            component = Component(
                component_type=component_type,
                config_json=json.dumps({
                    "platform": component_dict.get("platform"),
                    "pin": component_dict.get("pin"),
                    "temperature": {
                        "name": component_dict.get("temperature_name")
                    },
                    "humidity": {
                        "name": component_dict.get("humidity_name")
                    },
                    "update_interval": f'{component_dict.get("update_interval")}s',
                }),
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


forms = {
    "switch": {
        "form_class": SwitchGPIOForm,
        "template": """
        <div class="mb-3">
            {{ form.platform.label(class="form-label") }} {{ form.platform(class="form-select") }}
        </div>
        <div class="mb-3">
            {{ form.name.label(class="form-label") }} {{ form.name(class="form-control") }}
        </div>
        <div class="mb-3">
            {{ form.pin.label(class="form-label") }} {{ form.pin(class="form-select") }}
        </div>
        """,
    },
    "sensor": {
        "form_class": SensorDhtForm,
        "template": """
        <div class="mb-3">
            {{ form.platform.label(class="form-label") }} {{ form.platform(class="form-select") }}
        </div>
        <div class="mb-3">
            {{ form.pin.label(class="form-label") }} {{ form.pin(class="form-select") }}
        </div>
        <div class="mb-3">
            {{ form.temperature_name.label(class="form-label") }} {{ form.temperature_name(class="form-control") }}
        </div>
        <div class="mb-3">
            {{ form.humidity_name.label(class="form-label") }} {{ form.humidity_name(class="form-control") }}
        </div>
        <div class="mb-3">
            {{ form.update_interval.label(class="form-label") }} {{ form.update_interval(class="form-control", type="number") }}
        </div>
        """,
    },
    "servo": {
        "form_class": ServoForm,
        "template": """
        <div class="mb-3">
            {{ form.name.label(class="form-label") }} {{ form.name(class="form-control") }}
        </div>
        <div class="mb-3">
            {{ form.servo_id.label(class="form-label") }} {{ form.servo_id(class="form-control") }}
        </div>
        <div class="mb-3">
            {{ form.platform.label(class="form-label") }} {{ form.platform(class="form-select") }}
        </div>
        <div class="mb-3">
            {{ form.output_id.label(class="form-label") }} {{ form.output_id(class="form-control") }}
        </div>
        <div class="mb-3">
            {{ form.pin.label(class="form-label") }} {{ form.pin(class="form-select") }}
        </div>
        <div class="mb-3">
            {{ form.frequency.label(class="form-label") }} {{ form.frequency(class="form-control", type="number") }}
        </div>
        <div class="mb-3">
            {{ form.min_value.label(class="form-label") }} {{ form.min_value(class="form-control", type="number") }}
        </div>
        <div class="mb-3">
            {{ form.max_value.label(class="form-label") }} {{ form.max_value(class="form-control", type="number") }}
        </div>
        <div class="mb-3">
            {{ form.initial_value.label(class="form-label") }} {{ form.initial_value(class="form-control", type="number") }}
        </div>
        <div class="mb-3">
            {{ form.step.label(class="form-label") }} {{ form.step(class="form-control", type="number") }}
        </div>
        """,
    },
}

@app.route("/select-component-form", methods=["POST"])
def select_component_form():
    component_type = request.form.get("component_type")
    component_form = forms.get(component_type)
    if not component_form:
        return jsonify({"html": "<div>Tipo inválido</div>"}), 400
    html = render_template_string(
        component_form.get("template"),
        form=component_form.get("form_class")(),
    )
    return jsonify({ "html": html })
