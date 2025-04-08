from websocket import create_connection

class my_websockets():
    def __init__(self):
        self.ws = create_connection("wss://eventsub.wss.twitch.tv/ws")
    
    def test(self):
        ws = self.ws
        print(ws.recv())
        print("Sending 'Hello, World'...")
        ws.send("Hello, World")
        print("Sent")
        print("Receiving...")
        result =  ws.recv()
        print("Received '%s'" % result)
    
    def close(self):
        self.ws.close()
