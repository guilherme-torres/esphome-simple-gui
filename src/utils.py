from secrets import choice


def generate_password(length = 12):
    alpha_num = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
    return "".join([choice(alpha_num) for _ in range(length)])
