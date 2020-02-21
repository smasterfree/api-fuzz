"""

PyJFAPI - CLI json API fuzzer

PyJFAPI perform automatic analysis of JSON API using PyJFuzz fuzzing
framework (https://www.github.com/mseclab/PyJFuzz), the automatic analysis will extract
just the useful request which may lead to security flaws. If you found this tool useful
please leave a comment on GitHub!

MIT License

Copyright (c) 2017 Daniele Linguaglossa
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

"""

from BaseHTTPServer import BaseHTTPRequestHandler

try:
    from pyjfuzz.lib import PJFConfiguration
    from pyjfuzz.lib import PJFFactory
except ImportError:
    print "[!] Can't find PyJFuzz API library, please install with: 'git clone https://github.com/mseclab/PyJFuzz.git'"
    print "[!] One done install with: 'sudo python setup.py install'"
    exit(-1)
from argparse import Namespace
from StringIO import StringIO
from threading import Thread
from threading import Lock
import multiprocessing
import argparse
import httplib
import hashlib
import socket
import signal
import urllib
import Queue
import time
import json
import ssl
import sys
import os
import re

from my_logger import logger

print_queue = Queue.Queue(0)


def printer_thread():
    """
    Thread used to prevent race condition over console while printing, it uses a message Queue
    """
    #  infinite printer loop
    while True:
        try:
            #  if printer queue is not empty => we have something to print!
            while not print_queue.empty():
                #  get the element to print
                element = print_queue.get()
                sys.stdout.write("[INFO] {0}\n".format(element))
                #  task done! get the next
                print_queue.task_done()
            # prevent high CPU usage
            time.sleep(0.1)
        except KeyboardInterrupt:
            #  handle ctrl+c to prevent infinite process loop
            break


def init_printer():
    """
    Init the printer thread see above
    """
    pthread = Thread(target=printer_thread, args=())
    #  set daemon so process end when printer thread is killed
    pthread.setDaemon(True)
    pthread.start()


class HTTPRequestParser(BaseHTTPRequestHandler):
    def __init__(self, request_text):
        """
        Parse the request headers plus body
        """
        #  rfile contains the full http message
        self.rfile = StringIO(request_text)
        self.raw_requestline = self.rfile.readline()
        #  get errors during parsing
        self.error_code = self.error_message = None
        #  parse the message
        self.parse_request()
        tmp = {}
        #  restore original headers (CamelCase)
        for header in self.headers.headers:
            key, val = header[:-2].split(": ")
            tmp.update({key: val})
        self.headers = tmp
        #  Put connection to close in order to prevent socket bottleneck
        if "Connection" in self.headers:
            self.headers["Connection"] = "close"
        else:
            self.headers.update({"Connection": "close"})
        # delete the content-length header since it will be updated by httplib during requests
        if "Content-Length" in self.headers:
            del self.headers["Content-Length"]
        # wfile will contains just the message body (POST)
        self.wfile = StringIO(request_text.split("\r\n\r\n", 1)[1])
        self._body = self.wfile.read()

    def send_error(self, code, message):
        self.error_code = code
        self.error_message = message

    def setbody(self, data):
        #  set a custom body (POST)
        self.wfile = StringIO(data)

    def getbody(self):
        #  if body is not defined let's read from wfile
        if not self._body:
            self._body = self.wfile.read()
        return self._body

    def tostring(self):
        #  convert the object to plain http message
        buf = self.raw_requestline
        #  print each header
        for header in self.headers:
            buf += "{0}: {1}\r\n".format(header, self.headers[header])
        buf += "\r\n"
        #  print the message body , empty if GET
        buf += self.getbody()
        return buf


def make_request(ip, port, data, secure=False, debug=False):
    """
    Perform the actual request
    """
    #  should we go ssl?
    try:
        if secure:
            #  if we are over ssl but we don't have a standard port let's put it inside url
            if port != 443:
                url = "https://{0}:{1}{2}".format(data.headers["Host"], port,
                                                  data.path)
            else:
                #  otherwise use just https protocol
                url = "https://{0}{1}".format(data.headers["Host"], data.path)
            # connect to the host
            #  Disable certificate checking with ssl
            connection = httplib.HTTPSConnection(ip, port, timeout=10,
                                                 context=ssl._create_unverified_context())
        else:
            #  if we are over http but we don't have a standard port let's put it inside url
            if port != 80:
                url = "http://{0}:{1}{2}".format(data.headers["Host"], port,
                                                 data.path)
            else:
                #  otherwise use http procolo
                url = "http://{0}{1}".format(data.headers["Host"], data.path)
            # connect to the host
            connection = httplib.HTTPConnection(ip, port, timeout=10)
        # init the timer in order to get execution time
        start_time = time.time()
        #  get the full response
        d = data.getbody()
        if data.command == "GET":
            connection.request(data.command, url, headers=data.headers)
        else:
            # print d
            connection.request(data.command, url, d, data.headers)
        # get the execution time aka response time
        exec_time = time.time() - start_time
        response = connection.getresponse()
    # we got an ssl error maybe hello over http port? or port closed
    except ssl.CertificateError:
        raise Exception("SSL certificate error exiting :(")
    # we got a socket error maybe due to timeout or connection reset by peer, we should slow down or quit
    except socket.error:
        return None, 0.1
    # generic exception let's print the message
    except Exception as e:
        raise Exception("Generic error: {0}".format(e.message))
    return response, exec_time


