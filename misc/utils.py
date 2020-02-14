import random
import string

from IntelliFuzzTest_cli import uncurl_header


def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


def random_header(order_dict):
    action = random.choice([1, 2, 3])

    # random remove one header
    if action == 1:
        order_dict.pop(random.choice(uncurl_header.keys()))
        d = order_dict

    # random add one
    elif action == 2:
        d = dict(order_dict)
        d[id_generator(20)] = id_generator(20)

    # do nothing
    elif action == 3:
        d = order_dict

    return d