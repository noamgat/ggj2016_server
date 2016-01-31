import os
import unittest
from game import load_level, get_level_names
from game_types import PatternModel
import json
from gameroom import GameRoom

__author__ = 'noam'


class Tests(unittest.TestCase):

    def test_loading_levels(self):
        for fn in get_level_names():
            level = load_level(fn)
            print fn
            print level.to_primitive()

    def _send_func(self, client, message):
        print "Sending %s to %s" % (message, str(client))

    def test_simple_game(self):
        level = load_level("levels/level1.json")
        game_room = GameRoom([level], 2, self._send_func)
        game_room.add_player(1)
        game_room.add_player(2)
        game_room.handle_client_message(1, json.dumps({"action": "start"}))
        for i in xrange(len(level.edges)):
            game_room.handle_client_message(1, json.dumps({"action": "fill", "data": {"edge_id": i}}))

    def test_disconnect_before_start(self):
        level = load_level("levels/level1.json")
        game_room = GameRoom([level], 2, self._send_func)
        game_room.add_player(1)
        game_room.add_player(2)
        game_room.add_player(3)
        game_room.remove_player(1)
        game_room.add_player(4)
        game_room.handle_client_message(2, json.dumps({"action": "start"}))
        game_room.handle_client_message(2, json.dumps({"action": "start_level"}))
        for i in xrange(len(level.edges)):
            game_room.handle_client_message(4, json.dumps({"action": "fill", "data": {"edge_id": i}}))

    def test_multiple_levels(self):
        levels = [load_level(fn) for fn in get_level_names()]
        game_room = GameRoom(levels, 2, self._send_func)
        game_room.add_player(1)
        game_room.add_player(2)
        game_room.handle_client_message(1, json.dumps({"action": "start"}))
        for level in levels:
            game_room.handle_client_message(2, json.dumps({"action": "start_level"}))
            for i in xrange(len(level.edges)):
                game_room.handle_client_message(1, json.dumps({"action": "fill", "data": {"edge_id": i}}))
        game_room.handle_client_message(2, json.dumps({"action": "start_level"}))
        self.assertFalse(game_room.is_room_active)

    def test_lose_level(self):
        level = load_level("levels/level1.json")
        game_room = GameRoom([level], 2, self._send_func, 2, 3)
        game_room.add_player(1)
        game_room.add_player(2)
        game_room.handle_client_message(1, json.dumps({"action": "start"}))
        game_room.handle_client_message(2, json.dumps({"action": "start_level"}))
        game_room.update()
        self.assertTrue(game_room.is_in_level)
        from time import sleep
        sleep(3)
        game_room.update()


