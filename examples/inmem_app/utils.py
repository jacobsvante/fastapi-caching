import random
import string

ASCII_ALPHA_NUM = string.ascii_lowercase + string.ascii_uppercase + string.digits + " "


def random_ascii(n: int):
    return "".join(random.choice(ASCII_ALPHA_NUM) for _ in range(n))
