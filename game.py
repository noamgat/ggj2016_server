# -*- coding: utf-8 -*-

"""
Chat Server
===========

This simple application uses WebSockets to run a primitive chat server.
"""
import json

import os
import logging
import gevent
from flask import Flask, render_template
from flask_sockets import Sockets
from game_types import PatternModel
from gameroom import GameRoom

app = Flask(__name__)
app.debug = 'DEBUG' in os.environ

sockets = Sockets(app)


def load_level(fn):
    pattern = open(fn).read()
    pattern = json.loads(pattern)
    pattern = PatternModel(pattern)
    return pattern


def get_level_names():
    return ["levels/" + fn for fn in os.listdir('levels')]

@app.before_first_request
def setup_logging():
    if not app.debug:
        # In production mode, add log handler to sys.stderr.
        app.logger.addHandler(logging.StreamHandler())
        app.logger.setLevel(logging.DEBUG)


class GameBackend(object):
    """Interface for registering and updating WebSocket clients."""

    def __init__(self):
        self.message_queue = list()
        self.pickup_game_room = None
        """:type GameRoom"""
        self.game_rooms = []
        self.clients_to_rooms = {}

    def register(self, client):
        """Register a WebSocket connection for the game."""
        if self.pickup_game_room is None or self.pickup_game_room.did_game_start:
            app.logger.info("Creating new room")
            patterns = [load_level(fn) for fn in get_level_names()]
            self.pickup_game_room = GameRoom(patterns, 2, self.send)
            self.game_rooms.append(self.pickup_game_room)
        self.pickup_game_room.add_player(client)
        self.clients_to_rooms[client] = self.pickup_game_room

    def unregister(self, client):
        self.clients_to_rooms[client].remove_player(client)
        self.clients_to_rooms.pop(client)

    def _send_impl(self, client, data):
        """Send given data to the registered client.
        Automatically discards invalid connections."""
        try:
            client.send(data)
        except Exception, e:
            app.logger.info("Client disconnected: " + e.message)
            self.unregister(client)

    def send(self, client, data):
        gevent.spawn(self._send_impl, client, data)

    def run(self):
        """Listens for new messages in queue, and sends them to game room."""
        while True:
            messages_copy = self.message_queue[:]
            self.message_queue = []
            for client, message in messages_copy:
                self.clients_to_rooms[client].handle_client_message(client, message)

            rooms_to_remove = []
            for room in self.game_rooms:
                room.update()
                if not room.is_room_active:
                    rooms_to_remove.append(room)
            for room in rooms_to_remove:
                self.game_rooms.remove(room)
            gevent.sleep(0.01)

    def start(self):
        """Maintains queue subscription in the background."""
        gevent.spawn(self.run)

    def enqueue(self, client, message):
        self.message_queue.append((client, message))


game = GameBackend()
game.start()


@app.route('/')
def hello():
    app.logger.info("Hello")
    return render_template('index.html')


@sockets.route('/room')
def inbox(ws):
    """Receives incoming chat messages, inserts them into Redis."""
    app.logger.info("Start of room route")
    game.register(ws)
    while not ws.closed:
        # Sleep to prevent *contstant* context-switches.
        gevent.sleep(0.1)
        message = ws.receive()
        # app.logger.debug("HI")
        if message:
            app.logger.info(u'Inserting message: {}'.format(message))
            game.enqueue(ws, message)
    game.unregister(ws)
    app.logger.info("End of room route")




