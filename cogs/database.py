import sqlite3
from discord.ext import commands
import asyncio

class db(commands.Cog, name="Database", command_attrs = dict(hidden=True)):
    def __init__(self, bot):
        self.bot = bot
        self.conn = sqlite3.connect("./data/data.db")
        self.cursor = self.conn.cursor()

    @commands.command(name="exec")
    @commands.is_owner()
    async def execute(self, ctx, *, arg):
        self.cursor.execute(arg)
        self.conn.commit()
        await ctx.message.add_reaction("✅")

    @commands.command(name="getdb")
    @commands.is_owner()
    async def get_db(self, ctx, *, arg: str):
        data = self.cursor.execute(arg)
        paginator = commands.Paginator(max_size=1990)
        for x in data:
            paginator.add_line(str(x))

        if len(paginator.pages) == 1:
            await ctx.send(paginator.pages[0])
            return

        def check(reaction, user):
            return user == ctx.message.author and str(reaction) in emotes and reaction.message.id == message.id

        currentIndex = 0
        emotes = ["◀", "▶"]
        pages = f"Page {currentIndex+1}/{len(paginator.pages)}"
        message = await ctx.send(f"{paginator.pages}\n{pages}")
        for i in range(len(emotes)):
            await message.add_reaction(emotes[i])
        while True:
            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
                await message.remove_reaction(reaction, user)
            except asyncio.TimeoutError:
                await message.clear_reactions()
                break
            else:
                index = emotes.index(str(reaction))
                if index == 0:
                    currentIndex = (currentIndex-1) % len(paginator.pages)
                elif index == 1:
                    currentIndex = (currentIndex+1) % len(paginator.pages)
                pages = f"Page {currentIndex+1}/{len(paginator.pages)}"
                await message.edit(content=f"{paginator.pages[currentIndex]}\n{pages}")

    def cog_unload(self):
        self.conn.commit();
        self.cursor.close();
        self.conn.close();

def setup(bot):
    bot.add_cog(db(bot))