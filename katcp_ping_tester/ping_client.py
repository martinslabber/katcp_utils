#!/usr/bin/env python

from __future__ import print_function

import time
import argparse

import tornado

from katcp.inspecting_client import InspectingClientAsync

"""
PING 127.0.0.1 (127.0.0.1): 56 data bytes
64 bytes from 127.0.0.1: icmp_seq=0 ttl=64 time=0.046 ms
64 bytes from 127.0.0.1: icmp_seq=1 ttl=64 time=0.051 ms

--- 127.0.0.1 ping statistics ---
2 packets transmitted, 2 packets received, 0.0% packet loss
round-trip min/avg/max/stddev = 0.046/0.049/0.051/0.002 ms"
"""


def parse_args():
    parser = argparse.ArgumentParser(description='Send KatCP requests and'
                                     'report on the responses.')
    parser.add_argument('-r', '--requests', dest='request_count',
                        action='store', default=None,
                        help='Number of requests to send.')
    parser.add_argument('-i', '--informs', dest='inform_count',
                        action='store', default=1, type=int,
                        help='Number of informs the server should send back.')
    parser.add_argument('-s', '--size', dest='size',
                        action='store', default=1, type=int,
                        help='Additional payload size on each inform.')
    parser.add_argument('host')
    parser.add_argument('port', type=int)
    return parser.parse_args()


class DoPing(object):

    def __init__(self, ic, host, requests, informs, size):
        self.host = host
        self.inspecting_client = ic
        self.running = False
        self.count = 0
        self.recieved_informs = 0
        self.durations = []
        if not requests:
            self.requests = None
        else:
            try:
                self.requests = int(requests)
            except ValueError:
                self.requests = None

        if not informs:
            informs = 1
        if not size:
            size = 1

        try:
            self.informs = int(informs)
        except ValueError:
            self.informs = 1

        try:
            self.size = int(size)
        except ValueError:
            self.size = 1

    @tornado.gen.coroutine
    def run(self):
        yield self.inspecting_client.until_synced()
        if self.inspecting_client.is_connected():
            self.running = True
        else:
            self.running = False
            print('Timeout.')
        while self.running:
            stop_watch = time.time()
            self.count += 1
            request = self.inspecting_client.simple_request('ping',
                                                            self.informs,
                                                            self.size)
            response = yield request
            reply_ok = response[0].reply_ok()
            recieved_informs = len(response[1])
            self.recieved_informs += recieved_informs
            duration = time.time() - stop_watch
            if reply_ok and recieved_informs == self.informs:
                self.durations.append(duration)
                print('{0} informs from {1}: seq={2} time={3}s'.
                      format(recieved_informs, self.host, self.count, duration))
            else:
                print('failed on {0}'.format(self.count))
            if self.requests and self.requests <= self.count:
                self.running = False
        self.inspecting_client.ioloop.stop()

    def summary(self):
        print("--- {0} ping statistics ---".format(self.host))
        print("{0} requests transmitted, {1} responses received, {2}% response"
              " loss in {3} s".
              format(self.count, len(self.durations),
                     100 - (len(self.durations)/float(self.count)) * 100,
                     sum(self.durations)))
        print("round-trip min/avg/max = {0}/{1}/{2} s".
              format(min(self.durations),
                     sum(self.durations) / float(len(self.durations)),
                     max(self.durations)))
        print("request had {0} informs with each {1} bytes additional pyload".
              format(self.informs, self.size))
        print("recieved {0} informs in total".format(self.recieved_informs))

    def close(self):
        self.running = False

if __name__ == "__main__":
    args = parse_args()
    print(args.host)
    print(args.port)
    print(args.request_count)

    io_loop = tornado.ioloop.IOLoop.instance()
    ic = InspectingClientAsync(args.host, args.port)
    do_ping = DoPing(ic, args.host, args.request_count,
                     args.inform_count, args.size)
    ic.set_ioloop(io_loop)
    io_loop.add_callback(ic.connect)
    io_loop.add_callback(do_ping.run)
    try:
        io_loop.start()
    except KeyboardInterrupt:
        do_ping.close()
        ic.close()
    do_ping.summary()
