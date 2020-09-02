import discord
from discord.ext import commands
import sqlite3
import pathlib
from util.config import Config
import aiohttp
import asyncio
import importlib
from discord import errors
import sys

class CustomBot(commands.Bot):

    def _load_from_module_spec(self, spec, key, **kwargs):
        lib = importlib.util.module_from_spec(spec)
        sys.modules[key] = lib
        try:
            spec.loader.exec_module(lib)
        except Exception as e:
            del sys.modules[key]
            raise errors.ExtensionFailed(key, e) from e

        try:
            setup = getattr(lib, 'setup')
        except AttributeError:
            del sys.modules[key]
            raise errors.NoEntryPointError(key)

        try:
            setup(self, **kwargs)
        except Exception as e:
            del sys.modules[key]
            self._remove_module_references(lib.__name__)
            self._call_module_finalizers(lib, key)
            raise errors.ExtensionFailed(key, e) from e
        else:
            self._BotBase__extensions[key] = lib

    def load_extension(self, name, **kwargs):
        if name in self._BotBase__extensions:
            raise errors.ExtensionAlreadyLoaded(name)

        spec = importlib.util.find_spec(name)
        if spec is None:
            raise errors.ExtensionNotFound(name)

        self._load_from_module_spec(spec, name, **kwargs)

    def reload_extension(self, name, **kwargs):
        lib = self._BotBase__extensions.get(name)
        if lib is None:
            raise errors.ExtensionNotLoaded(name)

        # get the previous module states from sys modules
        modules = {
            name: module
            for name, module in sys.modules.items()
            if commands.bot._is_submodule(lib.__name__, name)
        }

        try:
            # Unload and then load the module...
            self._remove_module_references(lib.__name__)
            self._call_module_finalizers(lib, name)
            self.load_extension(name, **kwargs)
        except Exception as e:
            # if the load failed, the remnants should have been
            # cleaned from the load_extension function call
            # so let's load it from our old compiled library.
            lib.setup(self)
            self._BotBase__extensions[name] = lib

            # revert sys.modules back to normal and raise back to caller
            sys.modules.update(modules)
            raise

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

loop = asyncio.get_event_loop()
session = loop.run_until_complete(getSession())

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

bot = CustomBot(command_prefix=get_prefix, description="Just a cute loli.")
bot.remove_command('help')
bot.owner_id = int(config.ownerid)

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
        bot.load_extension(f"cogs.{cog}", config=config, session=session)
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
            bot.reload_extension(f"cogs.{cog}", config=config, session=session)
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
            bot.reload_extension(f"cogs.{file.name[:-3]}", config=config, session=session)
        except Exception as e:
            fail[file.name[:-3]] = str(e)
    embed = discord.Embed(title="Success", description=f"All cogs have been reloaded." if not fail else "All cogs have been reloaded except")
    for cogs, error in fail.items():
        embed.add_field(name=cogs, value=error, inline=False)
    await ctx.send(embed=embed)

@bot.command(name="exit", description="Exit the bot")
@commands.is_owner()
async def quiting(ctx):
    await session.close()
    await ctx.send("Shutting down.....")
    await bot.logout()

for file in pathlib.Path("cogs").glob("*.py"):
    try:
        bot.load_extension(f"cogs.{file.name[:-3]}", config=config, session=session)
    except Exception as e:
        print(f'{file.name[:-3]} cannot be loaded. Error:{e}')
try:
    bot.run(TOKEN)
except discord.errors.LoginFailure:
    print("Incorrect token.")