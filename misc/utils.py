import random
import string


def id_generator(size=15, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


def random_header(order_dict):
    action = random.choice([1, 2, 3])

    # random remove one header
    if action == 1:
        order_dict.pop(random.choice(order_dict.keys()))
        d = order_dict

    # random add one
    elif action == 2:
        d = dict(order_dict)
        d[id_generator(20)] = id_generator(20)

    # do nothing
    elif action == 3:
        d = order_dict

    return d
