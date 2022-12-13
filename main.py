import json
import discord
import asyncio
from discord.ext import tasks
import datetime

lock = asyncio.Lock()

with open('config.json') as f:
    config = json.load(f)


intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
client = discord.Client(intents=intents)

async def validate_arguments(ctx, command):
    args = ctx.content.split()

    #chec args length
    if(len(args) != 4):
        await ctx.channel.send(config["prefix"] + f"{command} [godzina] [minuta] [sekunda]")
        return False

    #check if all args are a number
    for i in range(3):
        if(not args[i + 1].isnumeric()):
            await ctx.channel.send(config["prefix"] + "reset [godzina] [minuta] [sekunda]")
            return False

    if(int(args[1]) < 0 or int(args[1]) > 23 or int(args[2]) < 0 or int(args[2]) > 59 or int(args[3]) < 0 or int(args[3]) > 59):
        await ctx.channel.send(config["prefix"] + f"{command} [godzina] [minuta] [sekunda]")
        return False

    return True


def create_list(resps_per_day):
    tz = datetime.timezone(datetime.timedelta(hours=1))
    time_list = []
    for i in range(resps_per_day):
        time_list.append(datetime.time(hour=i * int(24 / resps_per_day) % 24, minute=55, second=00, microsecond=0, tzinfo=tz))
    return time_list


async def kwiatki_routine(ctx):
    if(not await validate_arguments(ctx, "kwiatki")):
        return

    await update_timers_list(ctx, remind_flowers_resps, "Kwiatki", 24, 0xca15b9)


async def bossy_routine(ctx):
    if(not await validate_arguments(ctx, "reset")):
        return

    await update_timers_list(ctx, remind_boss_resps, "Respy", 8, 0x00ff00)


async def update_timers_list(ctx, func, title, resps_per_day, color):
    tz = datetime.timezone(datetime.timedelta(hours=1))
    args = ctx.content.split()

    #clear list
    time_list = []
    diff = int(24 / resps_per_day)
    #prepare embed
    desc = ""
    for i in range(resps_per_day):
        desc += str(datetime.time(hour=(int(args[1]) + i * diff) % 24, minute=int(
            args[2]), second=int(args[3]), microsecond=0, tzinfo=tz))[0:8] + "\n"

    #shift 5 minutes earlier
    if(int(args[2]) < 5):
        args[2] = str((int(args[2]) - 5) % 60)
        args[1] = str((int(args[1]) - 1) % 24)
    else:
        args[2] = str(int(args[2]) - 5)

    #append new times to the list
    for i in range(resps_per_day):
        time_list.append(datetime.time(hour=(int(args[1]) + i * diff) % 24, minute=int(
            args[2]), second=int(args[3]), microsecond=0, tzinfo=tz))

    #update play_alert loop list
    func.change_interval(time=time_list)
    func.restart()

    #send embed
    embedVar = discord.Embed(
        title=title, description=desc, color=color)
    await ctx.channel.send(embed=embedVar)

async def remind(channels, sound):
    for c in channels:
        channel = client.get_channel(c)
        voice_client = await channel.connect()
        voice_client.play(discord.FFmpegPCMAudio(sound), after=lambda e: asyncio.run_coroutine_threadsafe(voice_client.disconnect(), client.loop))
        while(voice_client.is_connected()):
            await asyncio.sleep(1)


boss_list = create_list(8)
flowers_list = create_list(24)



########################################################################################
#discord logic

@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')
    remind_boss_resps.start()
    remind_flowers_resps.start()



@tasks.loop(time=boss_list)
async def remind_boss_resps():
    await lock.acquire()
    await remind(config["bosses_voice_channel_ids"], config["sound_bosses"])
    lock.release()
    

@tasks.loop(time=boss_list)
async def remind_flowers_resps():
    await lock.acquire()
    await remind(config["flowers_voice_channel_ids"], config["sound_flowers"])
    lock.release()

@client.event
async def on_message(ctx):
    if(ctx.author.id == client.user.id):
        return

    if(ctx.channel != client.get_channel(config["text_channel_id"])):
        return

    if(not ctx.content.startswith(config["prefix"])):
        return
    
    if(ctx.content.startswith(config["prefix"] + "bossy")):
        #do reset routine
        await bossy_routine(ctx)

    if(ctx.content.startswith(config["prefix"] + "kwiatki")):
        #do kwiatki routine
        await kwiatki_routine(ctx)


client.run(config["token"])

