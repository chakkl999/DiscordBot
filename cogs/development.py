import discord
from discord.ext import commands
import pathlib
import asyncio
from discord import Webhook, AsyncWebhookAdapter
import aiohttp
import re
from timeit import default_timer
from inspect import getsource

class Development(commands.Cog, name="Development", command_attrs = dict(hidden=True)):
    def __init__(self, bot):
        self.bot = bot
        self.pattern = re.compile("(<:.*?:\d+>|:.*?:)")
        self.emotes = ["⏪", "◀", "▶", "⏩"]
        self.task = None
        self.config = bot.getConfig()

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

    @commands.command(name="getcommdef")
    @commands.is_owner()
    async def getcommdef(self, ctx, comm: str = None):
        if not comm:
            comm = "getcommdef"
        comm = self.bot.get_command(comm)
        if not comm:
            await ctx.send("Command not found.")
            return
        i = getsource(comm.callback).split("\n")
        line = ""
        pages = []
        backticks = re.compile("```")
        for sentence in i:
            if len(line) + len(sentence) >= 1990:
                pages.append(line)
                line = ""
            line += backticks.sub("'''", sentence) + "\n"
        if line:
           pages.append(line)

        if len(pages) == 1:
            await ctx.send(f"```py\n{pages[0]}```")
            return

        def check(reaction, user):
            return user == ctx.message.author and str(reaction) in emotes and reaction.message.id == message.id

        currentIndex = 0
        emotes = ["◀", "▶"]
        message = await ctx.send(f"```py\n{pages[0]}```")
        for i in range(len(emotes)):
            await message.add_reaction(emotes[i])
        while True:
            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=self.config.generic_timeout, check=check)
                await message.remove_reaction(reaction, user)
            except asyncio.TimeoutError:
                break
            else:
                index = emotes.index(str(reaction))
                if index == 0:
                    currentIndex = (currentIndex-1) % len(pages)
                elif index == 1:
                    currentIndex = (currentIndex+1) % len(pages)
                await message.edit(content=f"```py\n{pages[currentIndex]}```")
        await message.clear_reactions()

    @commands.command(name="test")
    @commands.max_concurrency(number=1, per=commands.BucketType.guild, wait=False)
    @commands.is_owner()
    async def testfunc(self, ctx, *, arg: str):
        await self.bot.get_command("reload all")(ctx)
        return
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