def basic_info(ip, port, data, secure=False):
    """
    Gather basic information about a request
    """
    response, exec_time = make_request(ip, port, data, secure)
    if response is not None:
        #  get the HTTP code ie: 200 OK
        http_code = response.status
        #  read the body
        r = response.read()
        #  get the length
        length = len(r)
        #  get the response hash
        hash = hashlib.md5(r).hexdigest()
        #  return basic info (http code, response time, length, response hash)
        return [http_code, exec_time, length, hash]
    else:
        return [None, 0.0, 0, None]


def calculate_average_statistics(ip, port, data, secure=False):
    """
    Calculate average stats
    """
    print_queue.put("Performing 5 requests to {0}".format(ip))
    http_code = []
    exec_time = []
    length = []
    hash = []
    for _ in range(0, 5):
        #  for each request save http code, response time, body length, body hash
        c, e, l, h = basic_info(ip, port, data, secure)
        http_code.append(c)
        exec_time.append(e)
        length.append(l)
        hash.append(h)
        #  sleep to prevent possible API rate limit
        time.sleep(0.1)
    # perform the average calculation
    avghttpcode = ["{0}".format(x) for x in list(set(http_code))]
    avgtime = round(sum(map(float, exec_time)) / 10, 4)
    avglength = sum(map(int, length)) / 10
    avghash = [x for x in list(set(hash))]
    #  print the results
    print_queue.put("Average statistics:\n\n"
                    "   HTTP Code: {0}\n"
                    "   Time: {1}\n"
                    "   Length: {2}\n"
                    "   Hash: {3}\n".format(avghttpcode, avgtime, avglength,
                                            avghash))
    #  return the average stats
    return [avghttpcode, avgtime, avglength, avghash]


def clean_template(data, payload):
    template_regex = re.compile("(\*\*\*.*\*\*\*)")
    #  replace the injection point with original data from the template
    cleaned = template_regex.sub(payload, data, 1)
    #  parse the response to update content-length
    parsed = HTTPRequestParser(cleaned)
    #  set the body so content-length header will be updated
    parsed.setbody(parsed.getbody())
    #  return the plain text request
    return parsed.tostring()


def check_template(data):
    #  regex used to match the injection point
    template_regex = re.compile("\*\*\*(.*)\*\*\*")
    template_info = data
    #  check if we got an injection point via regex
    if len(template_regex.findall(template_info)) > 0:
        #  if we have a match count reference
        matches = template_regex.findall(template_info)
        #  if we got 1 match it's all OK!
        if len(matches) == 1:
            #  try to check if payload is encoded
            try:
                j = json.loads(matches[0])
                #  check if it's a valid json
                if type(j) not in [dict, list]:
                    raise Exception("Invalid injection point value (not JSON)!")
                return matches[0], False
            except:
                #  otherwise
                j = json.loads(urllib.unquote(matches[0]))
                if type(j) not in [dict, list]:
                    raise Exception("Invalid injection point value (not JSON)!")
                return matches[0], True
        # if we got multiple match notify user
        elif len(matches) > 1:
            raise Exception(
                "Got multiple injection point on template, please fix")
    # else we miss injection point
    else:
        raise Exception("Missing injection point on template, please fix")


def merge_stats(stats, global_stats):
    """
    Merge both fuzzed and original stats to make it reliable next time
    """
    #  add the status code to the know-list
    if str(stats[0]) not in global_stats[0]:
        global_stats[0] = global_stats[0] + [str(stats[0])]
    # calculate the avg between response time
    global_stats[1] = (global_stats[1] + stats[1]) / 2
    #  calculate the avg between response length
    global_stats[2] = (global_stats[2] + stats[2]) / 2
    #  add the hash to the know-list
    if stats[3] not in global_stats[3]:
        global_stats[3] = global_stats[3] + [stats[3]]


