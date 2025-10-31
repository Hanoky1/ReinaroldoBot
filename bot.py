import requests
import os
from dotenv import load_dotenv

load_dotenv(".env")

def updates():
  updates = requests.get(f"https://api.telegram.org/bot{os.getenv('TELEGRAM_TOKEN')}/getUpdates?offset=-1")
  updates = updates.json()
  last_update = updates["result"][0]
  if last_update:
    last_date = last_update["message"]["date"]
  return last_update["message"]["chat"]["id"], last_update["message"]["text"], last_date

last_date = 0
while True:
  try:
    upd = updates()
    if upd[2] > last_date:
      id = upd[0]
      text = eval(upd[1])
      last_date = upd[2]
      requests.post(
            url=f"https://api.telegram.org/bot{os.getenv('TELEGRAM_TOKEN')}/sendMessage",
            data={"chat_id": id, "text": text}
        ).json() 
  except:
    pass