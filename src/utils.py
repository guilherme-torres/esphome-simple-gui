from secrets import choice
import serial.tools.list_ports
import yaml


def generate_password(length = 12):
    alpha_num = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
    return "".join([choice(alpha_num) for _ in range(length)])

def dict_to_yaml(obj):
    return yaml.dump(obj, sort_keys=False)

def list_serial_ports():
    return [port.device for port in serial.tools.list_ports.comports()]
