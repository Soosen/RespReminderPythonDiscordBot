import json
import requests
import asyncio
from discord.utils import get
from datetime import datetime

class Youtuber:
    def __init__(self, nickname, channel_ID):
        self.nickname = nickname
        self.channel_ID = channel_ID

async def main_routine(client, api_key):
    youtubers = load_youtubers_from_json()
    members = client.get_all_members()
    while(True):
        for m in members:
            for y in youtubers:
                if(y.nickname == m.display_name or "🔴[LIVE]" + y.nickname == m.display_name):
                    await change_discord_name(y, api_key, m)
        await asyncio.sleep(60)
        print(f"[{str(datetime.now())[:-7]}] Last streaming check")

def load_youtubers_from_json():
    with open("youtubers.json", "r") as f:
        data = json.load(f)
    return [Youtuber(y["nickname"], y["channel_ID"]) for y in data]

def is_streaming(youtuber, api_key):
    try:
        url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&channelId={youtuber.channel_ID}&type=video&eventType=live&key={api_key}"
        response = requests.get(url)
        data = response.json()
        
        if 'items' in data and len(data['items']) > 0:
            return True
        else:
            return False
    except Exception as e:
        print(f"An error occured: {e}")
        return False

async def change_discord_name(youtuber, api_key, member):
    if(member.display_name == youtuber.nickname and is_streaming(youtuber, api_key)):
        await member.edit(nick="🔴[LIVE]" + youtuber.nickname)
        print(f"Youtuber {youtuber.nickname} started streaming")
    elif(member.display_name == "🔴[LIVE]" + youtuber.nickname and not is_streaming(youtuber, api_key)):
        await member.edit(nick=youtuber.nickname)
        print(f"Youtuber {youtuber.nickname} stopped streaming")
    

