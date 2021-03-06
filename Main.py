import discord
from discord.ext import commands
import sqlite3
import pathlib
from util.config import Config
import aiohttp
import asyncio

class CustomBot(commands.Bot):

    def __init__(self, config, session, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config = config
        self.session = session

    async def logout(self):
        await self.session.close()
        await super().close()

    def getSession(self):
        return self.session

    def getConfig(self):
        return self.config

async def get_prefix(bot, message):
    current_prefix = cur.execute("SELECT prefix FROM prefixes WHERE server = ?", (message.guild.id,)).fetchone()
    if current_prefix:
        current_prefix = current_prefix[0]
    else:
        current_prefix = default_prefix
    return commands.when_mentioned_or(current_prefix)(bot, message)

async def getSession():
    session = aiohttp.ClientSession()
    return session

pathlib.Path("./data").mkdir(parents=True, exist_ok=True)
pathlib.Path("./data/data.db").touch(exist_ok=True)

if not pathlib.Path("config.ini").exists():
    if pathlib.Path("configTemplate.ini").exists():
        print("Config template found.\nMake sure you fill it out and rename it to config.ini.")
        exit(1)
    else:
        print("Config or config template not found.\nMake sure you have config.ini.\nYou can find a template for it in the repository.")
        exit(1)

con = sqlite3.connect("./data/data.db")
cur = con.cursor()

config = Config("config.ini")
config.read()

if not config.successful:
    print("Error reading config.ini.\nPlease make sure the file exists and follows the structure shown in https://docs.python.org/3/library/configparser.html#supported-ini-file-structure\nThere should be a template in the repo you can use.")
    exit(1)

TOKEN = config.token
default_prefix = config.prefix
if default_prefix[-1].isalnum():
    default_prefix += " "

loop = asyncio.get_event_loop()
session = loop.run_until_complete(getSession())

bot = CustomBot(config, session, command_prefix=get_prefix, description="Just a cute loli.")
bot.remove_command('help')
bot.owner_id = int(config.owner_id)

@bot.event
async def on_ready():
    print('-------------')
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('-------------')
    await bot.change_presence(activity=discord.Game(f"with onii-chan"))

@bot.event
async def on_message(message):
    if not message.author.bot and message.guild:
        await bot.process_commands(message)

@bot.command(name="load", description="Load a cog")
@commands.is_owner()
async def load(ctx, cog: str):
    cog = cog.lower()
    try:
        bot.load_extension(f"cogs.{cog}")
        embed = discord.Embed(title='Success', description=f'{cog} is loaded')
        await ctx.send(embed=embed)
    except Exception as e:
        embed = discord.Embed(title='Exception', description=f'{cog} cannot be loaded.')
        embed.add_field(name='Error:', value=str(e))
        await ctx.send(embed=embed)

@bot.command(name="unload", description="Unload a cog")
@commands.is_owner()
async def unload(ctx, cog: str):
    try:
        bot.unload_extension(f"cogs.{cog}")
        embed = discord.Embed(title='Success', description=f'{cog} is unloaded')
        await ctx.send(embed=embed)
    except Exception as e:
        embed = discord.Embed(title='Exception', description=f'{cog} cannot be unloaded.')
        embed.add_field(name='Error:', value=str(e))
        await ctx.send(embed=embed)

@bot.group(name="reload", description="Reload a cog", invoke_without_command=True)
@commands.is_owner()
async def reload(ctx, cog):
    if ctx.invoked_subcommand is None:
        try:
            bot.reload_extension(f"cogs.{cog}")
            embed = discord.Embed(title='Success', description=f'{cog} is reloaded')
        except Exception as e:
            embed = discord.Embed(title='Exception', description=f'{cog} cannot be reloaded.')
            embed.add_field(name='Error:', value=str(e))
        await ctx.send(embed=embed)

@reload.command(name="all", description="Reload all cogs.")
@commands.is_owner()
async def reload_all(ctx):
    fail = {}
    for file in pathlib.Path("cogs").glob("*.py"):
        try:
            bot.reload_extension(f"cogs.{file.name[:-3]}")
        except Exception as e:
            fail[file.name[:-3]] = str(e)
    embed = discord.Embed(title="Success", description=f"All cogs have been reloaded." if not fail else "All cogs have been reloaded except")
    for cogs, error in fail.items():
        embed.add_field(name=cogs, value=error, inline=False)
    await ctx.send(embed=embed)

@bot.command(name="reload_config", description="Reload config.")
@commands.is_owner()
async def reload_config(ctx):
    bot.config.read()
    for file in pathlib.Path("cogs").glob("*.py"):
        try:
            bot.reload_extension(f"cogs.{file.name[:-3]}")
        except Exception as e:
            pass
    await ctx.send("Config has been reloaded.")

@bot.command(name="exit", description="Exit the bot")
@commands.is_owner()
async def quiting(ctx):
    await ctx.send("Shutting down.....")
    await bot.logout()

for file in pathlib.Path("cogs").glob("*.py"):
    try:
        bot.load_extension(f"cogs.{file.name[:-3]}")
    except Exception as e:
        print(f'{file.name[:-3]} cannot be loaded. Error:{e}')
try:
    bot.run(TOKEN)
except discord.errors.LoginFailure:
    print("Incorrect token.")