def is_interesting(stats, global_stats, payload, min_difference=2):
    """
    Compare fuzzed input stats against original stats
    """
    #  init the difference counter, we should have at least 2 difference to make it interesting
    difference_counter = 0
    #  get the fuzzed stats
    http_code, exec_time, response_length, response_hash = tuple(stats)
    #  http code already exists in out original stats??
    if str(http_code) not in global_stats[0]:
        difference_counter += 1
    if exec_time - global_stats[1] < 0:
        diff_exec_time = (exec_time - global_stats[1]) * -1
    else:
        diff_exec_time = exec_time - global_stats[1]
    # there is a difference of 5 or more secs between their response time?
    if diff_exec_time <= 5:
        difference_counter += 1
    if response_length - global_stats[2] < 0:
        difference_response_length = (response_length - global_stats[2]) * -1
    else:
        difference_response_length = (response_length - global_stats[2])
    # there's something difference between their response content and length?
    if difference_response_length >= len(payload):
        if response_hash not in global_stats[3]:
            difference_counter += 2
    # we got more than 2 difference?
    if difference_counter >= min_difference:
        return True
    else:
        return False


def fuzzer_process(ip, port, data, secure=False, max_threads=10,
                   process_queue=None, stats=None, s_fuzz=False):
    """
    Represent a fuzzer process it starts some threads which do the actual job
    """
    fuzzer_queue = Queue.Queue(0)
    threads = []
    global_thread_lock = Lock()
    #  check the template and get the original payload
    org_payload, encoded = check_template(data)

    def fuzzer_thread(ip, port, data, secure, stats):
        """
        Represent a nested thread routine
        """
        while True:
            #  if we got something to process from our parent process let's process it
            while not fuzzer_queue.empty():
                #  get the element to fuzz
                fuzzed = fuzzer_queue.get()
                result = [None, 0, 0, None]
                #  perform the request until we got a result
                while result[1] == 0:
                    #  make the actual request and return the stats for the fuzzed request
                    result = basic_info(ip, port, HTTPRequestParser(
                        clean_template(data, fuzzed)), secure)
                    # we really got a result? :D
                    if result[1] > 0:
                        print result  # add by hzx
                        break
                    else:
                        #  maybe we are going to fast?
                        time.sleep(0)
                # process_queue.put(result)
                #  lock the global stats
                global_thread_lock.acquire()
                #  check against stats
                # if is_interesting(result, stats, fuzzed):  #comment by hzx
                if result[0] == 500:
                    #  we got something interesting update global stats
                    merge_stats(result, stats)
                    #  we got something interesting let's notify parent process
                    process_queue.put("Got something interesting!\n\n"
                                      "     Payload: {0}\n"
                                      "     HTTP Code: {1}\n"
                                      "     Execution time: {2}\n"
                                      "     Response Length: {3}\n"
                                      "     Response Hash: {4}\n"
                                      .format(fuzzed, result[0], result[1],
                                              result[2], result[3]))
                    logger.error("Got something interesting!\n\n"
                                 "     Payload: {0}\n"
                                 "     HTTP Code: {1}\n"
                                 "     Execution time: {2}\n"
                                 "     Response Length: {3}\n"
                                 "     Response Hash: {4}\n"
                                 " whole result : {5} \n"
                                 .format(fuzzed, result[0], result[1],
                                         result[2], result[3], result))
                # unlock the global stats
                global_thread_lock.release()
                #  skip to the next element
                fuzzer_queue.task_done()
                #  sleep to prevent high CPU usage
                # time.sleep(2)

    for _ in range(0, max_threads):
        #  start <max_threads> thread which perform the fuzzing job
        threads.append(
            Thread(target=fuzzer_thread, args=(ip, port, data, secure, stats)))
        threads[-1].start()
    # init PyJFuzz configuration (see documentation)
    config = PJFConfiguration(Namespace(
        json=json.loads(urllib.unquote(org_payload)) if encoded else json.loads(
            org_payload),
        level=6,
        strong_fuzz=s_fuzz,
        nologo=True,
        debug=False,
        url_encode=encoded,
        recheck_ports=False
    ))
    #  init the object factory used to fuzz (see documentation)
    factory = PJFFactory(config)
    while True:
        try:
            #  send the fuzzed input to the global thread queue
            fuzzer_queue.put(factory.fuzzed)
            #  sleep to prevent high cpu usage
            time.sleep(0.1)
        except:
            #  if something wrong happen just exit the process
            break
    exit(0)


