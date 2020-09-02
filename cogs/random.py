import discord
from discord.ext import commands
from django.core.paginator import Paginator
import asyncio
import random

class Random(commands.Cog, name="Random"):
    """Contains commands that give you random pictures."""
    def __init__(self, bot, session):
        self.bot = bot
        self.dog_breed = {}
        self.emotes = ["⏪", "◀", "▶", "⏩"]
        self.session = session

    async def get_breed_list(self):
        async with self.session.get(url="https://dog.ceo/api/breeds/list/all") as r:
            data = await r.json()
        dog_breed_list = data["message"]
        for breed in dog_breed_list:
            self.dog_breed[breed] = breed
            for subbreed in dog_breed_list[breed]:
                self.dog_breed[f"{subbreed} {breed}"] = f"{breed}/{subbreed}"

    @commands.command(name="doglist", description="Onii-chan, there's so many different dog breeds.", usage="doglist")
    async def doglist(self, ctx):
        """Gives the whole dog breed list that the command has."""
        if not self.dog_breed:
            await self.get_breed_list()
        p = Paginator(list(self.dog_breed.keys()), 15, allow_empty_first_page=False)
        currentPage = 1
        embed = discord.Embed(color=discord.Color.red())
        embed.add_field(name="Breed", value="\n".join(p.page(currentPage).object_list))
        embed.set_footer(text=f"Page {currentPage}/{p.num_pages}")
        message = await ctx.send(embed=embed)
        for emote in self.emotes:
            await message.add_reaction(emote)
        def check(reaction, user):
            return user == ctx.message.author and str(reaction) in self.emotes and reaction.message.id == message.id
        while True:
            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=15.0, check=check)
                await message.remove_reaction(reaction, user)
            except asyncio.TimeoutError:
                await message.clear_reactions()
                break
            else:
                currentPage = self.getNextPage(str(reaction), currentPage, p.num_pages)
                embed.set_field_at(0, name="Breed", value="\n".join(p.page(currentPage).object_list))
                embed.set_footer(text=f"Page: {currentPage}/{p.num_pages}")
                await message.edit(embed=embed)

    @commands.command(name="dog", description="Onii-chan, isn't this dog cute?", usage="dog *breed (optional)*")
    async def dog(self, ctx, *, breed: str = None):
        """If you don't provide a breed, it'll return a random picture from a random breed."""
        if not self.dog_breed:
            await self.get_breed_list()
        if not breed:
            async with self.session.get(url="https://dog.ceo/api/breeds/image/random") as r:
                data = await r.json()
        else:
            breed = breed.lower()
            if breed not in self.dog_breed:
                await ctx.send(f"Onii-chan, I can't find {breed}.")
                return
            async with self.session.get(url=f'https://dog.ceo/api/breed/{self.dog_breed[breed]}/images/random') as r:
                data = await r.json()
        if data["status"] != "success":
            await ctx.send("Sorry something is wrong, no dogs :(")
            return
        embed = discord.Embed(color=int("%06x" % random.randint(0, 0xffffff), 16))
        embed.set_image(url=data["message"])
        await ctx.send(embed=embed)

    @commands.command(name="birb", description="Onii-chan, this birb is cute.", usage="birb")
    async def birb(self, ctx):
        """birb"""
        async with self.session.get(url="http://random.birb.pw/tweet.json/") as r:
            data = await r.json()
        embed = discord.Embed(color=int("%06x" % random.randint(0, 0xffffff), 16))
        embed.set_image(url="https://random.birb.pw/img/" + data["file"])
        await ctx.send(embed=embed)

    @commands.command(name="cat", description="Onii-chan, this cat is really cute.", usage="cat")
    async def cat(self, ctx):
        """Cute cats."""
        async with self.session.get(url='http://aws.random.cat/meow') as r:
            data = await r.json()
        embed = discord.Embed(color=int("%06x" % random.randint(0, 0xffffff), 16))
        embed.set_image(url=data["file"])
        await ctx.send(embed=embed)

    async def getNextPage(self, reaction: str, current: int, max_page: int):
        if reaction == "⏪":
            return 1
        elif reaction == "◀":
            current = (current - 1) % max_page
        elif reaction == "▶":
            current = (current + 1) % max_page
        else:
            return max_page
        if not current:
            return max_page
        return current

def setup(bot, **kwargs):
    bot.add_cog(Random(bot, kwargs.get("session")))