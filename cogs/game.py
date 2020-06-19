import discord
from discord.ext import commands
import typing

class Game(commands.Cog, name="Game"):
    """Under construction."""
    def __init__(self, bot):
        self.bot = bot

def setup(bot):
    bot.add_cog(Game(bot))