import discord
from discord.ext import commands
import sqlite3
from django.core.paginator import Paginator
import asyncio
import aiohttp
from io import BytesIO
import imghdr

class Customcmd(commands.Cog, name="Customcmd"):
    """Commands for creating your own custom command."""
    def __init__(self, bot):
        self.bot = bot
        self.conn = sqlite3.connect("./data/data.db")
        self.cursor = self.conn.cursor()

    @commands.group(name="ccmd", description="Onii-chan can create some custom command for me, but nothing lewd ok? ( ≧Д≦)", usage="ccmd [command name] | [content]", invoke_without_command=True)
    async def ccmd(self, ctx, *, arg: commands.clean_content):
        """To use the custom command, just use them like you would for any other command.
        Try not to create any command with the same name as any of the existing ones. You can do it but it will use that command instead of the custom one.
        You can create a maximum of 40 custom commands, just because, but I might raise or remove the limit later.
        Because the command uses | as the delimiter to separate the command and the content, you can't have | as part of the command name. If you do have multiple |, any text after the first | will be counted as part of the content. I might change it later but idk."""
        if ctx.invoked_subcommand is None:
            if self.cursor.execute("SELECT count(cmd) FROM custom_cmd WHERE server = ?", (str(ctx.guild.id),)).fetchone()[0] >= 40:
                await ctx.send("Onii-chan, you have too many custom commands already >.<")
                return
            arg = arg.split("|")
            if len(arg) < 2:
                raise commands.BadArgument
            if len(arg) > 2:
                arg[1:] = ["|".join(arg[1:])]
            if not arg[1]:
                arg[1] = "No content."
            arg = [x.strip() for x in arg]
            try:
                self.cursor.execute("INSERT INTO custom_cmd VALUES (?,?,?,?,?)", (str(ctx.guild.id), str(ctx.author.id), str(ctx.author.id), arg[0], arg[1]))
                self.conn.commit()
            except sqlite3.IntegrityError:
                await ctx.send("A custom command with the same name has already been created.")
                return
            await ctx.message.add_reaction("✅")

    @ccmd.command(name="info", description="Onii-chan can find information about a custom command.", usage="ccmd info [command name]")
    async def ccmdinfo(self, ctx, *, arg: commands.clean_content):
        """Returns information (current owner, author, content) about a custom command."""
        arg = arg.strip()
        info = self.cursor.execute("SELECT owner, author, cmd, response FROM custom_cmd WHERE server = ? AND cmd = ?", (str(ctx.guild.id), arg)).fetchone()
        if not info:
            await ctx.send("Onii-chan, that custom command doesn't exist.")
            return
        embed = discord.Embed(title=f"Information for {info[2]}")
        embed.add_field(name="Owner:", value=ctx.guild.get_member(int(info[0])) or "Unknown owner.", inline=False)
        embed.add_field(name="Author:", value=ctx.guild.get_member(int(info[1])) or "Unknown author.", inline=False)
        embed.add_field(name="Content:", value=info[3])
        await ctx.send(embed=embed)

    @ccmd.command(name="set", description="Onii-chan can edit the content of the custom commnads.", usage="ccmd set [command name] | [new content]")
    async def setccmd(self, ctx, *, arg: commands.clean_content):
        """The arguments work the same way ccmd, in that it uses | as the delimiter and anything after the first | will be counted as the content.
        Only the owner/admin can edit the command."""
        arg = arg.split("|")
        if len(arg) < 2:
            raise commands.BadArgument
        if len(arg) > 2:
            arg[1:] = ["|".join(arg[1:])]
        if not arg[1]:
            arg[1] = "No content."
        arg = [x.strip() for x in arg]
        user = self.cursor.execute("SELECT owner FROM custom_cmd WHERE server = ? AND cmd = ?", (str(ctx.guild.id), arg[0])).fetchone()
        if not user:
            await ctx.send("Onii-chan, that custom command doesn't exist.")
            return
        if user[0] == str(ctx.author.id) or ctx.author.guild_permissions.administrator or user[0] == str(self.bot.owner_id):
            self.cursor.execute("UPDATE custom_cmd SET response = ? WHERE server = ? AND cmd = ?", (arg[1], str(ctx.guild.id), arg[0]))
            self.conn.commit()
            await ctx.message.add_reaction("✅")
        else:
            await ctx.send("Onii-chan, you don't have the permission to edit this command.")

    @ccmd.command(name="del", description="Onii-chan can delete the custom command.", usage="ccmd del [command name]")
    async def delccmd(self, ctx, *, arg: commands.clean_content):
        """Delete the custom command.
        Only the owner/admin can delete the command."""
        arg = arg.strip()
        user = self.cursor.execute("SELECT owner FROM custom_cmd WHERE server = ? AND cmd = ?", (str(ctx.guild.id), arg)).fetchone()
        if not user:
            await ctx.send("Onii-chan, that custom command doesn't exist.")
            return
        if user[0] == str(ctx.author.id) or ctx.author.guild_permissions.administrator or user[0] == str(self.bot.owner_id):
            self.cursor.execute("DELETE FROM custom_cmd WHERE server = ? AND cmd = ?", (str(ctx.guild.id), arg))
            self.conn.commit()
            await ctx.message.add_reaction("✅")
        else:
            await ctx.send("Onii-chan, you don't have the permission to delete this command.")

    @ccmd.command(name="transfer", description="Onii-chan can transfer the ownership of a custom command to someone else.", usage="ccmd transfer [command name]")
    async def transferccmd(self, ctx, *, arg: commands.clean_content):
        """Transfer ownership of a custom command.
        It will ask you who to give it to and you just need to @ the user when that happens.
        Only the owner/admin can transfer ownership."""
        arg = arg.strip()
        user = self.cursor.execute("SELECT owner FROM custom_cmd WHERE server = ? AND cmd = ?",(str(ctx.guild.id), arg)).fetchone()
        if not user:
            await ctx.send("Onii-chan, that custom command doesn't exist.")
            return
        if user[0] == str(ctx.author.id) or ctx.author.guild_permissions.administrator or user[0] == str(self.bot.owner_id):
            def check(message):
                return message.author == ctx.message.author
            try:
                await ctx.send("Onii-chan, who do you want to give the command to?")
                message = await self.bot.wait_for('message', timeout=15.0, check=check)
                try:
                    user = await commands.MemberConverter().convert(ctx, message.content)
                    if user.id == ctx.author.id:
                        await ctx.send("Onii-chan, you already own this command.")
                        return
                    self.cursor.execute("UPDATE custom_cmd SET owner = ? WHERE server = ? AND cmd = ?", (str(user.id), str(ctx.guild.id), arg))
                    self.conn.commit()
                    await message.add_reaction("✅")
                except commands.BadArgument:
                    await ctx.send("Onii-chan, I can't find the user（>﹏<)")
            except asyncio.TimeoutError:
                await ctx.send("Timed out.")
        else:
            await ctx.send("Onii-chan, you don't have the permission to transfer ownership of this command.")

    @ccmd.command(name="list", description="Onii-chan can get the list of custom command in the server.", usage="ccmd list")
    async def ccmdlist(self, ctx):
        """Get the list of all the custom commands and their name and content."""
        data = self.cursor.execute("SELECT cmd, response FROM custom_cmd WHERE server = ?", (ctx.guild.id,)).fetchall()
        if data:
            data = [f"{x[0]} | {x[1]}" for x in data]
        else:
            await ctx.send("There is no custom command.")
            return
        paginator = Paginator(data, 10, allow_empty_first_page=False)
        currentPage = 1
        emotes = ["◀", "▶"]

        def check(reaction, user):
            return user == ctx.message.author and str(reaction) in emotes and reaction.message.id == message.id

        embed = discord.Embed(title=f"Custom command list for {ctx.guild.name}", description=f"Current commands: {self.cursor.execute('SELECT count(cmd) FROM custom_cmd WHERE server = ?', (str(ctx.guild.id),)).fetchone()[0]}/40")
        embed.add_field(name="Custom command:", value="\n".join(paginator.page(currentPage).object_list))
        if paginator.num_pages == 1:
            await ctx.send(embed=embed)
            return
        embed.set_footer(text=f"Page: {currentPage}/{paginator.num_pages}")
        message = await ctx.send(embed=embed)
        for emote in emotes:
            await message.add_reaction(emote)
        while True:
            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=15.0, check=check)
                await message.remove_reaction(reaction, user)
            except asyncio.TimeoutError:
                await message.clear_reactions()
                break
            else:
                if str(reaction) == emotes[0]:
                    currentPage = (currentPage - 1) % paginator.num_pages
                else:
                    currentPage = (currentPage + 1) % paginator.num_pages
                if currentPage == 0:
                    currentPage = paginator.num_pages
                embed.set_field_at(0, name="Custom command:", value="\n".join(paginator.page(currentPage).object_list))
                embed.set_footer(text=f"Page: {currentPage}/{paginator.num_pages}")
                await message.edit(embed=embed)

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            response = self.cursor.execute("SELECT response FROM custom_cmd WHERE server = ? AND cmd = ?", (ctx.guild.id, ctx.message.content[len(ctx.prefix):])).fetchone()
            if response:
                if response[0].startswith("http"):
                    async with aiohttp.ClientSession() as session:
                        try:
                            async with session.get(response[0]) as r:
                                if r.status == 200:
                                    data = await r.read()
                                else:
                                    data = None
                        except:
                            data = None
                    await session.close()
                    if data:
                        try:
                            with BytesIO(data) as b:
                                ext = imghdr.what(None, h=b)
                                if not ext:
                                    await ctx.send(response[0])
                                else:
                                    await ctx.send(file=discord.File(fp=b, filename=f"{ctx.message.content[len(ctx.prefix):]}.{ext}"))
                        except:
                            await ctx.send(response[0])
                        return
                await ctx.send(response[0])
            else:
                await ctx.send("Command does not exist.")

    def cog_unload(self):
        self.conn.commit();
        self.cursor.close();
        self.conn.close();

def setup(bot):
    bot.add_cog(Customcmd(bot))