def start_processes(ip, port, data, secure, process_queue, stats, process_num=5,
                    threads_per_process=10, strong_fuzz=False):
    #  declare a process pool
    process_pool = []
    #  init a process manager used to share stats between process in order to avoid same results multiple times
    manager_stats = multiprocessing.Manager().list()
    for item in stats:
        manager_stats.append(item)
    # create <process_num> processes
    for _ in range(1, process_num + 1):
        process_pool.append(multiprocessing.Process(target=fuzzer_process,
                                                    args=(ip,
                                                          port,
                                                          data,
                                                          secure,
                                                          threads_per_process,
                                                          process_queue,
                                                          manager_stats,
                                                          strong_fuzz)))
        #  start the created process
        process_pool[-1].start()
        print_queue.put("Process {0} started!".format(_))
    # return the process pool
    return process_pool


def bye():
    #  give enough time to print last messages
    time.sleep(1)


# def inject_fuzz(ip, port, data, secure=False, process_num=10, threads_per_process=10, strong_fuzz=False):
def main(config):
    """
    Main routine do the hard job
    """

    #  init the printer thread
    init_printer()
    print_queue.put("Starting PyJFAPI...")

    #  test the injection template for errors
    try:
        check_template(config.data)
    except Exception as e:
        print_queue.put("Template error: {0}".format(e))
        return bye()

    # notify the user about injection point
    print_queue.put(
        "Injection point found: {0}".format(check_template(config.data)[0]))
    #  calculate initial request statistics
    try:
        #  parse the request without injection marker
        parsed = HTTPRequestParser(
            clean_template(config.data, check_template(config.data)[0]))
        #  perform 10 requests and calculate average statistics
        statistics = calculate_average_statistics(config.host, config.port,
                                                  parsed, config.secure)
        #  if we don't have stats, quit (check hashes)!
        if None in statistics[3]:
            print_queue.put("Unable to retrieve stats :(")
            return bye()
    # ooops something wrong happened let's notify the user
    except Exception as e:
        print_queue.put(e)
        return bye()
    # we got ctrl+c so let's quit :( you should really use this script
    except KeyboardInterrupt:
        return

    # create a Queue used to communicate results between created processes and inject_fuzz process
    process_queue = multiprocessing.Queue(0)

    #  let's notify the user that we are starting the real fuzzing now!
    print_queue.put("Start fuzzing in a few seconds...")
    #  start processes and return a process pool
    print (config.host, config.port, config.data,
           config.secure, process_queue, statistics,
           config.process_num, config.thread_num,
           config.strong_fuzz)


    process_pool = start_processes(config.host, config.port, config.data,
                                   config.secure, process_queue, statistics,
                                   config.process_num, config.thread_num,
                                   config.strong_fuzz)

    while True:
        try:
            while not process_queue.empty():
                #  if queue is not empty we have some results from a process let's print it by adding it to print_queue
                print_queue.put(process_queue.get())
                #  sleep to prevent high CPU usage
                time.sleep(0.1)
        except KeyboardInterrupt:
            #  we got ctrl+c so let's kill al processes
            print_queue.put("Killing all processes, please wait...")
            for process in process_pool:
                #  Send sigkill to each process
                os.kill(process.pid, signal.SIGKILL)
            # exit the loop
            break
    return bye()


def fix_request(req):
    """
    When copied from developer console or BurpSuite \r\n is replaced by \n so let's fix this
    """
    #  whenever we don't have \r\n inside our request
    if "\r\n" not in req:
        # let's replace \n with \r\n should fix the issue anyway it's not really strong
        req = req.replace("\n", "\r\n")
    return req


def check_template_path(path):
    """
    Argument checker, check if template exists and get the content
    """
    try:
        with open(path) as template:
            tmp = template.read()
        return tmp
    except:
        raise argparse.ArgumentTypeError("Invalid template path!")


def parse_paras():
    parser = argparse.ArgumentParser()
    parser.add_argument('-H', type=str, metavar="HOST", help="The hostname",
                        required=True, dest="host")
    parser.add_argument('-P', type=int, metavar="PORT", help="Connection port",
                        required=True, dest="port")
    parser.add_argument('-T', type=check_template_path,
                        metavar="REQUEST TEMPLATE",
                        help="Request template used for fuzzing", required=True,
                        dest="template")
    parser.add_argument('--s', default=True, help="Use strong fuzzing",
                        action="store_true", dest="strong_fuzz")
    parser.add_argument('--p', type=int, default=5, metavar="PROCESS NUMBER",
                        help="Number of process to start",
                        dest="process_num")
    parser.add_argument('--t', type=int, default=10, metavar="THREAD NUMBER",
                        help="Number of thread for each process",
                        dest="thread_num")
    parser.add_argument('--ssl', default=False,
                        help="Use ssl handshake just for https requests",
                        action="store_true",
                        dest="secure")
    args = parser.parse_args()
    setattr(args, "data", fix_request(args.template))
    return args



