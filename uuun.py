import uncurl_lib
import requests
from pyjfuzz.lib import PJFConfiguration
from pyjfuzz.lib import PJFFactory
from argparse import Namespace
import json
import argparse


def get_mutated_json(json_string):
    config = PJFConfiguration(Namespace(
        json=json.loads(json_string),
        level=6,
        strong_fuzz=False,
        nologo=True,
        debug=False,
        recheck_ports=False
    ))
    # init the object factory used to fuzz (see documentation)
    factory = PJFFactory(config)

    mutated_json = factory.fuzzed
    return mutated_json


def make_request(method, url, header, data):
    req = requests.request(method, url, data=data, headers=header)
    return req.status_code


if __name__ == '__main__':
    context = uncurl_lib.parse_context(
        '''curl  'http://10.182.2.253:8774/v2/9ac08939bf67465c88cd638107e0a6d6/os-tag-types/11/extra-specs' -X POST -H "X-Auth-Project-Id: admin" -H "Content-Type: application/json" -H "Accept: application/json" -H "X-Auth-Token: d8499072f58f4e01815812974e81ce9d" -d '{"extra_specs": {"host_required": "no", "unique_on_host": "dsadsa"}}' ''')

    uncurl_url = context.url
    uncurl_method = context.method
    uncurl_data = context.data
    uncurl_header = context.headers

    print uncurl_url
    print uncurl_method
    print uncurl_data
    print uncurl_header

    print get_mutated_json(str(uncurl_data))

    print make_request(method=uncurl_method,
                       url=uncurl_url,
                       data=uncurl_data,
                       header=uncurl_header)
