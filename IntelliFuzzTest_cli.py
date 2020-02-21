import argparse
import urlparse

import uncurl_lib
import requests
from pyjfuzz.lib import PJFConfiguration
from pyjfuzz.lib import PJFFactory
from argparse import Namespace
import json

from misc.parse_url import fuzz_url_path
from misc.utils import random_header


def arg_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("file", nargs='+',
                        help="input file")

    args = parser.parse_args()

    return args


def get_url_from_file(f):
    with open(f, 'r') as f:
        result = f.readlines(1)[0]
        return result


def get_mutated_json(json_string):
    config = PJFConfiguration(Namespace(
        json=json.loads(json_string),
        level=6,
        strong_fuzz=True,
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
    args = arg_parser()
    # args.file is a list of filenames, we need the first element!
    url = get_url_from_file(args.file[0])
    context = uncurl_lib.parse_context(url)

    uncurl_url = context.url

    uncurl_method = context.method
    uncurl_data = context.data
    uncurl_header = context.headers

    new_header = random_header(uncurl_header)

    for i in range(100):
        try:
            # get or delete, fuzz url
            if uncurl_method == "get" or uncurl_method == "delete":
                new_url = fuzz_url_path(uncurl_url)

                res_code = make_request(method=uncurl_method,
                                        url=new_url,
                                        header=new_header,
                                        data=uncurl_data,
                                        )
                print "status code:" + str(res_code) + "\tnew_url:" + \
                      "\t" + new_url + "\theader:\t " + \
                      new_header

            # post or put, fuzz post body
            elif uncurl_method == "put" or uncurl_method == "post":
                fuzzed_json = get_mutated_json(str(uncurl_data))

                res_code = make_request(method=uncurl_method,
                                        url=uncurl_url,
                                        header=new_header,
                                        data=fuzzed_json,
                                        )
                print "status code:" + str(res_code) + "\tpayload:" + \
                      "\t" + fuzzed_json

            else:
                print "This should never happen!!"
        except:
            pass
