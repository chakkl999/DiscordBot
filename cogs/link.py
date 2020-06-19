import discord
from discord.ext import commands
from django.core.paginator import Paginator
import asyncio
import re
import sqlite3
import pathlib

class Link(commands.Cog, name="Link", command_attrs=dict(hidden=True)):
    def __init__(self, bot):
        self.bot = bot
        self.conn = sqlite3.connect("./data/data.db")
        self.cursor = self.conn.cursor()

    @commands.command(name="addlink", description="Add links to file.")
    @commands.is_owner()
    async def add_link(self, ctx, file: str = None, *, links: str = None):
        if not file:
            await ctx.send("You need to enter the file name.")
            return
        file = file.upper()
        if file not in await self.get_file():
            await ctx.send(f"There is no file named {file}")
            return
        if not links:
            await ctx.send("You need to enter the url for the images.")
            return
        removed = []
        links = re.split("\||%7C", links)
        for i in range(len(links)):
            links[i] = links[i].strip()
        p = Paginator(links, 10, allow_empty_first_page=False)

        currentPage = 1
        emotes = ["◀", "▶", "✅", "❎"]
        def check(reaction, user):
            return user == ctx.message.author and str(reaction) in emotes and reaction.message.id == message.id

        embed = discord.Embed()
        embed.add_field(name="URL", value="\n".join(p.page(currentPage).object_list))

        if p.num_pages == 1:
            message = await ctx.send(embed=embed)
            await message.add_reaction(emotes[2])
            await message.add_reaction(emotes[3])
            try:
                reaction, user = await self.bot.wait_for("reaction_add", timeout=15.0, check=check)
                await message.remove_reaction(reaction, user)
            except asyncio.TimeoutError:
                await message.clear_reactions()
                await message.add_reaction(emotes[3])
            else:
                index = emotes.index(str(reaction))
                if index == 2:
                    for link in links:
                        try:
                            self.cursor.execute("INSERT INTO links VALUES (?,?)", (file, link))
                        except sqlite3.IntegrityError:
                            removed.append(link)
                        except Exception as e:
                            embed = discord.Embed(title="Error")
                            embed.add_field(name=link, value=str(e))
                            await ctx.send(embed=embed)
                    self.conn.commit()
                    if removed:
                        await ctx.send(embed=discord.Embed(title="Links removed due to duplication:", description="\n".join(removed)))
                    await message.clear_reactions()
                    await message.add_reaction(emotes[2])
                else:
                    await message.clear_reactions()
                    await message.add_reaction(emotes[3])
            return

        embed.set_footer(text=f"Page {currentPage}/{p.num_pages}")
        message = await ctx.send(embed=embed)
        for i in range(len(emotes)):
            await message.add_reaction(emotes[i])
        while True:
            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=15.0, check=check)
                await message.remove_reaction(reaction, user)
            except asyncio.TimeoutError:
                await message.clear_reactions()
                break
            else:
                index = emotes.index(str(reaction))
                if index == 0:
                    currentPage = (currentPage - 1) % p.num_pages
                    if currentPage == 0:
                        currentPage = p.num_pages
                elif index == 1:
                    currentPage = (currentPage + 1) % p.num_pages
                    if currentPage == 0:
                        currentPage = p.num_pages
                elif index == 2:
                    for link in links:
                        try:
                            self.cursor.execute("INSERT INTO links VALUES (?,?)", (file, link))
                        except sqlite3.IntegrityError:
                            removed.append(link)
                        except Exception as e:
                            embed = discord.Embed(title="Error")
                            embed.add_field(name=link, value=str(e))
                            await ctx.send(embed=embed)
                    self.conn.commit()
                    if removed:
                        await ctx.send(embed=discord.Embed(title="Links removed due to duplication:", description="\n".join(removed)))
                    await message.clear_reactions()
                    await message.add_reaction(emotes[2])
                    break
                else:
                    await message.clear_reactions()
                    await message.add_reaction(emotes[3])
                    break
                embed.set_field_at(0, name="URL", value="\n".join(p.page(currentPage).object_list))
                embed.set_footer(text=f"Page: {currentPage}/{p.num_pages}")
                await message.edit(embed=embed)

    @commands.group(name="showlink", description="Show the links.", invoke_without_command=True)
    @commands.is_owner()
    async def show_link(self, ctx, arg: str = None):
        if ctx.invoked_subcommand is None:
            if not arg:
                await ctx.send("You need to enter the name of the file to show.")
                return
            arg = arg.upper()
            try:
                data = await self.get_link(arg)
            except sqlite3.OperationalError:
                await ctx.send(f"There is no file named {arg}")
                return
            print("\n".join([t[1] for t in data]))
            await ctx.message.add_reaction("✅")

    @show_link.command(name="all", description="Show all the links.")
    @commands.is_owner()
    async def show_link_all(self, ctx):
        try:
            data = await self.get_link("ALL")
        except sqlite3.OperationalError:
            await ctx.send(f"Oops, something's wrong.")
            return
        print("\n".join([str(t) for t in data]))
        await ctx.message.add_reaction("✅")

    @commands.command(name="showfile", description="Show the list of file.")
    @commands.is_owner()
    async def show_file(self, ctx):
        files = await self.get_file()
        await ctx.send(embed=discord.Embed(title="Files:", description="\n".join(files)))

    @commands.group(name="countlink", description="Count the number of links", invoke_without_command=True)
    @commands.is_owner()
    async def count_link(self, ctx, arg: str = None):
        if ctx.invoked_subcommand is None:
            if not arg:
                await ctx.send("You need to enter the name of the file.")
                return
            arg = arg.upper()
            if arg != "ALL":
                data = self.cursor.execute("SELECT COUNT(*) FROM links WHERE file = ?", (arg,)).fetchall()
                if not data[0][0]:
                    await ctx.send(f"There is no file named {arg}")
            await ctx.send(f"{arg} has {data[0][0]} links.")

    @count_link.command(name="all", description="Count all links.")
    @commands.is_owner()
    async def count_link_all(self, ctx):
        data = self.cursor.execute("SELECT file, COUNT(*) FROM links GROUP BY file").fetchall()
        counting = 0
        embed = discord.Embed()
        for i in data:
            embed.add_field(name=i[0], value=str(i[1]))
            counting += i[1]
        embed.add_field(name="In total, there are", value=f"{counting} links.")
        await ctx.send(embed=embed)

    @commands.command(name="removelink", description="Remove link")
    @commands.is_owner()
    async def remove_link(self, ctx, *, links: str = None):
        if not links:
            await ctx.send("You need to enter the url for the images.")
            return
        links = re.split("\||%7C", links)
        for i in range(len(links)):
            links[i] = links[i].strip()
        for link in links:
            self.cursor.execute("DELETE FROM links WHERE link = ?", (link,))
        self.conn.commit()
        await ctx.message.add_reaction("✅")

    @commands.command(name="updatelink", description="Update link")
    @commands.is_owner()
    async def update_link(self, ctx, file: str = None, oldurl: str = None, newurl: str = None):
        if not file or not oldurl or not newurl:
            await ctx.send("You're missing arguments.")
            return
        file = file.upper()
        self.cursor.execute("UPDATE links SET link = ? WHERE file = ? AND link = ?", (newurl, file, oldurl))
        self.conn.commit()
        await ctx.message.add_reaction("✅")

    @commands.group(name="linkfile", description="Output links to file.", invoke_without_command=True)
    @commands.is_owner()
    async def linkfile(self, ctx, file: str = None):
        if ctx.invoked_subcommand is None:
            if not file:
                await ctx.send("You're missing arguments.")
                return
            file = file.upper()
            data = self.cursor.execute("SELECT link from links WHERE file = ?", (file,)).fetchall()
            data = "\n".join([file[0] for file in data])
            with open(f"./links/{file}.txt", 'w+') as f:
                f.write(data)
            await ctx.message.add_reaction("✅")

    @linkfile.command(name="all", desscription="Output all links to file.")
    @commands.is_owner()
    async def linkfileall(self, ctx):
        allfile = await self.get_file()
        for file in allfile:
            data = self.cursor.execute("SELECT link from links WHERE file = ?", (file,)).fetchall()
            data = "\n".join([file[0] for file in data])
            with open(f"./links/{file}.txt", 'w+') as f:
                f.write(data)
        await ctx.message.add_reaction("✅")

    @commands.group(name="filelink", description="Take file as input.", invoke_without_command=True)
    @commands.is_owner()
    async def filelink(self, ctx, file: str = None):
        if ctx.invoked_subcommand is None:
            if not file:
                await ctx.send("You're missing arguments.")
                return
            file = file.upper()
            with pathlib.Path(f"./links/{file}.txt").open(mode='r') as f:
                links = list(map(str.strip, f.readlines()))
            for link in links:
                try:
                    self.cursor.execute("INSERT INTO links VALUES (?,?)", (file, link))
                except sqlite3.IntegrityError:
                    print(f"Error inserting {link}")
            self.conn.commit()
            await ctx.message.add_reaction("✅")

    @filelink.command(name="all", description="Take all file for links")
    @commands.is_owner()
    async def filelinkall(self, ctx):
        links = {}
        for file in pathlib.Path("links").glob("*.txt"):
            with file.open(mode="r") as f:
                links[file.stem] = list(map(str.strip, f.readlines()))
        for f, l in links.items():
            for link in l:
                try:
                    self.cursor.execute("INSERT INTO links VALUES (?,?)", (f, link))
                except sqlite3.IntegrityError:
                    print(f"Error inserting {link}")
        self.conn.commit()
        await ctx.send("Inserted.")

    def cog_unload(self):
        self.conn.commit();
        self.cursor.close();
        self.conn.close();

    async def get_random(self, file):
        self.cursor.execute("SELECT link FROM links WHERE file = ? ORDER BY RANDOM() LIMIT 1", (file,))
        data = self.cursor.fetchone()
        if data:
            return data[0]
        return "https://developers.google.com/maps/documentation/maps-static/images/error-image-generic.png"

    async def get_link(self, file):
        if file != "ALL":
            self.cursor.execute("SELECT * FROM links WHERE file = ?", (file,))
        else:
            self.cursor.execute("SELECT * FROM links")
        return self.cursor.fetchall()

    async def get_file(self):
        data = self.cursor.execute("SELECT file FROM links GROUP BY file").fetchall()
        for i in range(len(data)):
            data[i] = data[i][0]
        return data

def setup(bot):
    bot.add_cog(Link(bot))