import time 
import notify2 

# path to notification window icon 
ICON_PATH = "./Twitch-notif/notify.png"

# initialise the d-bus connection 
notify2.init('Becky Notify') 

# create Notification object 
n = notify2.Notification(None, icon = ICON_PATH) 

# set urgency level 
n.set_urgency(notify2.URGENCY_NORMAL) 

# set timeout for a notification 
n.set_timeout(10000) 

def notify_now():
	# update notification data for Notification object 
	n.update("Beeky", "is live") 

	# show notification on screen 
	n.show() 

	# short delay between notifications 
	time.sleep(15) 

notify_now()