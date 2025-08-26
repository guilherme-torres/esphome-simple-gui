from secrets import choice
import serial.tools.list_ports
import yaml


def generate_password(length = 12):
    alpha_num = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
    return "".join([choice(alpha_num) for _ in range(length)])

class LambdaStr(str):
    pass

def lambda_representer(dumper, data):
    return dumper.represent_scalar('!lambda', data)

yaml.add_representer(LambdaStr, lambda_representer)

def convert_tags(obj):
    if isinstance(obj, dict):
        return {k: convert_tags(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_tags(i) for i in obj]
    elif isinstance(obj, str) and obj.startswith('!lambda '):
        return LambdaStr(obj[len('!lambda '):])
    return obj

def dict_to_yaml(obj):
    return yaml.dump(convert_tags(obj), sort_keys=False, allow_unicode=True)

def list_serial_ports():
    return [port.device for port in serial.tools.list_ports.comports()]
