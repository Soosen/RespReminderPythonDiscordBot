import json
import discord
import asyncio
from discord.ext import tasks
import datetime
import math
from loguru import logger

logger.add("error.log", level="ERROR")

with open('config.json') as f:
    config = json.load(f)

intents = discord.Intents.all()
intents.messages = True
intents.message_content = True
intents.members = True
intents.voice_states = True
client = discord.Client(intents=intents)


events_dict = {    
    "1h": 60,
    "3h": 180,
    "6h": 360
}

global events 
events = None


async def validate_arguments(ctx):
    args = ctx.content.split()
    
    #chec args length
    if(len(args) != 4):
        await ctx.channel.send(config["prefix"] + "start [godzina] [minuta] [sekunda]")
        return False

    #check if all args are a number
    for i in range(3):
        if(not args[i + 1].isnumeric()):
            await ctx.channel.send(config["prefix"] + "start [godzina] [minuta] [sekunda]")
            return False


    return True


async def start_routine(ctx):
    if(not await validate_arguments(ctx)):
        return

    await update_timers_list(ctx)


async def update_timers_list(ctx):
    args = ctx.content.split()

    advance_time = 5

    #clear list
    times_list_dict = {}
    visual_list_dict = {}
    for key in events_dict.keys():
        frequency = events_dict[key]
        resps_per_day = math.floor(1440 / frequency)
        #prepare embed
        for i in range(resps_per_day):
            h = (int(args[1]) + math.floor((int(args[2]) + frequency * i) / 60))% 24
            m = (int(args[2]) + math.floor(frequency * i)) % 60
            s = int(args[3])

            date = datetime.datetime(2023, 1, 1, h, m, s, 0)
            visual_list_dict[date.time()] = key

            date = date - datetime.timedelta(minutes=advance_time)

            #fix timezone
            tz_offset = -1
            date = date + datetime.timedelta(hours=tz_offset)
            times_list_dict[date.time()] = key
    
    global events
    events = times_list_dict
    update_intervals(times_list_dict)
    await print_resps_embed(ctx, visual_list_dict)


async def print_resps_embed(ctx, times_list_dict):
    desc = ""
    for key in times_list_dict.keys():
        desc += str(key)[0:8] + \
            f" === {times_list_dict[key]}\n"

    embedVar = discord.Embed(
        title="Respy", description=desc, color=0x00ff00)
    await ctx.channel.send(embed=embedVar)



def update_intervals(times_events_dict):
    times_list = []
    for key in times_events_dict.keys():
        times_list.append(key)

    remind_event.change_interval(time=times_list)
    remind_event.restart()

async def summon(ctx):
    args = ctx.content.split()
    if(len(args) != 2):
        await ctx.channel.send(config["prefix"] + "summon [1h/3h/6h]")
        return

    if(args[1] != "1h" and args[1] != "3h" and(args[1] != "6h")):
        await ctx.channel.send(config["prefix"] + "summon [1h/3h/6h]")
        return

    sound = config[f"sound_{args[1]}"]
    try:
        channel = ctx.author.voice.channel
        voice_client = await channel.connect()
        voice_client.play(discord.FFmpegPCMAudio(sound), after=lambda e: asyncio.run_coroutine_threadsafe(
            voice_client.disconnect(), client.loop))
    except Exception as e:
            logger.exception("An error occurred: %s", str(e))
            voice_client.disconnect()


async def remind():
    global events
    current_event_time = find_closest_event()
    current_event = events[current_event_time]

    channels = config["channel_ids"]
    sound = config[f"sound_{current_event}"]
    for c in channels:
        timeout = 10
        try:
            channel = client.get_channel(c)
            voice_client = await channel.connect()
            voice_client.play(discord.FFmpegPCMAudio(sound), after=lambda e: asyncio.run_coroutine_threadsafe(voice_client.disconnect(), client.loop))
            while(voice_client.is_connected()):
                await asyncio.sleep(1)
                timeout -= 1
                if(timeout <= 0):
                    voice_client.disconnect()
                    break
        except Exception as e:
            logger.exception("An error occurred: %s", str(e))
            voice_client.disconnect()

def find_closest_event():
    lowest_delta = math.inf
    global events
    now = datetime.datetime.now().time()
    for k in events.keys():
        datetime1 = datetime.datetime.combine(datetime.datetime.today(), k)
        datetime2 = datetime.datetime.combine(datetime.datetime.today(), now)
        delta = abs((datetime2 - datetime1).total_seconds())

        if(int(delta) < lowest_delta):
            lowest_delta = delta
            current_resp_timer = k

    return current_resp_timer

########################################################################################
#discord logic

@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')
    remind_event.start()



@tasks.loop()
async def remind_event():
    if(not events):
        return
    await remind()
    

@client.event
async def on_message(ctx):
    if(ctx.author.id == client.user.id):
        return

    if(ctx.channel != client.get_channel(config["text_channel_id"])):
        return

    if(not ctx.content.startswith(config["prefix"])):
        return
    
    if(ctx.content.startswith(config["prefix"] + "start")):
        await start_routine(ctx)

    if(ctx.content.startswith(config["prefix"] + "summon")):
        await summon(ctx)
        return


client.run(config["token"])

