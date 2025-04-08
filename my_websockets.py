import logging
from websocket import create_connection

LOGGER: logging.Logger = logging.getLogger(__name__)

class my_websockets():
    def __init__(self):
        
        self.ws = create_connection("wss://eventsub.wss.twitch.tv/ws")
    
    def test(self):
        ws = self.ws
        self.ws_info = ws.recv()
        LOGGER.info("Sending 'Hello, World'...")
        ws.send("Hello, World")
        LOGGER.info("Sent")
        LOGGER.info("Receiving...")
        LOGGER.info("Received %s", ws.recv())
    
    def close(self):
        self.ws.close()
