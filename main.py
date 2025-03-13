from twitchAPI.twitch import Twitch
from twitchAPI.webhook import TwitchWebHook
from pprint import pprint

def callback_stream_changed(uuid, data):
    print('Callback for UUID ' + str(uuid))
    pprint(data)

twitch = Twitch(td['app_id'], td['secret'])
twitch.authenticate_app([])

user_info = twitch.get_users(logins=['my_twitch_user'])
user_id = user_info['data'][0]['id']
# basic setup
hook = TwitchWebHook("https://my.cool.domain.net:8080", 'my_app_id', 8080)
hook.authenticate(twitch)
hook.start()
print('subscribing to hook:')
success, uuid = hook.subscribe_stream_changed(user_id, callback_stream_changed)
pprint(success)
pprint(twitch.get_webhook_subscriptions())
# the webhook is now running and you are subscribed to the topic you want to listen to. lets idle a bit...
input('press Enter to shut down...\n')
hook.stop()
print('done')