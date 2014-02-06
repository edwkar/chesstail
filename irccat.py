import Queue
import socket
import sys
import threading
import time


PONG_INTERVAL = 40


class StdinReader(threading.Thread):
    def __init__(self):
        super(StdinReader, self).__init__()
        self._queue = Queue.Queue()

    def run(self):
        while True:
            line = sys.stdin.readline()
            self._queue.put(line)

    def readline(self, timeout):
        return self._queue.get(timeout)


class IRCCatBot(object):
    def __init__(self, server_addr, server_port, chan, nick, reader):
        self._server_addr = server_addr
        self._server_port = server_port
        self._chan = chan
        self._nick = nick
        self._reader = reader

    def run(self):
        s = socket.create_connection((self._server_addr, self._server_port,),
                                     timeout=1)

        n = self._nick
        s.send('USER %s %s %s :%s\n' % (n, n, n, n,))
        s.send('NICK %s\n' % n)
        s.send('JOIN %s\n' % self._chan)

        last_pong_time = 0

        while True:
            t_now = int(time.time())

            if t_now - last_pong_time > PONG_INTERVAL:
                print '-* pong *-'
                s.send('PONG %s\n' % self._server_addr)
                last_pong_time = t_now

            line = self._reader.readline(timeout=1)
            if line:
                print line
                s.send('PRIVMSG %s :%s' % (self._chan, line,))

            time.sleep(0.1)


def main(argv):
    reader = StdinReader()
    reader.daemon = True
    reader.start()

    try:
        bot = IRCCatBot(*(argv[1:] + [reader]))
        bot.run()
    except KeyboardInterrupt:
        print 'got interrupt signal from user, exiting...'
        sys.exit(0)


if __name__ == '__main__':
    main(sys.argv)
