#!/usr/bin/env python

#
# A light weight telnet client with syntax
# highlighting and message formating for use with katcp.
# No special interpretation of the messages are performed.
#

from __future__ import print_function
import telnetlib
import threading
import sys

INFORM = '\033[94m'
OKGREEN = '\033[92m'
REQUEST = '\033[93m'
RESPONSE = '\033[91m'
INPUT = '\033[0m'


class ReadThread(threading.Thread):

    def __init__(self, name, telnet_session):
        self.keep_reading = True
        self.telnet = telnet_session
        super(ReadThread, self).__init__(name=name)
        self.raw = False
        self.prefix_colour = ''

    def run(self):
        text_buffer = ''
        while self.keep_reading:
            text = tn.read_eager()
            text_buffer += text
            if '\n' in text or '\r' in text:
                text_buffer = self.print_line(text_buffer)

    def print_line(self, text):
        if not text or not text.strip():
            return text
        ret_str = ''
        lines = text.split('\n')
        if text[-1] != '\n':
            ret_str = lines.pop()
        for line in lines:
            self.set_colour(line)
            self.print_katcp(line + '\n')
        return ret_str

    def stop(self):
        self.keep_reading = False

    def set_colour(self, line):
        if line and self.prefix_colour is not False:
            color = {'#': INFORM,
                     '!': RESPONSE}.get(line[0])
            if color:
                self.prefix_colour = color

    def print_katcp(self, text):
        if not self.raw:
            text = text.replace('\\n', '\n')
            text = text.replace('\\_', ' ')
            text = text.replace('\\@', '\@')
            text = text.replace('\_', ' ')
            text = text.replace(r'\\n', '\n')
        if self.prefix_colour is False:
            colour = ''
        else:
            colour = self.prefix_colour
        print('\r{0}{1}'.format(colour, text), end='')

    def toggle_raw(self):
        self.raw = not self.raw

    def toggle_colour(self):
        if self.prefix_colour is False:
            self.prefix_colour = ''
        else:
            self.prefix_colour = False


def print_help():
    print('Help')
    print('----')
    print('\t \? or \help : Display this.')
    print('\t \quit or \exit : Close the connection.')
    print('\t \\raw : Toggle Raw mode do not escape KatCP special characters.')
    print('\t \colour : Toggle colour display.')
    # \t for timing on/off.

if __name__ == '__main__':
    try:
        host = sys.argv[1]
        port = int(sys.argv[2])
    except IndexError:
        print('Specify Host and Port')
        sys.exit()
    except ValueError:
        print('Invalid Host or Port')
        sys.exit()
    print('Connected to', host, port)
    print_help()
    tn = telnetlib.Telnet(host, port)

    reader = ReadThread('read{0}:{1}'.format(host, port), tn)
    reader.start()
    history = []
    run = True
    while run:
        try:
            choice = raw_input('%s>>> ' % INPUT)
            choice = choice.strip()
        except KeyboardInterrupt:
            run = False

        if choice.startswith('\\'):
            # This is an internal to katcp_consore command.
            key = choice.strip('\\').lower()
            if key in ['quit', 'exit', 'q', 'e']:
                run = False
            elif key in ['help', '?', 'h']:
                print_help()
            elif key in ['raw', 'r']:
                reader.toggle_raw()
            elif key in ['colour', 'c', 'color']:
                reader.toggle_colour()
        else:
            print('{0}{1}'.format(REQUEST, choice))
            tn.write(choice)
            tn.write('\n')

    reader.stop()
    reader.join()
    tn.close()
