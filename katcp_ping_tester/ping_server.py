#!/usr/bin/env python

from __future__ import print_function

import sys
import time
import logging

import tornado

import katcp


logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

stdout_handle = logging.StreamHandler(sys.stdout)
stdout_handle.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - '
                              '%(levelname)s - %(message)s')
stdout_handle.setFormatter(formatter)
logger.addHandler(stdout_handle)


class EchoServer(katcp.DeviceServer):

    def request_ping(self, req, msg):
        """bla"""
        if not msg.arguments:
            pong_count = 1
            payload_size = 1
        else:
            try:
                pong_count = int(msg.arguments[0])
            except ValueError:
                pong_count = 1

            try:
                payload_size = int(msg.arguments[1])
            except ValueError:
                payload_size = 1

        payload = ''
        for count in range(payload_size):
            payload += 'a'

        for count in range(pong_count):
            req.inform('pong {0} of {1}: {2}'.
                       format(count + 1, pong_count, payload))
            self._inc_pong()

        self._inc_ping()
        return req.make_reply("ok", 'ping number {0} with {1} pongs'.
                              format(self._ping_counter, pong_count))

    def setup_sensors(self):
        self._ping_counter = -1
        self._pong_counter = -1
        self.restarted = False
        self.ping_sensor = katcp.Sensor(int, 'ping_counter', 'In', '', None)
        self.add_sensor(self.ping_sensor)
        self.pong_sensor = katcp.Sensor(int, 'pong_counter', 'Out', '', None)
        self.add_sensor(self.pong_sensor)
        self._inc_ping()
        self._inc_pong()

    def _inc_ping(self):
        self._ping_counter += 1
        status = katcp.Sensor.NOMINAL
        self.ping_sensor.set(time.time(), status, self._ping_counter)

    def _inc_pong(self):
        self._pong_counter += 1
        status = katcp.Sensor.NOMINAL
        self.pong_sensor.set(time.time(), status, self._pong_counter)

io_loop = tornado.ioloop.IOLoop.instance()
katcp_server = EchoServer(host='', port=9909, logger=logger)
katcp_server.set_ioloop(io_loop)
io_loop.add_callback(katcp_server.start)
try:
    io_loop.start()
except KeyboardInterrupt:
    katcp_server.stop()
