import json
import discord
import asyncio
from discord.ext import tasks
import datetime

with open('config.json') as f:
    config = json.load(f)


intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
client = discord.Client(intents=intents)

async def validate_arguments(ctx):
    args = ctx.content.split()

    #chec args length
    if(len(args) != 4):
        await ctx.channel.send("!reset [godzina] [minuta] [sekunda]")
        return False

    #check if all args are a number
    for i in range(3):
        if(not args[i + 1].isnumeric()):
            await ctx.channel.send(config["prefix"] + "reset [godzina] [minuta] [sekunda]")
            return False

    if(int(args[1]) < 0 or int(args[1]) > 23 or int(args[2]) < 0 or int(args[2]) > 59 or int(args[3]) < 0 or int(args[3]) > 59):
        await ctx.channel.send("!reset [godzina] [minuta] [sekunda]")
        return False

    return True

def create_times_list():
    tz = datetime.timezone(datetime.timedelta(hours=1))
    time_list = []
    for i in range(8):
        time_list.append(datetime.time(hour= i * 2 % 24, minute=55, second=00, microsecond=0, tzinfo=tz))
    return time_list


time_list = create_times_list()


########################################################################################
#discord logic

@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')
    await play_alert.start()

@tasks.loop(time=time_list)
async def play_alert():
    channel_ids = config["voice_channel_ids"]
    for c in channel_ids:
        channel = client.get_channel(c)
        voice_client = await channel.connect()
        voice_client.play(discord.FFmpegPCMAudio("timetoduel.mp3"), after = lambda e: asyncio.run_coroutine_threadsafe(voice_client.disconnect(), client.loop))
        while(voice_client.is_connected()):
            await asyncio.sleep(1)

@client.event
async def on_message(ctx):
    if(ctx.author.id == client.user.id):
        return

    if(ctx.channel != client.get_channel(config["text_channel_id"])):
        return

    if(not ctx.content.startswith(config["prefix"])):
        return
    
    if(ctx.content.startswith(config["prefix"] + "reset")):
        #do reset routine
        if(await validate_arguments(ctx)):
            tz = datetime.timezone(datetime.timedelta(hours=1))
            args = ctx.content.split()

            #clear list
            time_list = []

            #prepare embed
            desc = ""
            for i in range(8):
                desc += str(datetime.time(hour=(int(args[1]) + i * 3) % 24, minute=int(args[2]), second=int(args[3]), microsecond=0, tzinfo=tz))[0:8] + "\n"

            #shift 5 minutes earlier
            if(int(args[2]) < 5):
                args[2] = str((int(args[2]) - 5) % 60)
                args[1] = str((int(args[1]) - 1) % 24)
            else:
                args[2] = str(int(args[2]) - 5)

            #append new times to the list
            for i in range(8):
                time_list.append(datetime.time(hour=(int(args[1]) + i * 3) % 24, minute=int(args[2]), second=int(args[3]), microsecond=0, tzinfo=tz))
            
            #update play_alert loop list
            play_alert.change_interval(time=time_list)
            play_alert.restart()

            #send embed
            embedVar = discord.Embed(title="Respy", description=desc, color=0x00ff00)
            await ctx.channel.send(embed=embedVar)


client.run(config["token"])

