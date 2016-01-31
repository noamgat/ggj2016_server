import json
import gevent

__author__ = 'noam'

from time import time

MAX_PLAYERS_PER_ROOM = 4


class GameRoom(object):
    def __init__(self, patterns, fade_time, send_func, seconds_per_level=30, room_id=0):
        """
        @type pattern: PatternModel
        """
        self.patterns = patterns
        self.current_level_index = -1
        self.pattern = patterns[0]
        self.seconds_per_level = seconds_per_level
        self.level_start_time = 0

        self.player_id_to_client = {}
        self.last_edge_fill_times = [0]
        self.fade_time = fade_time
        self.send_func = send_func
        self.did_send_win_message = False
        self.did_complete_game = False
        self.did_room_start = False
        self.room_id = room_id

    def get_player_id(self, client):
        for player_id in self.player_id_to_client:
            if self.player_id_to_client[player_id] == client:
                return player_id
        raise Exception("Could not find player id")

    def start_room(self):
        if not self.did_room_start:
            self.did_room_start = True
            self.send_message("start_game", {"room_id": self.room_id})

    @property
    def num_players(self):
        return len(self.player_id_to_client)

    def add_player(self, client):
        player_id = 1
        while self.player_id_to_client.has_key(player_id):
            player_id += 1
        self.player_id_to_client[player_id] = client
        self.send_message("connect", {"player_id": player_id, "room_id": self.room_id}, client)
        self._broadcast_num_players_changed()
        if not self.did_room_start and self.num_players == MAX_PLAYERS_PER_ROOM:
            self.start_room()

    def remove_player(self, client):
        try:
            player_id = self.get_player_id(client)
            self.player_id_to_client.pop(player_id)
            self._broadcast_num_players_changed()
        except Exception, e:
            #This is not the room that the client was in
            pass

    def _broadcast_num_players_changed(self):
        self.send_message("num_players_changed", {"num_players": self.num_players, "room_id": self.room_id})

    def _handle_client_filled_edge(self, client, edge_id):
        if not self.is_in_level:
            return
        player_id = self.get_player_id(client)
        self.last_edge_fill_times[edge_id] = time()
        self.send_message("fill", {"player_id": player_id, "edge_id": edge_id})
        if self.did_win_current_level:
            self.send_message("win_level")
            self.level_start_time = 0

    @property
    def did_win_current_level(self):
        num_edges = float(len(self.last_edge_fill_times))
        num_good_edges = 0
        max_fill_time = time() - self.fade_time
        for fill_time in self.last_edge_fill_times:
            if fill_time >= max_fill_time:
                num_good_edges += 1
        relative_good_edges = num_good_edges / num_edges
        return relative_good_edges > 0.9

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
        if message["action"] == "start":
            if not self.did_room_start and self.num_players > 0:
                self.start_room()
        if message["action"] == "start_level":
            if self.did_room_start and not self.is_in_level:
                self._start_next_level()

    def _start_next_level(self):
        if self.current_level_index == len(self.patterns) - 1:
            self.did_complete_game = True
            self.send_message("complete")
            self.pattern = None
        else:
            self.current_level_index += 1
            self.pattern = self.patterns[self.current_level_index]
            self.last_edge_fill_times = [0] * len(self.pattern.edges)
            self.send_message("start_level", {"pattern": self.pattern.to_primitive(), "room_id": self.room_id})
            self.level_start_time = time()

    @property
    def is_room_active(self):
        return self.num_players > 0 and not self.did_complete_game

    @property
    def is_in_level(self):
        return self.did_room_start and not self.did_complete_game and self.level_start_time > 0

    def update(self):
        if self.is_in_level and time() > self.level_start_time + self.seconds_per_level:
            self.send_message("lose_level")
            self.level_start_time = 0
            self.current_level_index = -1
