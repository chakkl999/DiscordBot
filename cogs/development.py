import discord
from discord.ext import commands
import os
import asyncio

class Development(commands.Cog, name="Development", command_attrs = dict(hidden=True)):
    def __init__(self, bot):
        self.bot = bot

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
        for filename in os.listdir('./cogs'):
            if filename.endswith(".py"):
                allcogs.append(filename[:-3].capitalize())
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
    async def testfunc(self, ctx, *, arg: int):
        # embed = discord.Embed(color=int("%06x" % random.randint(0, 0xffffff), 16))
        await ctx.send(arg)

def setup(bot):
    bot.add_cog(Development(bot))
