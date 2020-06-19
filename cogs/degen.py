import discord
from discord.ext import commands
import typing

class Degen(commands.Cog, name="Degen"):
    """Contains all the degen commands you'll need."""
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="lick", description="Onii-chan licking someone... hentai! (⸝⸝⸝ ≧ㅿ＼⸝⸝⸝)/", usage="lick [@mention (optional)]")
    async def lick(self, ctx, *, mention: typing.Optional[commands.MemberConverter] = None):
        """If you don't mention anyone, it'll default to the bot. Can't have @everyone or @role."""
        link = self.bot.get_cog("Link")
        if mention:
            if mention == self.bot.user:
                embed = discord.Embed(color=0xffffff)
                embed.set_image(url="https://cdn.discordapp.com/attachments/532819712409600000/656715400628928512/007.jpg")
            else:
                embed = discord.Embed(
                    description=f"{ctx.author.mention} is giving {mention.mention} a lick. (／≧ω＼)"
                    if mention != ctx.message.author else f"Onii-chan is licking himself...?",
                    color=0xffffff)
                embed.add_field(name="I'm too lazy", value="Still gathering images which will probably never happen.")
        else:
            if ctx.message.mention_everyone or ctx.message.role_mentions:
                raise commands.BadArgument
            embed = discord.Embed(color=0xffffff)
            embed.set_image(url=await link.get_link("LICK"))
        await ctx.send(embed=embed)

    @commands.command(name="pat", description="Onii-chan can headpat someone but I would rather onii-chan to give me a headpat, is it ok...?", usage="pat [@mention (optional)].")
    async def pat(self, ctx, *, mention: typing.Optional[commands.MemberConverter] = None):
        """If you don't mention anyone, it'll default to the bot. Can't have @everyone or @role."""
        await ctx.send("Under construction for images.")
        return
        link = self.bot.get_cog("Link")
        if mention:
            if mention == self.bot.user:
                embed = discord.Embed(color=0xffffff)
                # embed.set_image(url=links.PATBOT)
                embed.add_field(name="I'm too lazy", value="To get an image specifically for this.")
            else:
                embed = discord.Embed(
                    description=f"{ctx.author.mention} is giving {mention.mention} a headpat."
                    if mention != ctx.message.author else f"Onii-chan is patting himself...?",
                    color=0xffffff)
                embed.set_image(url=await link.get_link("PAT"))
        else:
            if ctx.message.mention_everyone or ctx.message.role_mentions:
                raise commands.BadArgument
            embed = discord.Embed(color=0xffffff)
            # embed.set_image(url=links.PATBOT)
            embed.add_field(name="I'm too lazy", value="To get an image specifically for this.")
        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(Degen(bot))