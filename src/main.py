import subprocess
import threading
from flask import Flask, request, jsonify, render_template_string
from flask_alembic import Alembic
from flask_socketio import SocketIO
from src.database.db import db
from src.forms import SwitchGPIOForm, SensorDhtForm, ServoForm
from src.utils import list_serial_ports
from src.repositories.device import DeviceRepository
from src.repositories.component import ComponentRepository
from src.services.device import DeviceService
from src.services.component import ComponentService


device_repository = DeviceRepository()
component_repository = ComponentRepository()

device_service = DeviceService(
    device_repository=device_repository,
    component_repository=component_repository,
)
component_service = ComponentService(
    component_repository=component_repository,
    device_repository=device_repository,
    device_service=device_service,
)

alembic = Alembic()

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SECRET_KEY"] = "super-secret-key"

db.init_app(app)
alembic.init_app(app)

socketio = SocketIO(app)

@app.route("/create-device", methods=["POST"])
def create_device():
    return device_service.create_device(request)

@app.route("/")
def list_devices():
    return device_service.list_devices()

@app.route("/delete-device/<int:device_id>", methods=["POST"])
def delete_device(device_id):
    return device_service.delete_device(device_id)

@app.route("/edit-device/<int:device_id>", methods=["GET", "POST"])
def edit_device(device_id):
    return device_service.update_device(device_id=device_id, request=request)

@app.route("/available-ports")
def list_available_ports():
    return list_serial_ports()

@socketio.on("start_upload")
def handle_upload(data):
    device_id = data["device_id"]
    serial_port = data["serial_port"]
    device = device_repository.get(device_id)
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

@app.route("/add-component/<int:device_id>", methods=["POST"])
def add_component(device_id):
    return component_service.create_component(device_id=device_id, request=request)

@app.route("/delete-component/<int:device_id>/<int:component_id>", methods=["POST"])
def delete_component(device_id, component_id):
    return component_service.delete_component(device_id=device_id, component_id=component_id)

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
