import discord
from discord import app_commands
from discord.ext import commands
from discord.ext.commands.context import Context
from discord import interactions
from dotenv import load_dotenv
from _deberlive import keep_alive #web server keeps deber alive
#class masworld has complex toml parsing for accesing str as a discord channel that you can use masworld.<channel>.send() on :)
from _serverside import emoji, toml_struct, masworld #backend server stuff (see comment above)
import os
import json
import asyncio #for debugging offline and reaction tracking
from aiohttp.client_exceptions import ClientConnectorSSLError, ClientConnectionError, ClientConnectorError
from rich import print as rprint
from time import sleep
from typing import Literal
import secrets
import logging as log
import signal
import sys
import copy

#Note from 4/19/25: the original Masworld has been archived, and the "new masworld" is named Malworld (after malachi196), even though the class is still named masworld.
#Note from 9/6/25: server was renamed to Masworld again :), ignore comment above

log.basicConfig(
    filename="deber/data/sessions.log",
    level=log.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s')
session_id = secrets.token_hex(32)

#https://discordpy.readthedocs.io/en/stable/api.html use this for the documation

datafile = json.load(open(r"./deber/data/datafile.json"))
userfile = open(r"./deber/data/users.txt").read()
statiofile = json.load(open(r"./deber/backend_io/debstats.json"))

def update_data():
    global datafile
    datafile = json.load(open(r"./deber/data/datafile.json"))
  
def reload_status():
    global statiofile
    statiofile = json.load(open(r"./deber/backend_io/debstats.json"))
    
def change_status(section, newstatus):
    global statiofile
    statiofile["stats"][section] = newstatus
    with open(r"./deber/backend_io/debstats.json", "w") as file:
    	json.dump(statiofile, file, indent=4)

def dprint(msg, color:Literal["blue", "yellow","red","purple"]="blue"):
    """deber logging (with color)
    Ex. output: `Deber:    bla bla bla` 
    \ncolorkey: blue for info, yellow for warning, red for error, purple for user proticols"""
    rprint(f"[{color}]Deber[/{color}]:    {msg}")
    match color:
        case "blue":
            log.info(msg)
        case "yellow":
            log.warning(msg)
        case "red":
            
            log.error(msg)
        case "purple":
            log.info(f"USER ACTION: {msg}")

bot = commands.AutoShardedBot(command_prefix="$", intents=discord.Intents.all())
#masworld.set_bot(bot_instance=bot)
    
#>>> note: you can use the @bot.tree.command() to use '/' commands 
#>>> note: use 'ctx.author.send' to DM a command author
#>>> note: 'ctx.author.create_dm' can create a DM channel that your bot can send messages to a DMChannel

"""
class StrikeModel(discord.ui.Modal, title="Striker!"):
    userselect = discord.ui.UserSelect(label="Select user")
    options = [
        discord.SelectOption(label="1"),
        discord.SelectOption(label="2"),
        discord.SelectOption(label="3")
    ]
    discord.ui.Select(label="Strike count",options=options)
"""
    
@bot.event
async def on_ready():
    dprint("deber started")
    try:
        synced = await bot.tree.sync()
        s = "s"
        if len(synced) == 1:
            s = ""
        dprint(f"synced {len(synced)} slash command{s}")
        dprint(f"session id: {session_id}")
    except Exception as e:
        dprint(f"failed to sync commands; {e}", color="red")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return 
    if isinstance(message.channel, discord.DMChannel):
        dprint(f"deber was dm'd by {message.author}")
        await message.channel.send(f"hi @{message.author}! Im sorry, but I do not support DM ... try talking in masworld {emoji.masworldlogo}!")
    else:
        await bot.process_commands(message)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send(f"the command you issued appears to be invalid {emoji.thunking}")

@bot.command("reload_data") #reload datafile vars
async def reload_data(ctx: Context):
    update_data()
    await ctx.send("`datafile` vars reloaded successfully")

@bot.command("strike")
async def strike(ctx: Context, user):
    """give a user 1 strike (3 strikes = timout)"""
    update_data()
    if user not in [user.strip() for user in datafile["users"]]:
        dprint("`strike` was requested on an invalid user", color="red")
        await ctx.send(f"`@{user}` is not on the userlist :warning:!\ntry running `builduserfile` to scrape users,\nand `rebuildmeta` to register new users")
    else:
        try:
            datafile["users"][user]["strikes"] = datafile["users"][user]["strikes"] + 1 #message strikes
            with open(r"./deber/data/datafile.json", "w") as file:
                json.dump(datafile, file, indent=4)
            sleep(0.3)
            update_data()
            if datafile["users"][user]["strikes"] < 3:
                await ctx.send(f"`{user}` gained 1 strike;\ntotal strikes: {datafile['users'][user]['strikes']}")
                dprint(f"{user} just gained 1 strike")
            else:
                await ctx.send(f"`{user}` **has reached the max strike count**")
                dprint(f"{user} gained max strikes!",color="purple")
        except Exception as e:
            print(f"ERROR: {e.with_traceback()}")

@bot.command("strike_count") #get strikes
async def strike_count(ctx: Context, user):
    """obtain the number of strikes a user has"""
    update_data()
    if user not in [user.strip() for user in datafile["users"]]:
        dprint("'strike_count' was requested on an invalid user", "red")
        await ctx.send(f"`{user}` is not on the userlist :warning:!\ntry running `builduserfile` to scrape users,\nand `rebuildmeta` to register new users")
    else:
        try:
            userstrikecount = datafile["users"][user]["strikes"]
            s = "s"
            if userstrikecount == 1:
                s = ""
            await ctx.send(f"`{user}` has {userstrikecount} strike{s}")
        except Exception as e:
            print(f"ERROR: {e}")

@bot.command("builduserfile") #scrape users from server & dump to file
async def builderuserfile(ctx: Context):
    """scrape all of the users from discord"""
    memcount = 0
    open("deber/data/users.txt", "w").close() #truncate file contents
    for member in ctx.guild.members:
        with open(r"./deber/data/users.txt", "a+") as file:
            skipmem = False
            for line in file.readlines():
                if str(member) in str(line):
                    skipmem = True
            if skipmem:
                skipmem = False
                continue
            else:
                file.seek(0)
                file.write(str(member) + "\n")
                memcount += 1
    dprint(f"built usersfile; users found: {memcount}")
    await ctx.send(f"userfile was built with {memcount} users")

#guild: 1273393484715524238 (fetchable from datafile["server"]["guild_id"])

@bot.command("rebuildmeta") #register new users onto datafile
async def rebuildmeta(ctx: Context):
    """parses the scraped users and registers any unknown users"""
    newusercount = 0
    removed_count = 0
    with open(r"./deber/data/users.txt", "r") as file:
        try:
            for name in file.readlines():
                name=name.strip()
                if str(name) in [user.strip() for user in datafile["users"]]:
                    continue
                else:
                    newusercount += 1
                    datafile["users"][name] = {"username":"", "realname":"", "nickname":"", "strikes":0}
            datanames = dict(copy.deepcopy(datafile["users"]))
            print(datanames) #DEBUG
            for name in datanames:
                name = str(name).strip()
                flag = False
                print(f"This was called at: {name}") #DEBUG
                for currentname in file.readlines():
                    currentname = str(currentname).strip()
                    print(f"{str(name)} == {str(currentname)}?") #DEBUG
                    if str(name) == str(currentname):
                        flag = True
                        continue
                if flag == False:
                    datafile["users"].pop(name)
                    removed_count += 1
            with open(r"./deber/data/datafile.json", "w") as file:
                json.dump(datafile, file, indent=4)
            sleep(0.2)
            update_data()
        except Exception as e:
            dprint(f"FAILED TO REBUILD DATAFILE: {e}", 'red')
            await ctx.send("FAILED TO REBUILD DATAFILE!!! Check console for more info...")
            return
    dprint(f"Datafile was rebuilt successfully. Registered {newusercount} users. Removed {removed_count} users.")
    if newusercount == 0 and removed_count == 0:
        await ctx.send("userfile scanned; no new users were registered or removed")
    else:
        s = "s"
        rs = "s"
        if newusercount == 1:
            s = ""
        if removed_count == 1:
            s = ""
        await ctx.send(f"Datafile was rebuilt successfully; registered `{newusercount}` user{s}; removed `{removed_count}` user{rs}")
    newusercount = 0
    removed_count=0

@bot.command("testfunc") #testing stuff
async def testfunc(ctx: Context):
    """testing function for testing purposes"""
    modonly = bot.get_channel(int(masworld.channels.manifest["moderator_only"]))
    msg = await modonly.fetch_message("1302612302021001247")
    await ctx.send(f"```{msg}```")
    if msg.reactions:
        await ctx.send(f"reactions: true:\n{msg.reactions}")
        for reaction in msg.reactions:
            async for user in reaction.users():
                await user.send(f"hi {user.name}, thanks for reacting with {reaction.emoji}")

@bot.command("realname") #get user's realname
async def realname(ctx, name):
    """fetch a user's irl name (if registered)"""
    if name not in [name.strip() for name in datafile["users"]]:
        dprint("'realname' was requested on an invalid user", "red")
        await ctx.send(f"`{name}` is not on the userlist :warning:!\ntry running `builduserfile` to scrape users,\nand `rebuildmeta` to register new users")
        return 1
    rname = datafile['users'][name]["realname"]
    if rname == "":
        await ctx.send(f"{name} does not have his realname registered")
    else:
        await ctx.send(f"{name}'s realname is `{rname}`")

@bot.command("debermessage") #message channel in manifest
async def debermessage(ctx, category, channel):
    """used for official messages and stuff(though you may have to edit deber source code for your usage)"""
    match category:
        case "manifest":
            channelname = bot.get_channel(int(masworld.channels.manifest[str(channel)]))
        case "text_channels":
            channelname = bot.get_channel(int(masworld.channels.text_channels[str(channel)]))
        case "admin":
            channelname = bot.get_channel(int(masworld.channels.admin[str(channel)]))
        case _:
            await ctx.channel.send(f"no such category `{category}`")
    if channelname is None:
        await ctx.channel.send("channel error")
        return
    await channelname.send(str(open(r"./deber/data/deber-message-contents.txt").read()))

running = True
watch_task = None
previously_seen_r = set()
@bot.command("watch_reactions")
async def watch_reactions(ctx, channel, msgid):
    """infinitely check for either adding or removing reactions on the specified message!"""
    global watch_task
    if watch_task is not None:
        await ctx.send("a message is already being monitored")
        return
    chnl = bot.get_channel(int(masworld.channels.text_channels[str(channel)])) #change for category
    if chnl is None:
        await ctx.send("channel does not exist")
        return
    try:
        msg = await chnl.fetch_message(int(msgid))
        watch_task = asyncio.create_task(monitor_r(msg, 3))
        await ctx.send(f"now monitoring reactions on {msgid}")
    except Exception as e:
        print(e)

async def monitor_r(msg, bufferspeed):
    global running
    global previously_seen_r
    current_r = set()
    try:
        while running:
            new_r = set()
            msg = await msg.channel.fetch_message(msg.id)
            if msg.reactions:
                for reaction in msg.reactions:
                    async for user in reaction.users():
                        new_r.add((user.id, reaction.emoji))
                        if (user.id, reaction.emoji) not in previously_seen_r:
                            previously_seen_r.add((user.id, reaction.emoji))
                            if user != bot.user:
                                await user.send(f"thanks for reacting with {reaction.emoji}")
            removed_r = previously_seen_r - new_r
            for userid, emoji in removed_r:
                user = await bot.fetch_user(userid)
                await user.send(f"you removed {emoji}")
                previously_seen_r.remove((userid, emoji))
            current_r = new_r
            await asyncio.sleep(bufferspeed)
    except Exception as e:
        print(e)

@bot.command("stop_rwatch")
async def stop_r_watch(ctx):
    """stops checking for reactions on the set message (if any)"""
    global watch_task
    if watch_task:
        watch_task.cancel()
        watch_task = None
        await ctx.send("stopped watching reactions")
    else:
        await ctx.send("no messages are being watched")

@bot.command("v_watch")
async def v_watch(ctx, vc):
    pass

@bot.tree.command(name="online") # list online players
async def online(interaction:discord.Interaction):
    """lists the users who are online in masworld (used for nonadmin)"""
    try:
        minecraft_chat = bot.get_channel(masworld.channels.admin["console"])
        await minecraft_chat.send("online")
    except Exception as e:
        await interaction.response.send_message("an error occured with `/online` :sob:")
        dprint(f"{e.with_traceback()}", color="red")

consolecoms = {
"restart":"",
 "shutdown":"",
  #"stats":
} #deberconsole commands
        
@bot.command("debercon")
async def deberconsole(ctx: Context, *args): #console for deber commands (ie. restart, shutdown, etc.)
    """deber system console"""
    if args[0] in consolecoms:
        consolecoms[args[0]](ctx)
    else:
        await ctx.send(f"invalid command parameter `{args[0]}` {emoji.thunking}")

#@bot.command("deber")
#async def deber(ctx:Context, *args):

#def deberchat(request):
    

def exit_handler():
    global running
    dprint("deber successfully shutdown")
    running = False
    sleep(2)
    sys.exit(0)

if __name__ == "__main__":
    change_status("failed", False)
    change_status("offline", False)
    with open("./deber/data/sessions.log", "a") as file:
        file.write(f"-{session_id}-\n")
    signal.signal(signal.SIGINT, lambda *args: exit_handler())
    keep_alive() 
    load_dotenv()
    TOKEN = os.getenv("TOKEN")
    try:
        bot.run(TOKEN)
    except ClientConnectorSSLError:
        dprint("discord is blocked on this network", color="yellow")
        change_status("offline", True)
    except ClientConnectionError:
        dprint("no network connection", color="yellow")
        change_status("offline", True)
    except ClientConnectorError:
        dprint("network connection halted", color="yellow")
        change_status("offline", True)
    except Exception:
        change_status("failed", True)
        exit(1)

