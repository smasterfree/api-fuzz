from pyjfuzz.core.pjf_server import PJFServer
from pyjfuzz.lib import PJFConfiguration
from pyjfuzz.lib import PJFFactory
from argparse import Namespace
import urllib
import json

from pjfapi import check_template

data = '***{"NetworkTypes":["private","idc"],"VpcId":"233a5ef1-25c0-417c-8984-f684c99b9b9f","FlavorId":80,"ClusterName":"1ddb-ab-smoke-quick-check-czq","ClusterSizes":[1,2],"DDBVersion":"5.0","VpcSecurityGroups":["6e9796ee-c87e-46ec-a0fb-da511b214d87"],"SubnetIds":["663a1aa0-7f97-41fd-a613-6cdb08bbb340","2a490371-5f38-49e0-8ed7-cc8fbaf37173"],"TopAvailableZones":["cn-east-1b","cn-east-1a"]}***'

if __name__ == '__main__':
    org_payload, encoded = check_template(data)

    config = PJFConfiguration(Namespace(
        json=json.loads(urllib.unquote(org_payload)) if encoded else json.loads(
            org_payload),
        level=6,
        strong_fuzz=True,
        nologo=True,
        debug=False,
        url_encode=encoded,
        recheck_ports=False
    ))
    # init the object factory used to fuzz (see documentation)
    factory = PJFFactory(config)

    for i in range(1, 100):
        print factory.fuzzed
