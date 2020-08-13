import discord
from discord.ext import commands
import asyncio
import sqlite3
from util import customException

def is_server_owner():
    async def predicate(ctx):
        if ctx.author.id != ctx.guild.owner.id or ctx.author.id != ctx.bot.owner_id:
            raise customException.ServerOwnerOnly("Onii-chan, only server owner can use this command. (｡>口<｡)!")
        return True
    return commands.check(predicate)

class Essential(commands.Cog, name="Essential"):
    """Essential commands that you'll need."""
    def __init__(self, bot):
        self.bot = bot
        self.cogs = ["Degen", "Misc", "Essential", "Weeb", "Random", "Search", "Customcmd", "Game"]
        self.emotes = ["0⃣", "1⃣", "2⃣", "3⃣", "4⃣", "5⃣", "6⃣", "7⃣", "8⃣", "9⃣", '🗑']
        self.conn = sqlite3.connect("./data/data.db")
        self.cursor = self.conn.cursor()

    def mainMenu(self, ctx):
        prefix = ctx.prefix
        embed = discord.Embed(title="Help", description=f"Prefix = {prefix}\nUsage: {prefix}command. \nReact with :zero: to get back to this menu.\nReact with :wastebasket: to delete this message.",
                              color=discord.colour.Color.blue())
        embed.set_author(name="A cute loli",
                         icon_url='https://pbs.twimg.com/profile_images/772635480244441088/r_ANUUZ0_400x400.jpg')
        index = 1
        for cog in self.cogs:
            embed.add_field(name=f"{index}.{cog}", value=f"`{self.bot.get_cog(cog).description}`", inline=False)
            index += 1
        embed.set_footer(text=f"Onii-chan can command me to do anything you want (⌯˃̶᷄ ﹏ ˂̶᷄⌯)ﾟ. But nothing lewd ( ≧Д≦)  Use {prefix}help *command(optional)* *dm(optional)* to view the specifics.\nI made this when I was bored, stop judging me.")
        return embed

    @commands.group(name="help", description="Send you help.", usage="help [category/command (optional)]", invoke_without_command=True)
    async def help(self, ctx, *, arg: str = ""):
        """You can also get the specific category or command without going through the menu by putting the name of it after the command."""
        await ctx.message.delete()
        if ctx.invoked_subcommand is None:
            cog = await self.isCog(arg.capitalize())
            if cog:
                embed = discord.Embed(title='Category', description=f"Help for {arg.capitalize()}", color=discord.colour.Color.blue())
                for command in cog.walk_commands():
                    if not command.hidden:
                        embed.add_field(name=command.qualified_name, value=f"`{command.description}`", inline=False)
                await ctx.send(embed=embed)
                return
            arg = arg.lower()
            if arg:
                command = await self.check_command(arg)
                if command:
                    embed = discord.Embed(title='Command', description=f"Help for {command.qualified_name}", color=discord.Color.blurple())
                    embed.add_field(name=f"Usage: {ctx.prefix}{command.usage}", value=f"```\n{command.help}\n```", inline=False)
                    await ctx.send(embed=embed)
                else:
                    await ctx.send("I'm not sure there's a category with that name, onii-chan.")
                return
            msg = await ctx.send(embed=self.mainMenu(ctx))
            for i in range(len(self.cogs) + 1):
                await msg.add_reaction(self.emotes[i])
            await msg.add_reaction(self.emotes[len(self.emotes)-1])

            def check(reaction, user):
                return user == ctx.message.author and str(reaction) in self.emotes and reaction.message.id == msg.id

            while True:
                try:
                    reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
                    await msg.remove_reaction(reaction, user)
                except asyncio.TimeoutError:
                    await msg.clear_reactions()
                    break
                else:
                    index = self.emotes.index(str(reaction))
                    if index <= 0:
                        await msg.edit(embed=self.mainMenu(ctx))
                    elif index == len(self.emotes) - 1:
                        await msg.clear_reactions()
                        await msg.delete()
                        break
                    else:
                        embed = discord.Embed(title=self.cogs[index-1], description=f"Help for {self.cogs[index-1]}", color=discord.colour.Color.blue())
                        for command in self.bot.get_cog(self.cogs[index-1]).walk_commands():
                            if not command.hidden:
                                embed.add_field(name=command.qualified_name, value=f"`{command.description}`", inline=False)
                        await msg.edit(embed=embed)

    @help.command(name="dm", description="Sliding help into your DM.", usage="help dm [category/command (optional)]")
    async def helpDM(self, ctx, *, arg: str = ""):
        """This is the same as help but message through DM instead."""
        cog = await self.isCog(arg.capitalize())
        if cog:
            embed = discord.Embed(title='Category', description=f"Help for {arg.capitalize()}", color=discord.colour.Color.blue())
            for command in cog.walk_commands():
                if not command.hidden:
                    embed.add_field(name=command.qualified_name, value=f"`{command.description}`", inline=False)
            await ctx.message.author.send(embed=embed)
            return
        arg = arg.lower()
        if arg:
            command = await self.check_command(arg)
            if command:
                embed = discord.Embed(title='Command', description=f"Help for {command.qualified_name}", color=discord.Color.blurple())
                embed.add_field(name=f"Usage: {ctx.prefix}{command.usage}", value=f"```\n{command.help}\n```", inline=False)
                await ctx.message.author.send(embed=embed)
            else:
                await ctx.send("I'm not sure there's a category with that name, onii-chan.")
            return
        msg = await ctx.send(embed=self.mainMenu(ctx))
        for i in range(len(self.cogs) + 1):
            await msg.add_reaction(self.emotes[i])
        await msg.add_reaction(self.emotes[len(self.emotes) - 1])

        def check(reaction, user):
            return user == ctx.message.author and str(reaction) in self.emotes and reaction.message.id == msg.id

        while True:
            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
            except asyncio.TimeoutError:
                break
            else:
                index = self.emotes.index(str(reaction))
                if index <= 0:
                    await msg.edit(embed=self.mainMenu(ctx))
                elif index == len(self.emotes) - 1:
                    await msg.delete()
                    break
                else:
                    embed = discord.Embed(title=self.cogs[index - 1], description=f"Help for {self.cogs[index - 1]}", color=discord.colour.Color.blue())
                    for command in self.bot.get_cog(self.cogs[index - 1]).walk_commands():
                        if not command.hidden:
                            embed.add_field(name=command.qualified_name, value=f"`{command.description}`", inline=False)
                    await msg.edit(embed=embed)

    @commands.command(name="setprefix", description="Onii-chan can set a custom prefix for the server.", usage="set_prefix [prefix]")
    @is_server_owner()
    async def set_prefix(self, ctx, *, arg: commands.clean_content):
        """Sets the custom prefix for the server, cannot be empty. Only the server owner to set the prefix.
           If the prefix ends in an alphanumeric character, it will automatically append a space to the end."""
        if arg[-1].isalnum():
            arg += " "
        if int(self.cursor.execute("SELECT EXISTS(SELECT 1 FROM prefixes WHERE server = ?)", (str(ctx.guild.id),)).fetchone()[0]):
            self.cursor.execute("UPDATE prefixes SET prefix = ? WHERE server = ?", (arg, str(ctx.guild.id)))
            self.conn.commit()
        else:
            self.cursor.execute("INSERT INTO prefixes VALUES (?,?)", (str(ctx.guild.id), arg))
            self.conn.commit()
        await ctx.message.add_reaction("✅")

    @commands.command(name="removeprefix", description="Onii-chan can remove the custom prefix.", usage="remove_prefix")
    @is_server_owner()
    async def remove_prefix(self, ctx):
        """Remove the custom prefix. Reverting back to the default prefix which is !loli . Only the server owner can remove the prefix."""
        self.cursor.execute("DELETE FROM prefixes WHERE server = ?", (ctx.guild.id,))
        self.conn.commit()
        await ctx.message.add_reaction("✅")

    @commands.command(name="getprefix", description="Onii-chan can get the current prefix.", usage="get_prefix")
    async def get_prefix(self, ctx):
        """Get the current prefix of the server"""
        prefix = ctx.prefix
        await ctx.send(f"Current prefix for {ctx.guild.name} is `{prefix}`.")

    @commands.command(name="invite", description="Onii-chan can invite me to their server.", usage="invite")
    async def invite_link(self, ctx):
        """Get the invite link to the bot."""
        await ctx.send("https://discord.com/api/oauth2/authorize?client_id=591468206581874691&permissions=1946549329&scope=bot")

    async def check_command(self, command):
        for cog in self.cogs:
            for commands in self.bot.get_cog(cog).walk_commands():
                if command == commands.qualified_name:
                    return commands
        return None

    async def isCog(self, cog):
        """
        temp = self.bot.get_cog(cog)
        if temp:
            return temp
        return None
        """
        if cog not in self.cogs:
            return None
        return self.bot.get_cog(cog)

    def cog_unload(self):
        self.conn.commit();
        self.cursor.close();
        self.conn.close();

def setup(bot):
    bot.add_cog(Essential(bot))