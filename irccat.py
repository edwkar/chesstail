#! /usr/bin/env python
#
# (this is (more or less) irccat from irclib python library.)

import sys
import argparse
import itertools

import irc.client
import irc.logging

target = None
"The nick or channel to which to send messages"

def on_connect(connection, event):
    if irc.client.is_channel(target):
        connection.join(target)
        return
    main_loop(connection)

def on_join(connection, event):
    main_loop(connection)

def get_lines():
    while True:
        yield sys.stdin.readline().rstrip()

def main_loop(connection):
    for line in itertools.takewhile(bool, get_lines()):
        print(line)
        connection.privmsg(target, line)
    connection.quit("Using irc.client.py")

def on_disconnect(connection, event):
    raise SystemExit()

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('server')
    parser.add_argument('nickname')
    parser.add_argument('target', help="a nickname or channel")
    parser.add_argument('-p', '--port', default=6667, type=int)
    irc.logging.add_arguments(parser)
    return parser.parse_args()

def main():
    global target

    args = get_args()
    irc.logging.setup(args)
    target = args.target

    client = irc.client.IRC()
    try:
        c = client.server().connect(args.server, args.port, args.nickname)
    except irc.client.ServerConnectionError:
        print(sys.exc_info()[1])
        raise SystemExit(1)

    c.add_global_handler("welcome", on_connect)
    c.add_global_handler("join", on_join)
    c.add_global_handler("disconnect", on_disconnect)

    client.process_forever()

if __name__ == '__main__':
    main()
