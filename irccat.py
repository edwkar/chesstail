import Queue
import socket
import sys
import threading
import time


PONG_INTERVAL = 60


class StdinReader(threading.Thread):
    def __init__(self):
        super(StdinReader, self).__init__()
        self._queue = Queue.Queue()

    def run(self):
        while True:
            try:
                line = sys.stdin.readline()
            except Exception as e:
                print ('exception raised in reading thread, sleeping and ' +
                       're-trying...')
                print e
                time.sleep(0.5)
                continue
            self._queue.put(line)

    def readline(self):
        try:
            return self._queue.get(False)
        except Queue.Empty:
            return None


class IRCCatBot(object):
    def __init__(self, server_addr, server_port, chan, nick, reader):
        self._server_addr = server_addr
        self._server_port = server_port
        self._chan = chan
        self._nick = nick
        self._reader = reader

    def run(self):
        s = socket.create_connection((self._server_addr, self._server_port,),)

        n = self._nick
        s.send('USER %s %s %s :%s\n' % (n, n, n, n,))
        s.send('NICK %s\n' % n)
        s.send('JOIN %s\n' % self._chan)

        while True:
            s.settimeout(0.01)
            irc_line = ''
            try:
                irc_line = s.recv(512).strip()
            except socket.timeout:
                pass
            if irc_line and irc_line.startswith('PING'):
                response = irc_line.strip().split(' ')[1]
                s.send('PONG %s\n' % response)
            s.settimeout(10)

            line = self._reader.readline()
            if line and line.strip():
                print '"%s"' % line
                s.send('PRIVMSG %s :%s' % (self._chan, line,))

            time.sleep(0.1)

    def rerun(self):
        while True:
            try:
                self.run()
            except Exception as e:
                print ('exception raised in bot thread, sleeping and ' +
                       're-starting...')
                print e
                print type(e)
                time.sleep(60)


def main(argv):
    reader = StdinReader()
    reader.daemon = True
    reader.start()

    try:
        bot = IRCCatBot(*(argv[1:] + [reader]))
        bot.rerun()
    except KeyboardInterrupt:
        print 'got interrupt signal from user, exiting...'
        sys.exit(0)


if __name__ == '__main__':
    main(sys.argv)
