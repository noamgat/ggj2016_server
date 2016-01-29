import json
import gevent

__author__ = 'noam'

from time import time


class GameRoom(object):
    def __init__(self, pattern, fade_time, send_func):
        """
        @type pattern: PatternModel
        """
        self.pattern = pattern

        self.player_id_to_client = {}
        self.last_edge_fill_times = [0] * len(pattern.edges)
        self.fade_time = fade_time
        self.num_players = 0
        self.send_func = send_func
        self.did_send_win_message = False

    def get_player_id(self, client):
        for player_id in self.player_id_to_client:
            if self.player_id_to_client[player_id] == client:
                return player_id
        raise Exception("Could not find player id")

    def add_player(self, client):
        self.num_players += 1
        player_id = self.num_players
        self.player_id_to_client[player_id] = client
        self.send_message("load", {"player_id": player_id, "pattern": self.pattern.to_primitive()}, client)

    def remove_player(self, client):
        player_id = self.get_player_id(client)
        self.player_id_to_client.pop(player_id)

    def _handle_client_filled_edge(self, client, edge_id):
        player_id = self.get_player_id(client)
        self.last_edge_fill_times[edge_id] = time()
        self.send_message("fill", {"player_id": player_id, "edge_id": edge_id})
        if not self.did_send_win_message and self.did_win():
            self.send_message("win")

    def did_win(self):
        max_fill_time = time() - self.fade_time
        for fill_time in self.last_edge_fill_times:
            if fill_time < max_fill_time:
                return False
        return True

    def send_message(self, action, data=None, client=None):
        message = {"action": action}
        if data is not None:
            message["data"] = data
        message = json.dumps(message)
        clients = [client] if client is not None else self.player_id_to_client.values()
        for client in clients:
            self.send_func(client, message)

    def handle_client_message(self, client, message):
        message = json.loads(str(message))
        if message["action"] == "fill":
            edge_id = message["data"]["edge_id"]
            self._handle_client_filled_edge(client, edge_id)