import discord
from discord.ext import commands
import random

class Weeb(commands.Cog, name="Weeb"):
    """Weeb commands for you weebs."""
    def __init__(self, bot):
        self.bot = bot
        self.responses = ["Onii-chan, you shouldn't do anything lewd. ( >д<)",
                     "I'll give myself to onii-chan then. (⁄ ⁄•⁄ω⁄•⁄ ⁄)⁄",
                     "Onii-chan, you already have me.", "Onii-chan wants a loli? Then.... do you want me? (∗∕ ∕•∕ω∕•∕)"]

    @commands.command(name="hamm", description="Onii-chan already has me but you still want someone else... Maybe because I don't have cat ears like her... (つ﹏<。)", usage="hamm")
    async def hamm(self, ctx):
        """Cutest bote in the game, don't @ me"""
        link = self.bot.get_cog("Link")
        embed = discord.Embed(color=0xffffff)
        embed.set_image(url=await link.get_random("HAMM"))
        await ctx.send(embed=embed)

    @commands.command(name="loli", description="Gives a cute loli pic", usage="loli")
    async def give_me_a_loli(self, ctx):
        """Gives a random loli image."""
        link = self.bot.get_cog("Link")
        embed = discord.Embed(color=0xe1e1fa)
        embed.set_image(url=await link.get_random("LOLI"))
        await ctx.send(embed=embed)

    @commands.command(name="gib", description="Gives you a loli~~(it doesn't)~~", usage="gib")
    async def gives_loli(self, ctx):
        """Just a stupid command that gives a random response."""
        await ctx.send(random.choice(self.responses))

    @commands.command(name="chino", description="Chino-chan is cute", usage="chino")
    async def chino(self, ctx):
        """Chino is the best loli and you're wrong for disagreeing."""
        link = self.bot.get_cog("Link")
        embed = discord.Embed(color=0xb1c0e9)
        embed.set_image(url=await link.get_random("CHINO"))
        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(Weeb(bot))