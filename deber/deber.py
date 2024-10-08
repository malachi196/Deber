import discord
from discord import app_commands
from discord.ext import commands
from discord.ext.commands.context import Context
from discord import interactions
from dotenv import load_dotenv
from _deberlive import keep_alive
#class masworld has complex toml parsing for accesing str as a discord channel that you can use <channel>.send() on :)
from _serverside import masworld, emoji, toml_struct #backend server stuff
import os
import json
import asyncio #for debugging offline
from aiohttp.client_exceptions import ClientConnectorSSLError, ClientConnectionError
from rich import print as rprint
from time import sleep
from typing import Literal


#https://discordpy.readthedocs.io/en/stable/api.html use this for the documation


datafile = json.load(open(r"./data/datafile.json"))
userfile = open(r"./data/users.txt").read()

def update_data():
    global datafile
    datafile = json.load(open(r"./data/datafile.json"))

def dprint(msg, color:Literal["blue", "yellow","red","purple"]="blue"):
    """deber logging (with color)
    Ex. output: `Deber:    bla bla bla` 
    \ncolorkey: blue for info, yellow for warning, red for error, purple for user proticols"""
    rprint(f"[{color}]Deber[/{color}]:    {msg}")

bot = commands.AutoShardedBot(command_prefix="$", intents=discord.Intents.all())
masworld.set_bot(bot_instance=bot)
    
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
    try:
        synced = await bot.tree.sync()
        s = "s"
        if len(synced) == 1:
            s = ""
        dprint(f"synced {len(synced)} command{s}")
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
        if bot.user.mentioned_in(message):
            await message.channel.send(f":)")
        await bot.process_commands(message)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send(f"the command you issued appears to be invalid {emoji.thunking}")

@bot.command("reload_data") #reload datafile vars
async def reload_data(ctx: Context):
    update_data()
    await ctx.send("`datafile` vars reloaded successfully")


@bot.command("strike") # give a player 1 strike
async def strike(ctx: Context, user):
    update_data()
    if user not in [user.strip() for user in datafile["users"]]:
        dprint("`strike` was requested on an invalid user", color="red")
        await ctx.send(f"`@{user}` is not on the userlist :warning:!\ntry running `builduserfile` to scrape users,\nand `rebuildmeta` to register new users")
    else:
        try:
            datafile["users"][user]["strikes"] = datafile["users"][user]["strikes"] + 1 #message strikes
            with open(r"./data/datafile.json", "w") as file:
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
async def strike_count(ctx: Context, user: discord.Member):
    update_data()
    if user not in [user.strip() for user in datafile["users"]]:
        dprint("'strike_count' was requested on an invalid user", "red")
        await ctx.send(f"`{user.mention}` is not on the userlist :warning:!\ntry running `builduserfile` to scrape users,\nand `rebuildmeta` to register new users")
    else:
        try:
            userstrikecount = datafile["users"][user]["strikes"]
            s = "s"
            if userstrikecount == 1:
                s = ""
            await ctx.send(f"`{user}` has {userstrikecount} strike{s}")
        except Exception as e:
            print(f"ERROR: {e}")


@bot.command("builduserfile") #scrape users from server
async def builderuserfile(ctx: Context):
    memcount = 0
    for member in ctx.guild.members:
        with open(r"./data/users.txt", "a+") as file:
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
    """register new users onto datafile"""
    with open(r"./data/users.txt", "r") as file:
        for name in file.readlines():
            name=name.strip()
            if str(name) in [user.strip() for user in datafile["users"]]:
                continue
            else:
                datafile["users"][name] = {"username":"", "realname":"", "nickname":"", "strikes":0}
        with open(r"./data/datafile.json", "w") as file:
            json.dump(datafile, file, indent=4)
        sleep(0.2)
        update_data()
    dprint("datafile was rebuilt successfully")
    await ctx.send("datafile was rebuilt successfully")

@bot.command("testfunc") #testing stuff
async def testfunc(ctx: Context):
    await ctx.send(masworld.serverstuff["name"])

@bot.tree.command(name="online") # list online players
async def online(interaction:discord.Interaction):
    try:
        minecraft_chat = masworld().admin["console"]
        await minecraft_chat.send("online")
    except Exception as e:
        await interaction.response.send_message("an error occured with `/online` :sob:")
        dprint(f"{e.with_traceback()}", color="red")

@bot.command("deber")
async def deberconsole(ctx: Context, *args): #console for deber commands (ie. restart, shutdown, etc.)
    if args[0] == "restart":
        await ctx.send(f"restart was called")
    elif args[0] == "shutdown":
        await ctx.send(f"shutdown was called")
    else:
        await ctx.send(f"invalid command parameter `{args[0]}` {emoji.thunking}")

if __name__ == "__main__":
    keep_alive() 
    load_dotenv()
    TOKEN = os.getenv("TOKEN")
    try:
        bot.run(TOKEN)
    except ClientConnectorSSLError:
        rprint("[yellow]WARNING[/yellow]:  discord is blocked on this network")
    except ClientConnectionError:
        rprint("[yellow]WARNING[/yellow]:  no network connection")