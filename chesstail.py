import pgn
import re
import requests
import sys
import threading
import time


POLLING_INTERVAL = 30
ERROR_SLEEP_TIME = 60
CHESS_COM = 'http://www.chess.com/'
PRINT_LOCK = threading.Lock()


def read_url(url):
    r = requests.get(url)
    return r.text


class SingleGameTracker(threading.Thread):

    def __init__(self, game_id):
        super(SingleGameTracker, self).__init__()
        self.daemon = True
        self._game_id = game_id

    def run(self):
        last_moves = None

        while True:
            try:
                text = read_url(CHESS_COM +
                                'echess/download_pgn?id=%d' % self._game_id)
            except:
                print 'failed to read game data from chess.com :('
                time.sleep(ERROR_SLEEP_TIME)
                continue

            game = pgn.loads(text)[0]
            moves = game.moves[:]
            if moves and moves[-1] == '*':
                moves.pop()
            num_moves = len(moves)

            msg_end = None

            if game.result == '1-0':
                msg_end = 'ended with score 1-0 after %d moves' % num_moves
                return
            elif game.result == '0-1':
                msg_end = 'ended with score 0-1 after %d moves' % num_moves
                return
            elif game.result == '1/2-1/2':
                msg_end = 'ended with score 1/2-1/2 after %d moves' % num_moves
                return
            else:
                if moves and moves != last_moves:
                    msg_end = '%2d. %s%s' % (
                        num_moves // 2,
                        '' if num_moves % 2 == 1 else '...',
                        moves[-1],
                    )
                last_moves = moves[:]

            if msg_end:
                with PRINT_LOCK:
                    sys.stdout.write(
                        '%25s | %-16s  (%s)\n' % (
                            '%s vs. %s' % (game.white, game.black),
                            msg_end,
                            CHESS_COM + 'echess/game?id=%d' % self._game_id))
                    sys.stdout.flush()

            time.sleep(POLLING_INTERVAL)


class TrackingManager(object):

    def __init__(self, users):
        self._users = users

    def run(self):
        tracked_games = set()

        while True:
            try:
                cur_game_ids = self._read_game_ids()
            except:
                print 'failed to fetch game ids from chess.com :('
                time.sleep(ERROR_SLEEP_TIME)
                continue

            for id_ in cur_game_ids:
                if not id_ in tracked_games:
                    SingleGameTracker(id_).start()
                    tracked_games.add(id_)
            time.sleep(POLLING_INTERVAL)

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
    users = argv[1:]
    if not users:
        print 'usage: python %s <user_1> <user_2> ... <user_n>' % argv[0]
        sys.exit(1)

    print 'tracking all games for users %s...' % ' '.join(users)
    TrackingManager(users).run()


if __name__ == '__main__':
    main(sys.argv)
