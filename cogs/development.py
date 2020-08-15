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
    @commands.is_owner()
    async def testfunc(self, ctx, *, arg: str):
        print(await ctx.bot.get_prefix(ctx.message))
        return
        await ctx.message.delete()
        webhook = discord.utils.get(await ctx.channel.webhooks(), name="Emotes")
        if not webhook:
            webhook = await ctx.channel.create_webhook(name="Emotes", reason="Automatically created webhook for bot.")
        start = default_timer()
        print(arg)
        arg = self.pattern.split(arg)
        print(arg)
        for i in range(len(arg)):
            if arg[i] and arg[i][0] == ':' and arg[i][-1] == ':':
                emote = discord.utils.get(self.bot.emojis, name=arg[i][1:-1])
                if emote:
                    arg[i] = str(emote)
        arg = "".join(arg)
        print(arg)
        print(default_timer() - start)
        async with aiohttp.ClientSession() as session:
            w = Webhook.partial(webhook.id, webhook.token, adapter=AsyncWebhookAdapter(session))
            await w.send(content=arg, username=ctx.author.display_name, avatar_url=ctx.author.avatar_url)

def setup(bot):
    bot.add_cog(Development(bot))
