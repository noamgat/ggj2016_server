import os
import unittest
from game_types import PatternModel
import json
from gameroom import GameRoom

__author__ = 'noam'


class Tests(unittest.TestCase):
    def _load_level(self, fn):
        content = open(fn).read()
        content = json.loads(content)
        level = PatternModel(content)
        return level

    def test_loading_levels(self):
        for fn in os.listdir('levels'):
            level = self._load_level('levels/' + fn)
            print fn
            print level.to_primitive()

    def _send_func(self, client, message):
        print "Sending %s to %s" % (message, str(client))

    def test_simple_game(self):
        level = self._load_level("levels/level1.json")
        game_room = GameRoom(level, 2, self._send_func)
        game_room.add_player(1)
        game_room.add_player(2)
        game_room.handle_client_message(1, json.dumps({"action": "fill", "data": {"edge_id": 0}}))
