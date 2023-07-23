import json
import discord
import asyncio
from discord.ext import tasks
import datetime
from is_streaming import main_routine
import math
import random

lock = asyncio.Lock()

with open('config.json') as f:
    config = json.load(f)

intents = discord.Intents.all()
intents.messages = True
intents.message_content = True
intents.members = True
intents.voice_states = True
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


async def kwiatki_routine(ctx):
    if(not await validate_arguments(ctx, "kwiatki")):
        return

    await update_timers_list(ctx, remind_flowers_resps, "Kwiatki", 60, 0xca15b9, 5)


async def bossy_routine(ctx):
    if(not await validate_arguments(ctx, "bossy")):
        return

    await update_timers_list(ctx, remind_boss_resps, "Respy", 180, 0x00ff00, 10)


async def mrok_routine(ctx):
    if(not await validate_arguments(ctx, "mrok")):
        return

    await update_timers_list(ctx, remind_mrok_resps, "Mrok", 30, 0x380A2E, 2)


async def update_timers_list(ctx, func, title, frequency, color, advance_time):
    args = ctx.content.split()

    #clear list
    time_list = []
    resps_per_day = math.floor(1440 / frequency)
    #prepare embed
    desc = ""
    for i in range(resps_per_day):
        h = (int(args[1]) + math.floor((int(args[2]) + frequency * i) / 60))% 24
        m = (int(args[2]) + math.floor(frequency * i)) % 60
        s = int(args[3])

        date = datetime.datetime(2023, 1, 1, h, m, s, 0)
        time = date.time()
        desc += str(time)[0:8] + "\n"

        date = date - datetime.timedelta(minutes=advance_time)

        #fix timezone
        tz_offset = -2
        date = date + datetime.timedelta(hours=tz_offset)
        time_list.append(date.time())

    #update play_alert loop list
    func.change_interval(time=time_list)
    func.restart()

    #send embed
    embedVar = discord.Embed(
        title=title, description=desc, color=color)
    await ctx.channel.send(embed=embedVar)


async def remind(channels, sound):
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
        except:
            voice_client.disconnect()

async def move_all(ctx):
    args = ctx.content.split()
    if(len(args) < 1 or len(args) > 2):
        await ctx.channel.send(config["prefix"] + "moveall [source_channel_name]")

    target_channel = ctx.author.voice.channel
    if(not target_channel):
        await ctx.channel.send("You must be connected to a voice channel")

    for member in ctx.guild.members:
        if(member == ctx.author):
            continue
        if(member.voice):
            members_vc = member.voice.channel
            if(len(args) == 1 or args[1] in members_vc.name):
                if(members_vc != ctx.guild.afk_channel):
                    await member.move_to(target_channel)

async def list_all_voice_channels(guild):
    voice_channels = []
    all_channels = guild.channels
    for c in all_channels:
        if(str(c.type) == "voice" and c != guild.afk_channel):
            voice_channels.append(c)

    return voice_channels


async def find_member_by_nickname(nickname, guild):
    for member in guild.members:
        if member.name.lower() == nickname.lower() or member.display_name.lower() == nickname.lower():
            return member
    return None

async def shake(ctx):
    if(not isModerator(ctx.author)):
        await ctx.channel.send("You have no permision to use the command")
        return
     
    args = ctx.content.split()
    if(len(args) != 3 or not args[2].isnumeric()):
        await ctx.channel.send(config["prefix"] + "shake [nick] [amount]")
        return

    voice_channels = await list_all_voice_channels(ctx.guild)
    nickname = args[1]
    amount = int(args[2])

    victim = await find_member_by_nickname(nickname, ctx.guild)
    if(not victim):
        await ctx.channel.send(f"Did not find {nickname}")
        return
    
    last_r = -1
    for i in range(amount):
        while(True):
            r = random.randint(0, len(voice_channels) - 1)
            if(r != last_r):
                last_r = r
                break

        try:
            await victim.move_to(voice_channels[r])
        except:
            continue



async def roulette(ctx):
    if(not isModerator(ctx.author)):
        await ctx.channel.send("You have no permision to use the command")
        return
    
    args = ctx.content.split()
    if(len(args) == 1):
        winners = 1
    elif(len(args) == 2 and args[1].isnumeric()):
        winners = int(args[1])
    else:
        await ctx.channel.send(f"{config['prefix']}roulette [winners_amount]")
        return
    
    if(not ctx.author.voice):
        await ctx.channel.send("You must be connected to a voice channel")
        return
    
    members_in_channel = []
    for member in ctx.guild.members:
        if(member.voice and member.voice.channel == ctx.author.voice.channel):
            members_in_channel.append(member)

    while(len(members_in_channel) > winners):
        r = random.randint(0, len(members_in_channel) - 1)
        victim = members_in_channel[r]
        await victim.move_to(None)
    

def isModerator(member):
    return(discord.utils.get(member.roles, id=config["moderatorID"]))




boss_list = [datetime.time(hour = 0, minute = 0, second=  0)]
flowers_list = [datetime.time(hour = 0, minute = 0, second=  0)]
mrok_list = [datetime.time(hour=0, minute=0, second=0)]

########################################################################################
#discord logic

@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')
    remind_boss_resps.start()
    #remind_flowers_resps.start()
    remind_mrok_resps.start()

    try:
        task = asyncio.create_task(main_routine(client))
    except:
        pass



@tasks.loop(time=boss_list)
async def remind_boss_resps():
    #await lock.acquire()
    await remind(config["bosses_voice_channel_ids"], config["sound_bosses"])
    #lock.release()
    

@tasks.loop(time=flowers_list)
async def remind_flowers_resps():
    await lock.acquire()
    await remind(config["flowers_voice_channel_ids"], config["sound_flowers"])
    lock.release()


@tasks.loop(time=mrok_list)
async def remind_mrok_resps():
    await lock.acquire()
    await remind(config["mrok_voice_channel_ids"], config["sound_mrok"])
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
    
    if(ctx.content.startswith(config["prefix"] + "mrok")):
        #do mrok routine
        await mrok_routine(ctx)

    if(ctx.content.startswith(config["prefix"] + "summon")):
        args = ctx.content.split()
        if(len(args) != 2 or (args[1] != "mrok" and args[1] != "bossy")):
            await ctx.channel.send(f"{args[0]} bossy/mrok")
            return
        
        if(args[1] == "bossy"):
            await remind(config["bosses_voice_channel_ids"], config["sound_bosses"])
        else:
            await remind(config["mrok_voice_channel_ids"], config["sound_mrok"])

    if(ctx.content.startswith(config["prefix"] + "moveall")):
        await move_all(ctx)

    if(ctx.content.startswith(config["prefix"] + "shake")):
        await shake(ctx)

    if(ctx.content.startswith(config["prefix"] + "roulette")):
        await roulette(ctx)



client.run(config["token"])

