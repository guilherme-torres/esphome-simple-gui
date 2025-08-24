from flask_wtf import FlaskForm
from wtforms import SelectField
from wtforms.validators import DataRequired


class SwitchGPIOForm(FlaskForm):
    pin = SelectField(
        "Pino",
        validators=[DataRequired()],
        choices=[
            ("GPIO0", "GPIO0"), ("GPIO1", "GPIO1"), ("GPIO2", "GPIO2"), ("GPIO3", "GPIO3"),
            ("GPIO4", "GPIO4"), ("GPIO5", "GPIO5"), ("GPIO6", "GPIO6"), ("GPIO7", "GPIO7"),
            ("GPIO8", "GPIO8"), ("GPIO9", "GPIO9"), ("GPIO10", "GPIO10"), ("GPIO11", "GPIO11"),
            ("GPIO12", "GPIO12"), ("GPIO13", "GPIO13"), ("GPIO14", "GPIO14"), ("GPIO15", "GPIO15"),
            ("GPIO16", "GPIO16"), ("GPIO17", "GPIO17"),
        ]
    )