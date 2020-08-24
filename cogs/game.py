import discord
from discord.ext import commands
import asyncio
import random

class Game(commands.Cog, name="Game"):
    """Under construction."""
    def __init__(self, bot):
        self.bot = bot
        self.emotes = ["🇭", "🇩" ,"🇸"]
        self.task = None

    @commands.command(name="blackjack", description="Onii-chan, want to play a game of blackjack with me?", usage="blackjack")
    async def blackjack(self, ctx):
        """A game of blackjack.
        When the game starts, users have 15 seconds to react to the message to join the game.
        During the game, each player have 10 seconds to decide on their action (hit, double down, stand).
        """
        if self.task is None:
            self.task = asyncio.create_task(self.blackjackhelper(ctx))
        else:
            raise commands.MaxConcurrencyReached(1, commands.BucketType.guild)
        try:
            await self.task
        except asyncio.CancelledError:
            await ctx.send("Blackjack game is cancalled.")
            pass
        self.task = None

    @commands.command(name="cancel")
    @commands.is_owner()
    async def cancel(self, ctx):
        if self.task is not None:
            self.task.cancel()
        self.task = None

    async def blackjackhelper(self, ctx):
        msg = await ctx.send("```React to this message to join the game of blackjack.```")
        await msg.add_reaction("✅")

        await asyncio.sleep(15)

        msg = await ctx.fetch_message(msg.id)
        users_list = await self.get_reaction_user(msg).users().flatten()
        for index, user in enumerate(users_list):
            if user.bot:
                users_list.pop(index)
                break
        users = {}
        dealer = BlackjackInfo()
        turn = 0
        for user in users_list:
            users[user] = BlackjackInfo()
        if not users:
            await msg.edit(content="Nobody join :(.")
            return
        await msg.edit(content="Time's up.")
        await msg.delete(delay=2.0)

        dealer.addRandomCard(2)
        for user in users:
            users[user].addRandomCard(2)

        embed = discord.Embed(title="Blackjack", description="A game of blackjack.", color=int("%06x" % random.randint(0, 0xffffff), 16))
        embed.set_footer(text="React H to hit, D to double down, S to stand.")
        embed.add_field(name="Dealer:", value=f"{dealer.hands[0]}/Hidden\n", inline=False)
        for i in range(len(users)):
            embed.add_field(name="", value="", inline=False)
        self.displayUserCard(users, turn, embed)
        msg = await ctx.send(embed=embed)

        natural_blackjack = []
        for user, info in users.items():
            if info.getCardValue() == 21:
                natural_blackjack.append(user)
        if natural_blackjack:
            if dealer.getCardValue() == 21:
                await ctx.send("Natural black jack for both the player and dealer.")
                return
            else:
                await ctx.send(f"Congrats, {'/'.join([user.mention for user in natural_blackjack])}. You won from a natural blackjack.")
                for user in natural_blackjack:
                    users[user].standing()

        if not self.isOver(users):
            await self.addReaction(msg)
            mention = await ctx.send(f"{list(users)[turn].mention} It's your turn.")

            def check(reaction, user):
                return user == list(users)[turn] and str(reaction) in self.emotes and reaction.message.id == msg.id

            while True:
                try:
                    reaction, user = await self.bot.wait_for('reaction_add', timeout=10, check=check)
                except asyncio.TimeoutError:
                    reaction = "🇸"
                    user = list(users)[turn]
                await msg.remove_reaction(reaction, user)
                await mention.delete()
                if str(reaction) == "🇭":
                    users[user].addRandomCard(1)
                    mention = await ctx.send(content=f"{list(users)[turn].mention} You got {users[user].hands[-1]}. Total: {users[user].getCardValue()}")
                    if users[user].getCardValue() > 21:
                        busted = await ctx.send(content=f"{list(users)[turn].mention} Busted.")
                        users[user].standing()
                        await asyncio.sleep(3)
                        await busted.delete()
                        await mention.delete()
                    else:
                        await asyncio.sleep(3)
                        await mention.delete()
                elif str(reaction) == "🇩":
                    users[user].addRandomCard(1)
                    mention = await ctx.send(content=f"{list(users)[turn].mention} You got {users[user].hands[-1]}. Total: {users[user].getCardValue()}")
                    users[user].standing()
                    if users[user].getCardValue() > 21:
                        busted = await ctx.send(content=f"{list(users)[turn].mention} Busted.")
                        await asyncio.sleep(3)
                        await busted.delete()
                        await mention.delete()
                    else:
                        await asyncio.sleep(3)
                        await mention.delete()
                else:
                    users[user].standing()
                if self.isOver(users):
                    break
                turn = self.getNextTurn(users, turn)
                self.displayUserCard(users, turn, embed)
                await msg.edit(embed=embed)
                mention = await ctx.send(f"{list(users)[turn].mention} It's your turn.")

        over = await ctx.send("The game is over, dealer is revealing their hand.")
        await asyncio.sleep(2)
        await over.delete()

        self.displayUserCard(users, -1, embed)
        embed.set_field_at(0, name="```>Dealer:```", value=f"```{'/'.join(dealer.hands)}\nTotal:{dealer.getCardValue()}```", inline=False)
        await msg.delete()
        msg = await ctx.send(embed=embed)
        await asyncio.sleep(1.5)

        while dealer.getCardValue() < 17:
            dealer.addRandomCard(1)
            embed.set_field_at(0, name="```>Dealer:```", value=f"```{'/'.join(dealer.hands)}\nTotal:{dealer.getCardValue()}```", inline=False)
            await msg.edit(embed=embed)
            await asyncio.sleep(1.5)

        winner = self.win(users, dealer.getCardValue())

        if winner:
            await ctx.send(f"Congrats {'/'.join([user.mention for user in winner])}. You won.")
        else:
            await ctx.send("No one won.")

    def get_reaction_user(self, msg):
        for reaction in msg.reactions:
            if str(reaction.emoji) == "✅":
                return reaction
        return None

    def displayUserCard(self, users: dict, turn: int, embed: discord.Embed):
        for i, (user, info) in enumerate(users.items()):
            name = f"{user.display_name}:"
            value = f"{'/'.join(info.hands)}\nTotal:{info.getCardValue()}"
            if i == turn:
                name = "```>"+name+"```"
                value = "```"+value+"```"
            embed.set_field_at(i+1, name=name, value=value, inline=False)

    async def addReaction(self, message):
        for emote in self.emotes:
            await message.add_reaction(emote)

    def isOver(self, users):
        for v in users.values():
            if v.stand == False:
                return False
        return True

    def getNextTurn(self, users, turn):
        while True:
            turn = (turn + 1) % len(users)
            if users[list(users)[turn]].stand == False:
                return turn

    def win(self, users, dealer):
        winner = []
        for user, info in users.items():
            value = info.getCardValue()
            if value <= 21 and (value > dealer or dealer > 21):
                winner.append(user)
        return winner

def setup(bot):
    bot.add_cog(Game(bot))

class BlackjackInfo:
    cards = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5, "Six": 6, "Seven": 7, "Eight": 8, "Nine": 9,
            "Ten": 10, "Jack": 10, "Queen": 10, "King": 10, "Ace": 11}

    def __init__(self, stand=False, hands=None):
        if hands is None:
            hands = []
        self.stand = stand
        self.hands = hands

    def getCardValue(self):
        total = 0
        ace = 0
        for card in self.hands:
            if card == "Ace":
                ace += 1
            else:
                total += BlackjackInfo.cards[card]
        if ace > 0:
            if total <= 10:
                total += 11
            else:
                total += 1
        return total

    def standing(self):
        self.stand = True

    def addRandomCard(self, number=1):
        for i in range(number):
            self.hands.append(random.choice(list(BlackjackInfo.cards.keys())))
