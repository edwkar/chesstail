import pgn
import re
import urllib2
import sys
import threading
from time import sleep
from datetime import datetime

def debug_log(msg):
    sys.stderr.write('%s: %s\n' % (datetime.now(), msg,))

POLLING_INTERVAL = 20
ERROR_SLEEP_TIME = 80
CHESS_COM = 'http://www.chess.com/'
PRINT_LOCK = threading.Lock()


def read_url(url):
    x = urllib2.urlopen(url)
    text = x.read()
    x.close()
    return text


class SingleGameTracker(threading.Thread):

    def __init__(self, game_id):
        super(SingleGameTracker, self).__init__()
        self.daemon = True
        self._game_id = game_id

    def run(self):
        should_continue = True
        last_moves = None

        iteration = -1
        while should_continue:
            iteration += 1

            try:
                text = read_url(CHESS_COM +
                                'echess/download_pgn?id=%d' % self._game_id)
            except Exception as e:
                debug_log('ERROR: failed to read game data from chess.com :(')
                #print e
                #print type(e)
                sleep(ERROR_SLEEP_TIME)
                continue

            game = pgn.loads(text)[0]
            moves = self._trim_moves(game.moves)
            num_moves = len(moves)

            if iteration == 0:
                debug_log('started tracking game %d between %s and %s' % (
                          self._game_id,
                          game.white,
                          game.black,))

            msg_end = None

            if game.result in ['1-0', '0-1', '1/2-1/2']:
                msg_end = 'ended with score %s after %d moves' % (game.result,
                                                                  num_moves,)
                should_continue = False
            elif moves and moves != last_moves:
                msg_end = '%2d. %s%s' % (1 + (num_moves-1) // 2,
                                         '' if num_moves % 2 == 1 else '...',
                                         moves[-1],)
            last_moves = moves[:]

            if msg_end and iteration != 0:
                with PRINT_LOCK:
                    sys.stdout.write('%25s | %-16s\n' % (
                            '%s vs. %s' % (game.white, game.black),
                            msg_end,))
                    sys.stdout.flush()

            sleep(POLLING_INTERVAL)

    @staticmethod
    def _trim_moves(moves):
        moves = moves[:]
        if moves and moves[-1] == '*':
            moves.pop()
        return moves


class TrackingManager(object):

    def __init__(self, users):
        self._users = users

    def run(self):
        tracked_games = set()

        while True:
            try:
                cur_game_ids = self._read_game_ids()
            except:
                debug_log('ERROR. failed to fetch game ids from chess.com :(')
                sleep(ERROR_SLEEP_TIME)
                continue

            for id_ in cur_game_ids:
                if not id_ in tracked_games:
                    debug_log('preparing to track game %d...' % id_)
                    tracker = SingleGameTracker(id_)
                    tracker.start()
                    tracked_games.add(id_)
            sleep(POLLING_INTERVAL)

    def _read_game_ids(self):
        res = set()
        for u in self._users:
            user_page = read_url(CHESS_COM + 'members/view/%s' % u)
            cur_seg = user_page[user_page.find('Current Games'):
                                user_page.find('Finished Games')]
            for id_ in re.findall(r'href="/echess/game\?id=(\d+)', cur_seg):
                res.add(int(id_))
        return res


def main(argv):
    debug_log('yo')
    users = argv[1:]
    if not users:
        print 'usage: python %s <user_1> <user_2> ... <user_n>' % argv[0]
        sys.exit(1)

    manager = TrackingManager(users)
    manager.run()


if __name__ == '__main__':
    main(sys.argv)
