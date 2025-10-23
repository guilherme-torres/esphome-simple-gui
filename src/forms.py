from flask_wtf import FlaskForm
from wtforms import SelectField, StringField, IntegerField, ValidationError
from wtforms.validators import DataRequired, NumberRange
from wtforms import BooleanField


ESP8266_NODEMCU_PINOUT = [
    ("GPIO0", "GPIO0"), ("GPIO1", "GPIO1"), ("GPIO2", "GPIO2"), ("GPIO3", "GPIO3"),
    ("GPIO4", "GPIO4"), ("GPIO5", "GPIO5"), ("GPIO6", "GPIO6"), ("GPIO7", "GPIO7"),
    ("GPIO8", "GPIO8"), ("GPIO9", "GPIO9"), ("GPIO10", "GPIO10"), ("GPIO11", "GPIO11"),
    ("GPIO12", "GPIO12"), ("GPIO13", "GPIO13"), ("GPIO14", "GPIO14"), ("GPIO15", "GPIO15"),
    ("GPIO16", "GPIO16"), ("GPIO17", "GPIO17"),
]

class SwitchGPIOForm(FlaskForm):
    platform = SelectField(
        "Plataforma",
        validators=[DataRequired()],
        choices=[("gpio", "GPIO")],
        default="gpio",
        id="component_platform",
    )
    name = StringField("Nome", validators=[DataRequired()])
    pin = SelectField(
        "Pino",
        validators=[DataRequired()],
        choices=ESP8266_NODEMCU_PINOUT,
        default="GPIO5",
    )
    inverted = BooleanField("Invertido", default=False)


class SensorDhtForm(FlaskForm):
    platform = SelectField(
        "Plataforma",
        validators=[DataRequired()],
        choices=[("dht", "dht")],
        default="dht",
        id="component_platform",
    )
    pin = SelectField(
        "Pino",
        validators=[DataRequired()],
        choices=ESP8266_NODEMCU_PINOUT,
        default="GPIO4",
    )
    temperature_name = StringField("Nome temperatura", validators=[DataRequired()])
    humidity_name = StringField("Nome humidade", validators=[DataRequired()])
    update_interval = IntegerField("Intervalo de atualização (em segundos)", validators=[DataRequired()], default=60)

    def validade_update_interval(form, field):
        if field < 1:
            raise ValidationError("Este campo não pode ser menor que 1")


class ServoForm(FlaskForm):
    name = StringField("Nome", validators=[DataRequired()])
    servo_id = StringField("ID", validators=[DataRequired()])
    platform = SelectField(
        "Plataforma",
        validators=[DataRequired()],
        choices=[("esp8266_pwm", "esp8266_pwm")],
        default="esp8266_pwm",
        id="component_platform",
    )
    output_id = StringField("Output ID", validators=[DataRequired()])
    pin = SelectField(
        "Pino",
        validators=[DataRequired()],
        choices=ESP8266_NODEMCU_PINOUT,
        default="GPIO4",
    )
    frequency = IntegerField("Frequência (Hz)", validators=[DataRequired()], default=50)
    min_value = IntegerField("Ângulo mínimo", validators=[DataRequired()], default=-180)
    max_value = IntegerField("Ângulo máximo", validators=[DataRequired()], default=180)
    initial_value = IntegerField("Ângulo inicial", validators=[DataRequired()], default=180)
    step = IntegerField("Passo", validators=[DataRequired()], default=1)


class BinarySensorGPIOForm(FlaskForm):
    platform = SelectField(
        "Plataforma",
        validators=[DataRequired()],
        choices=[("gpio", "GPIO")],
        default="gpio",
        id="component_platform",
    )
    name = StringField("Nome", validators=[DataRequired()])
    pin = SelectField(
        "Pino",
        validators=[DataRequired()],
        choices=ESP8266_NODEMCU_PINOUT,
        default="GPIO14",
    )
    device_class = SelectField(
        "Classe do dispositivo (opcional)",
        choices=[
            ("", "Nenhuma"),
            ("motion", "Movimento"),
            ("door", "Porta"),
            ("window", "Janela"),
            ("moisture", "Umidade"),
            ("occupancy", "Ocupação"),
            ("opening", "Abertura"),
            ("presence", "Presença"),
            ("safety", "Segurança"),
            ("vibration", "Vibração"),
            ("sound", "Som"),
            ("problem", "Problema"),
            ("connectivity", "Conectividade"),
        ],
        default="",
    )
    inverted = BooleanField("Invertido", default=False)
    # filters_delayed_on = IntegerField(
    #     "Atraso para ligar (ms)", default=0, validators=[NumberRange(min=0)]
    # )
    # filters_delayed_off = IntegerField(
    #     "Atraso para desligar (ms)", default=0, validators=[NumberRange(min=0)]
    # )