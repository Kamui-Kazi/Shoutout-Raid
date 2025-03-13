import time 
from plyer import notification

TITLE_TEXT = 'Becky notification'
MESSAGE_TEXT='Becky is live'
NAME='BEEKY' 
ICON_PATH = "notify.ico"
TICKER = 'test'

def notify_now():
	notification.notify(
		title=TITLE_TEXT,
		message=MESSAGE_TEXT,
		app_name=NAME,
		app_icon=ICON_PATH,
  		ticker=TICKER,
		timeout=2
	)
	time.sleep(7)

notify_now()