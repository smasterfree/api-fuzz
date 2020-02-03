from pyjfuzz.lib import PJFConfiguration
from pyjfuzz.lib import PJFFactory
from argparse import Namespace
import json
import argparse


# data = '{"NetworkTypes":["private","idc"],"VpcId":"233a5ef1-25c0-417c-8984-f684c99b9b9f","FlavorId":80,"ClusterName":"1ddb-ab-smoke-quick-check-czq","ClusterSizes":[1,2],"DDBVersion":"5.0","VpcSecurityGroups":["6e9796ee-c87e-46ec-a0fb-da511b214d87"],"SubnetIds":["663a1aa0-7f97-41fd-a613-6cdb08bbb340","2a490371-5f38-49e0-8ed7-cc8fbaf37173"],"TopAvailableZones":["cn-east-1b","cn-east-1a"]}'


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
