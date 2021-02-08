import discord
from discord.ext import commands
import asyncio
import typing
from django.core.paginator import Paginator
import json

class Search(commands.Cog, name="Search"):
    """Commands relating to searching for things."""
    def __init__(self, bot):
        self.bot = bot
        self.emotes = ["⏪", "◀", "▶", "⏩"]
        self.session = bot.getSession()
        self.config = bot.getConfig()
        self.baseURL = "https://www.youtube.com/watch?v="

    @commands.command(name="yt", description="I can search whatever onii-chan wants on youtube. Onii-chan, don't search for any lewd things, ok?（＞д＜）", usage="yt [things to search]")
    @commands.max_concurrency(number=1, per=commands.BucketType.guild)
    async def yt(self, ctx, *, arg):
        # Credit to https://github.com/joetats/youtube_search for the parsing of the html
        """Searches things on youtube. It'll return the first page of videos and channels(apparently). Limit to 10 videos/channel. I might include an optional limit later but idk."""
        await ctx.send("Searching for ***" + arg + "***.......")
        vids = []
        """
        async with self.session.get(url="https://www.youtube.com/results?search_query=" + arg) as r:
            data = await r.text()
        startIndex = (data.index('window["ytInitialData"]') + len('window["ytInitialData"]') + 3)
        endIndex = data.index("};", startIndex) + 1
        response = json.loads(data[startIndex:endIndex])["contents"]["twoColumnSearchResultsRenderer"]["primaryContents"]["sectionListRenderer"]["contents"][0]["itemSectionRenderer"]["contents"]
        for vid in response:
            if "videoRenderer" in vid:
                id = vid.get("videoRenderer", {}).get("videoId", None)
                if id:
                    vids.append(id)
        """
        async with self.session.get(url=f"https://www.googleapis.com/youtube/v3/search?part={'id'}&q={arg}&key={self.config.youtubeToken}&maxResults={self.config.youtubeMaxResult}") as r:
            data = json.loads(await r.text())
        for item in data["items"]:
            if item["id"]["kind"] == "youtube#video":
                vids.append(item["id"]["videoId"])

        if not vids:
            await ctx.send("Sorry onii-chan, I can't find any video.（>﹏<）")
            return
        message = await ctx.send(f"{self.baseURL}{vids[0]}\nPage: {1}/{len(vids)}")
        currentIndex = 0
        for i in range(len(self.emotes)):
            await message.add_reaction(self.emotes[i])
        def check(reaction, user):
            return user == ctx.message.author and str(reaction) in self.emotes and reaction.message.id == message.id
        while True:
            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=self.config.search_timeout, check=check)
                await message.remove_reaction(reaction, user)
            except asyncio.TimeoutError:
                await message.clear_reactions()
                break
            else:
                currentIndex, test = self.getNextPage(str(reaction), currentIndex, len(vids))
                await message.edit(content=f"{self.baseURL}{vids[currentIndex]}\nPage: {currentIndex+1}/{len(vids)}")

    @commands.command(name="als", description="I can search things up on the azur lane wiki for onii-chan.", usage="als [things to search]")
    async def als(self, ctx, *, arg: str):
        """Search things on the AL wiki. To search multiple things, separate each argument with |.
        It can only return a maximum of 15 results.
        This number includes redirects, file, and empty pages which are not shown in the results. So, the actual result shown might be much less than 15 or even none."""
        arg = arg.split("|")
        for a in arg:
            a.strip()
        arg = " | ".join(arg)
        async with self.session.get(url='https://azurlane.koumakan.jp/w/api.php?action=query&format=json&list=search&srlimit=20', params={
            'srsearch': arg
        }) as r:
            data = await r.json()
        titles = []
        for title in data['query']['search']:
            if title["snippet"].startswith("#REDIRECT") or not title['snippet']:
                pass
            else:
                titles.append(title['title'])
        if not titles:
            await ctx.send("Sorry onii-chan, I can't find anything.")
            return
        embed = discord.Embed(title="Results:", color=discord.Color.green())
        for x in titles:
            embed.add_field(name=x, value=f"https://azurlane.koumakan.jp/{x.replace(' ', '_')}", inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="alsi", description="I can search up images on the azur lane wiki for onii-chan", usage="alsi [things to search]")
    async def alsi(self, ctx, *, arg: str):
        """Search images on the AL wiki. To search multiple images, separate each argument with |.
        Altho this does search image, you do need to know the exact name of the file because wiki search isn't very good."""
        arg = arg.split("|")
        for i in range(len(arg)):
            arg[i] = arg[i][:1].upper() + arg[i][1:]
            arg[i] = f"File:{arg[i].strip()}.png"
        arg = "|".join(arg)
        async with self.session.get(url='https://azurlane.koumakan.jp/w/api.php?action=query&format=json&prop=imageinfo&iiprop=url', params={
            "titles": arg
        }) as r:
            data = await r.json()
        data = data["query"]["pages"]
        results = []
        for page in data:
            if int(page) < 0:
                pass
            else:
                results.append((data[page]["title"][5:-4], data[page]["imageinfo"][0]["url"]))
        if not results:
            await ctx.send("Sorry onii-chan, I can't find anything.")
            return
        if len(results) == 1:
            embed = discord.Embed(title=results[0][0], color=discord.Color.dark_orange())
            embed.set_image(url=results[0][1])
            await ctx.send(embed=embed)
            return
        embed = discord.Embed(title=results[0][0], color=discord.Color.dark_orange())
        embed.set_image(url=results[0][1])
        embed.set_footer(text=f"Page: {1}/{len(results)}")
        message = await ctx.send(embed=embed)
        currentIndex = 0

        for i in range(len(self.emotes)):
            await message.add_reaction(self.emotes[i])

        def check(reaction, user):
            return user == ctx.message.author and str(reaction) in self.emotes and reaction.message.id == message.id
        while True:
            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=self.config.search_timeout, check=check)
                await message.remove_reaction(reaction, user)
            except asyncio.TimeoutError:
                await message.clear_reactions()
                break
            else:
                currentIndex, update = self.getNextPage(str(reaction), currentIndex, len(results))
                if update:
                    embed = discord.Embed(title=results[currentIndex][0], color=discord.Color.dark_orange())
                    embed.set_image(url=results[currentIndex][1])
                    embed.set_footer(text=f"Page: {currentIndex+1}/{len(results)}")
                    await message.edit(embed=embed)

    @commands.group(name="alsf", description="I can search files on the AL wiki for onii-chan if onii-chan doesn't know the file name.", usage="alsf [things to search]")
    async def alsf(self, ctx, *, arg: str):
        """Searches file name on AL wiki.
        This returns a maximum of 100 results.
        Only .png file will be returned."""
        arg = arg.strip()
        async with self.session.get(url='https://azurlane.koumakan.jp/w/api.php?action=opensearch&format=json&namespace=6&limit=100&redirects=resolve', params={
            "search": arg
        }) as r:
            data = await r.json()
        if not data[1]:
            await ctx.send("Sorry onii-chan, I can't find anything.")
            return
        data = [file for file in data[1] if file.endswith(".png")]
        p = Paginator(data, 20, allow_empty_first_page=False)
        currentPage = 1
        emotes = ["◀", "▶"]
        def check(reaction, user):
            return user == ctx.message.author and str(reaction) in emotes and reaction.message.id == message.id

        embed = discord.Embed()
        embed.add_field(name=f"Search results for {arg}", value="\n".join(p.page(currentPage).object_list))
        if p.num_pages == 1:
            message = await ctx.send(embed=embed)
            return
        embed.set_footer(text=f"Page {currentPage}/{p.num_pages}")
        message = await ctx.send(embed=embed)
        for emote in emotes:
            await message.add_reaction(emote)
        while True:
            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=self.config.search_timeout, check=check)
                await message.remove_reaction(reaction, user)
            except asyncio.TimeoutError:
                await message.clear_reactions()
                break
            else:
                currentPage, test = self.getNextPage(str(reaction), currentPage, p.num_pages, True)
                embed.set_field_at(0, name=f"Search results for {arg}", value="\n".join(p.page(currentPage).object_list))
                embed.set_footer(text=f"Page: {currentPage}/{p.num_pages}")
                await message.edit(embed=embed)

    @commands.command(name="gb", description="I can search images on gelbooru but this is a lewd website isn't it? Onii-chan is a hentai...", usage="gb [limit (optional)] [things to search]")
    @commands.is_nsfw()
    async def gb(self, ctx, limit: typing.Optional[int] = 20, *, arg: str):
        """Search images on gelbooru. Separate each tag with |. This searches 50 images but it can only display a maximum of 20 images.
        If you don't include a limit, it'll default to 20.
        The limit is 20 just because I don't think you would want to press the next button so many times.
        Command can only be used in nsfw channels."""
        if limit < 1 or limit > 20:
            await ctx.send("Onii-chan, enter a number that I can work with.")
            return
        arg = " ".join([tag.strip().replace(" ", "_") for tag in list(filter(None, (" ".join(arg.split())).split("|")))])
        async with self.session.get(url="https://gelbooru.com/index.php?page=dapi&s=post&q=index&json=1", params={
            "tags": arg
        }) as r:
            data = await r.json()
        if not data:
            await ctx.send("Sorry onii-chan, I can't find anything. .( ̵˃﹏˂̵ )")
            return
        results = []
        for file in data:
            # if file["rating"] != 'e':
            if file["rating"] == "s":
                results.append((file["source"], file["file_url"], file["id"]))
            if len(results) == limit:
                break
        if not results:
            await ctx.send(f"Found {len(data)} results but they're all lewd. Onii-chan... hentai.")
            return
        embed = discord.Embed(title="Search results:", color=discord.Color.dark_blue())
        embed.add_field(name="Source:", value=results[0][0] or "No sauce", inline=False)
        embed.set_image(url=results[0][1])
        embed.add_field(name="Gelbooru:", value=f"https://gelbooru.com/index.php?page=post&s=view&id={results[0][2]}", inline=False)
        if len(results) == 1:
            await ctx.send(embed=embed)
            return
        embed.set_footer(text=f"Page: {1}/{len(results)}")
        message = await ctx.send(embed=embed)
        currentIndex = 0

        for emote in self.emotes:
            await message.add_reaction(emote)

        def check(reaction, user):
            return user == ctx.message.author and str(reaction) in self.emotes and reaction.message.id == message.id

        while True:
            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=self.config.search_timeout, check=check)
                await message.remove_reaction(reaction, user)
            except asyncio.TimeoutError:
                await message.clear_reactions()
                break
            else:
                currentIndex, update = self.getNextPage(str(reaction), currentIndex, len(results))
                if update:
                    embed.set_field_at(0, name="Source:", value=results[currentIndex][0] or "No sauce", inline=False)
                    embed.set_field_at(1, name="Gelbooru:", value=f"https://gelbooru.com/index.php?page=post&s=view&id={results[currentIndex][2]}", inline=False)
                    embed.set_image(url=results[currentIndex][1])
                    embed.set_footer(text=f"Page: {currentIndex + 1}/{len(results)}")
                    await message.edit(embed=embed)

    def getNextPage(self, reaction: str, current: int, max_page: int, start_index_one: bool = False):
        if start_index_one:
            current = current - 1
        temp = True
        if reaction == "⏪":
            if not current:
                temp = False
            current = 0
        if reaction == "◀":
            current = (current - 1) % max_page
        if reaction == "▶":
            current = (current + 1) % max_page
        if reaction == "⏩":
            if current == max_page - 1:
                temp = False
            current = max_page - 1
        if start_index_one:
            current = current + 1
        return current, temp

def setup(bot):
    bot.add_cog(Search(bot))