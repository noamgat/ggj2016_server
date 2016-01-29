import os
from game import app
from gevent.wsgi import WSGIServer
from geventwebsocket.handler import WebSocketHandler

__author__ = 'noam'


class MyWebSocketHandler(WebSocketHandler):
    def upgrade_websocket(self):
        self.environ.update({
            'HTTP_UPGRADE' : self.environ.get('HTTP_UPGRADE', '').split(',')[0]
        })
        return super(MyWebSocketHandler, self).upgrade_websocket()

port = int(os.environ.get("PORT", 8000))

http_server = WSGIServer(('', port), app, handler_class=MyWebSocketHandler)
print "Finished loading, starting server"
http_server.serve_forever()
