from pyjfuzz.lib import PJFConfiguration
from pyjfuzz.lib import PJFFactory
from argparse import Namespace
import json
import argparse


def set_argu_parser():
    parser = argparse.ArgumentParser()

    parser.add_argument('data', help='a valid string json data ')
    parser.add_argument("-n", "--number", required=True,
                        help="return how many mutated jsons")

    arguments = parser.parse_args()
    return arguments


args = set_argu_parser()


def print_mutated_json(number):
    config = PJFConfiguration(Namespace(
        json=json.loads(args.data),
        level=6,
        strong_fuzz=True,
        nologo=True,
        debug=False,
        recheck_ports=False
    ))
    # init the object factory used to fuzz (see documentation)
    factory = PJFFactory(config)

    sum = []
    for i in range(1, number):
        sum.append(factory.fuzzed)

    print sum


if __name__ == '__main__':
    print_mutated_json(int(args.number))
