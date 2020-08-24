import discord
from discord.ext import commands
import pathlib
import asyncio
from discord import Webhook, AsyncWebhookAdapter
import aiohttp
import re
from timeit import default_timer

class Development(commands.Cog, name="Development", command_attrs = dict(hidden=True)):
    def __init__(self, bot):
        self.bot = bot
        self.pattern = re.compile("(<:.*?:\d+>|:.*?:)")
        self.emotes = ["⏪", "◀", "▶", "⏩"]
        self.task = None

    @commands.command(name="getcogcmd")
    @commands.is_owner()
    async def cogcmd(self, ctx, arg: str):
        cog = self.bot.get_cog(arg.capitalize())
        if not cog:
            await ctx.send("Cog doesn't exist.")
            return
        commands = "\n".join([command.name if not command.parent else f"{command.parent.name} {command.name}" for command in cog.walk_commands()])
        embed = discord.Embed(title=f"Commands for {arg}", description=commands)
        await ctx.send(embed=embed)

    @commands.command(name="getallcogs")
    @commands.is_owner()
    async def getallcogs(self, ctx):
        allcogs = []
        for file in pathlib.Path("cogs").glob("*.py"):
            allcogs.append(file.name[:-3].capitalize())
        embed = discord.Embed(title="Cogs:", description="\n".join(allcogs))
        await ctx.send(embed=embed)

    @commands.command(name="cg", description="Change the game the bot is playing.")
    @commands.is_owner()
    async def change(self, ctx, *, arg: str = None):
        if not arg:
            await ctx.send("Please enter something to change the current game to.")
            return
        try:
            await self.bot.change_presence(activity=discord.Game(arg))
            await ctx.send(embed=discord.Embed(title="Success", description=f"Game acvtivity is changed to `{arg}`."))
        except Exception as e:
            await ctx.send(embed=discord.Embed(title="Error", description=str(e)))

    @commands.command(name="test")
    @commands.max_concurrency(number=1, per=commands.BucketType.guild, wait=False)
    @commands.is_owner()
    async def testfunc(self, ctx, *, arg: str):
        msg = await ctx.send("ass")
        self.task = asyncio.create_task(self.longfunc(msg))
        try:
            if self.task is not None:
                await self.task
        except asyncio.CancelledError:
            await msg.edit(content="cancelled")
            pass
        self.task = None

    @commands.command(name="testcancel")
    @commands.is_owner()
    async def cancel(self, ctx):
        if self.task is not None:
            self.task.cancel()
        self.task = None

    async def longfunc(self, msg):
        await asyncio.sleep(5)
        await msg.edit(content="bitch")
        await asyncio.sleep(5)
        await msg.edit(content="cunt")
        await asyncio.sleep(5)
        await msg.edit(content="penis")
        await asyncio.sleep(5)
        await msg.edit(content="pp")


def setup(bot):
    bot.add_cog(Development(bot))
