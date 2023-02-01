import json
import requests
import asyncio
from discord.utils import get
from datetime import datetime
import time

class Youtuber:
    def __init__(self, nickname, channel_ID):
        self.nickname = nickname
        self.channel_ID = channel_ID

async def main_routine(client):
    youtubers = load_youtubers_from_json()
    api_key = load_api_key(1)
    while(True):
        print(f"[{str(datetime.now())[:-7]}] Last streaming check")
        members = client.get_all_members()
        for m in members:
            for y in youtubers:
                if(y.nickname == m.display_name or "🔴[LIVE] " + y.nickname == m.display_name):
                    await change_discord_name(y, api_key, m)
        await asyncio.sleep(600)

def load_youtubers_from_json():
    with open("youtubers.json", "r") as f:
        data = json.load(f)
    return [Youtuber(y["nickname"], y["channel_ID"]) for y in data]

def load_api_key(id):
    with open('api.json') as f:
        return json.load(f)[f"api_key{id}"]

def is_streaming(youtuber, api_key):
    try:
        url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&channelId={youtuber.channel_ID}&type=video&eventType=live&key={api_key}"
        response = requests.get(url)
        data = response.json()
        if("quotaExceeded" in str(data)):
            print("Daily limit of youtube api requests exceded")
            return False
        
        if 'items' in data and len(data['items']) > 0:
            return True
        else:
            return False
    except Exception as e:
        print(f"An error occured: {e}")
        return False

async def change_discord_name(youtuber, api_key, member):
    if(member.display_name == youtuber.nickname and is_streaming(youtuber, api_key)):
        await member.edit(nick="🔴[LIVE] " + youtuber.nickname)
        print(f"Youtuber {youtuber.nickname} started streaming")
    elif(member.display_name == "🔴[LIVE] " + youtuber.nickname and not is_streaming(youtuber, api_key)):
        await member.edit(nick=youtuber.nickname)
        print(f"Youtuber {youtuber.nickname} stopped streaming")
    

