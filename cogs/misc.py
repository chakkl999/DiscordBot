import discord
from discord.ext import commands
from discord import Webhook, AsyncWebhookAdapter
import typing
from PIL import Image, ImageFont, ImageDraw
import io
import textwrap
import random
import re
import aiohttp
from inspect import Parameter

class Misc(commands.Cog, name="Misc"):
    """All your miscellaneous commands."""
    def __init__(self, bot):
        self.bot = bot
        self.searchPattern = re.compile("(<:.*?:\d+>|:.*?:)")
        self.matchPattern = re.compile("^(<:.*?:\d+>|:.*?:|[^a-zA-Z0-9:<\-])$")
        self.eightballAnswer = ["It is certain.", "It is decidedly so.", "Without a doubt.", "Yes - definitely.", "You may rely on it.", "As I see it, yes.", "Most likely.", "Outlook good.", "Yes.", "Signs point to yes.", "Reply hazy, try again.", "Ask again later.", "Better not tell you now.", "Cannot predict now.", "Concentrate and ask again.", "Don't count on it.", "My reply is no.", "My sources say no.", "Outlook not so good.", "Very doubtful."]
        try:
            self.font = ImageFont.truetype("./image/font.ttf", 20)
            self.source = Image.open("./image/og.png").convert("RGBA")
        except OSError:
            print("Please make sure you have a font file in the image directory (font.ttf).\nYou don't need it if you don't care about the command.")
            self.font = None
            self.source = None
        except FileNotFoundError:
            print("Please make sure you have the base image (og.png).\nYou don't need it if you don't care about the command.")
            self.source = None

    @commands.command(name="triangle", description="Onii-chan, look at this, I can make a pyramid out of emotes. (　＾∇＾)", usage="triangle [number of row] [emote 1] [emote 2 (optional)]")
    async def triangle(self, ctx, size: int, emote1: typing.Union[commands.EmojiConverter, str], emote2: typing.Union[commands.EmojiConverter, str] = "<:trans:600929649253416980>"):
        """If you don't provide a second emote, it'll default to a transparent emote.
           The arguments must be an emote, otherwise, it will throw an error."""
        if size < 1:
            await ctx.send("Onii-chan, please enter a positive number.")
            return
        pyramid = ""
        if self.matchPattern.match(emote1):
            if emote1.startswith(":"):
                first = discord.utils.get(self.bot.emojis, name=emote1[1:-1])
                if first:
                    emote1 = str(first)
        else:
            raise commands.BadArgument(Parameter("First emote argument not an emote.", Parameter.POSITIONAL_OR_KEYWORD, annotation=str))
        if self.matchPattern.match(emote2):
            if emote2.startswith(":"):
                second = discord.utils.get(self.bot.emojis, name=emote2[1:-1])
                if second:
                    emote2 = str(second)
        else:
            raise commands.BadArgument(Parameter("Second emote argument not an emote.", Parameter.POSITIONAL_OR_KEYWORD, annotation=str))
        for i in range(size):
            pyramid += emote2 * (size - i - 1)
            pyramid += emote1 * (i * 2 + 1)
            # pyramid += emote2 * (size - i - 1)
            pyramid += "\n"
        try:
            await ctx.send(pyramid)
        except:
            await ctx.send("Onii-chan, I can't make a pyramid that big. It needs to be under 2000 characters. >.<")

    @commands.command(name="say", description="Onii-chan can make me say whatever you want >///<", usage="say [things]")
    async def echo(self, ctx, *, arg: commands.clean_content):
        """Repeats whatever you put after the command."""
        await ctx.message.delete()
        await ctx.send(arg)

    @commands.command(name="avatar", description="I can show onii-chan the pfp of the person you mention or yourself.", usage="avatar [mention (optional)]")
    async def avatar(self, ctx, *, mention: typing.Optional[commands.MemberConverter] = None):
        """If you don't mention anyone or the bot can't find the person, it'll return your pfp instead."""
        if not mention:
            mention = ctx.message.author
        embed = discord.Embed(title=str(mention), color=discord.colour.Color.gold())
        embed.set_image(url=str(mention.avatar_url))
        await ctx.send(embed=embed)

    @commands.command(name="reverse", description="I can say whatever Onii-chan wants in reverse.", usage="reverse [things to reverse]")
    async def reverse(self, ctx, *, arg: commands.clean_content):
        """Returns the reversed clean content of whatever you typed"""
        await ctx.send(arg[::-1])

    @commands.command(name="ping", description="Onii-chan can get the latency with this", usage="ping")
    async def ping(self, ctx):
        """Returns the latency of the bot"""
        await ctx.send(f"Pong: {int(self.bot.latency*1000)}ms")

    @commands.command(name="warn", description="Onii-chan... what did you do...", usage="warn [reason for warn]")
    async def warn(self, ctx, *, arg: commands.clean_content):
        """Returns the ALO warn image with the reason you put"""
        if not self.font or not self.source:
            await ctx.send("Onii-chan didn't give me the image or font for this command so I can't do it ( ≧Д≦)")
            return
        arg = await self.text_wrap(str(arg), 50)
        text = Image.new("RGBA", self.source.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(text)
        draw.text((90, 95), arg, font=self.font, fill=(200, 201, 203, 255))
        with io.BytesIO() as buf:
            Image.alpha_composite(self.source, text).save(buf, format="png")
            buf.seek(0)
            await ctx.send(file=discord.File(fp=buf, filename="warn.png"))

    @commands.command(name="8ball", description="Onii-chan can ask the magic 8 ball any questions.", usage="8ball [question]")
    async def eightball(self, ctx, *, arg: commands.clean_content = None):
        """It's the magic 8 ball."""
        if not arg:
            await ctx.send("Onii-chan, you need to ask the magic 8ball something.")
            return
        await ctx.send(random.choice(self.eightballAnswer))

    @commands.command(name="nitro", description="Onii-chan can use any emotes from any server that I'm also in.", usage="nitro [content]")
    async def nitro(self, ctx, *, arg: commands.clean_content):
        """It will look for any emotes in the message and try to replace it for the actual emote.
           Only works for emotes that are in servers that the bot is also in."""
        await ctx.message.delete()
        webhook = discord.utils.get(await ctx.channel.webhooks(), name="Emotes")
        if not webhook:
            webhook = await ctx.channel.create_webhook(name="Emotes", reason="Automatically created webhook for bot.")
        arg = self.searchPattern.split(arg)
        for i in range(len(arg)):
            if arg[i] and arg[i][0] == ':' and arg[i][-1] == ':':
                emote = discord.utils.get(self.bot.emojis, name=arg[i][1:-1])
                if emote:
                    arg[i] = str(emote)
        arg = "".join(arg)
        async with aiohttp.ClientSession() as session:
            w = Webhook.partial(webhook.id, webhook.token, adapter=AsyncWebhookAdapter(session))
            await w.send(content=arg, username=ctx.author.display_name, avatar_url=ctx.author.avatar_url)

    async def text_wrap(self, text, maxwidth):
        text_arr = text.split()
        per_line = ""
        final_text = []
        for i in range(len(text_arr)):
            if len(per_line) + len(text_arr[i]) > maxwidth:
                if i == len(text_arr)-1:
                    if per_line:
                        final_text.append(per_line)
                    if len(text_arr[i]) > maxwidth:
                        final_text.extend(textwrap.wrap(text_arr[i], maxwidth))
                    else:
                        final_text.append(text_arr[i])
                    per_line = ""
                else:
                    final_text.append(per_line)
                    per_line = text_arr[i]
            else:
                if not per_line:
                    per_line = text_arr[i]
                else:
                    per_line += (" " + text_arr[i])
        if per_line:
            final_text.append(per_line)
        return "\n".join(final_text)

def setup(bot):
    bot.add_cog(Misc(bot))