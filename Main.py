import discord
from discord.ext import commands
import os
import sqlite3
import pathlib
from util.config import Config

async def get_prefix(bot, message):
    current_prefix = cur.execute("SELECT prefix FROM prefixes WHERE server = ?", (message.guild.id,)).fetchone()
    if current_prefix:
        current_prefix = current_prefix[0]
    else:
        current_prefix = default_prefix
    return commands.when_mentioned_or(current_prefix)(bot, message)

pathlib.Path("./data").mkdir(parents=True, exist_ok=True)
pathlib.Path("./data/data.db").touch(exist_ok=True)
con = sqlite3.connect("./data/data.db")
cur = con.cursor()

config = Config("config.ini")
config.read()
if not config.successful:
    print("Error reading config.ini.\nPlease make sure the file exists and follows the structure shown in https://docs.python.org/3/library/configparser.html#supported-ini-file-structure")
    exit(0)

TOKEN = config.token
default_prefix = config.prefix
if default_prefix[-1].isalnum():
    default_prefix += " "

bot = commands.Bot(command_prefix=get_prefix, description="Just a cute loli.")
bot.remove_command('help')
bot.owner_id = int(config.ownerid)

@bot.event
async def on_ready():
    print('-------------')
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('-------------')
    await bot.change_presence(activity=discord.Game("with onii-chan"))

@bot.event
async def on_message(message):
    if not message.author.bot and not message.guild:
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
    for filename in os.listdir('./cogs'):
        if filename.endswith(".py"):
            try:
                bot.reload_extension(f"cogs.{filename[:-3]}")
            except Exception as e:
                fail[filename[:-3]] = str(e)
    embed = discord.Embed(title="Success", description=f"All cogs have been reloaded." if not fail else "All cogs have been reloaded except")
    for cogs, error in fail.items():
        embed.add_field(name=cogs, value=error, inline=False)
    await ctx.send(embed=embed)

@bot.command(name="exit", description="Exit the bot")
@commands.is_owner()
async def quiting(ctx):
    await ctx.send("Shutting down.....")
    await bot.logout()

for filename in os.listdir('./cogs'):
    if filename.endswith(".py"):
        try:
            bot.load_extension(f"cogs.{filename[:-3]}")
        except Exception as e:
            print(f'{filename[:-3]} cannot be loaded. Error:{e}')
try:
    bot.run(TOKEN)
except discord.errors.LoginFailure:
    print("Incorrect token.")