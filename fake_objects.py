import datetime

class FakePartialUser:
    def __init__(self, id:str, login:str, name:str):
        self.id:str=id, 
        self.login:str=login,
        self.name:str=name,
        
class FakeChannelRaid:
    def __init__(self):
        self.from_broadcaster = FakePartialUser("1111", 'None', 'None')
        self.to_broadcaster = FakePartialUser("1111", "Kazi_Kamui", "Kazi_Kamui")
        self.viewer_count = 10
        self.timestamp = datetime.datetime.now().strftime("%I:%M%p")