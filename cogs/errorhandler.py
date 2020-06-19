import discord
from discord.ext import commands
import datetime

class ErrorHandler(commands.Cog, name="Errorhandler", command_attrs=dict(hidden=True)):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, discord.ext.commands.NotOwner):
            await ctx.send("Onii-chan, you do not have permission to use this command. (｡>口<｡)!")
        elif isinstance(error, commands.errors.CommandOnCooldown):
            await ctx.send(f"Onii-chan can't use this command yet. Try again in {int(error.retry_after)} second(s). (⁎˃ᆺ˂)")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Onii-chan, make sure you have the required arguments. Use `{ctx.prefix}help {ctx.command.parent.name + ' ' + ctx.command.name if ctx.command.parent else ctx.command.name}` for more details.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send(f"Onii-chan, make sure you have the correct arguments. Use `{ctx.prefix}help {ctx.command.parent.name + ' ' + ctx.command.name if ctx.command.parent else ctx.command.name}` for more details.")
        elif isinstance(error, commands.NSFWChannelRequired):
            await ctx.send("With the nature of this command, in order to avoid the mishaps of including nsfw images, this command is disabled in channels that are not marked as nsfw. I apologize for this inconvenience.")
        elif not isinstance(error, commands.errors.CommandNotFound):
            await ctx.send("An unknown error has occurred. Please tell onii-chan to check #error.")
            embed = discord.Embed(title=f"Server: {ctx.guild.name}")
            embed.add_field(name=f"Command: {ctx.command.name}", value=f"Message: {ctx.message.content if len(ctx.message.content) <= 1024 else 'Too long, Abbreviated: ' + ctx.message.content[0:100]}", inline=False)
            embed.add_field(name="Error:", value=str(error), inline=False)
            embed.set_footer(text=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            await self.bot.get_guild(414125981087825920).get_channel(632118836057079808).send(embed=embed)

def setup(bot):
    bot.add_cog(ErrorHandler(bot))