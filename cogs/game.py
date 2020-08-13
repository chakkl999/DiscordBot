import discord
from discord.ext import commands
import asyncio
import random

class Game(commands.Cog, name="Game"):
    """Under construction."""
    def __init__(self, bot):
        self.bot = bot
        self.cards = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5, "Six": 6, "Seven": 7, "Eight": 8, "Nine": 9,
                      "Ten": 10, "Jack": 10, "Queen": 10, "King": 10, "Ace": 11}
        self.emotes = ["🇭", "🇩" ,"🇸"]

    @commands.command(name="blackjack", description="Onii-chan, want to play a game of blackjack with me?", usage="blackjack")
    @commands.cooldown(rate=1, per=0.0, type=commands.BucketType.guild)
    async def blackjack(self, ctx):
        """A game of blackjack.
        When the game starts, users have 15 seconds to react to the message to join the game.
        During the game, each player have 10 seconds to decide on their action (hit, double down, stand).
        """
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
        dealer_card = []
        turn = 0
        for user in users_list:
            users[user] = [False, []]
        if not users:
            await msg.edit(content="Nobody join :(.")
            return
        await msg.edit(content="Time's up.")
        await msg.delete(delay=2.0)

        dealer_card.extend([self.randomCard(), self.randomCard()])
        for user in users:
            users[user][1].extend([self.randomCard(), self.randomCard()])

        embed = discord.Embed(title="Blackjack", description="A game of blackjack.", color=int("%06x" % random.randint(0, 0xffffff), 16))
        embed.set_footer(text="React H to hit, D to double down, S to stand.")
        embed.add_field(name="Dealer:", value=f"{dealer_card[0]}/Hidden\n", inline=False)
        for i in range(len(users)):
            embed.add_field(name="", value="", inline=False)
        self.displayUserCard(users, turn, embed)
        msg = await ctx.send(embed=embed)

        natural_blackjack = []
        for user, cards in users.items():
            if self.getCardValue(cards[1]) == 21:
                natural_blackjack.append(user)
        if natural_blackjack:
            if self.getCardValue(dealer_card) == 21:
                await ctx.send("Natural black jack for both the player and dealer.")
                return
            else:
                await ctx.send(f"Congrats, {'/'.join([user.mention for user in natural_blackjack])}. You won from a natural blackjack.")
                return

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
                users[user][1].append(self.randomCard())
                mention = await ctx.send(content=f"{list(users)[turn].mention} You got {users[user][1][-1]}. Total: {self.getCardValue(users[user][1])}")
                await asyncio.sleep(3)
                await mention.delete()
                if self.getCardValue(users[user][1]) > 21:
                    busted = await ctx.send(content=f"{list(users)[turn].mention} Busted.")
                    users[user][0] = True
                    await asyncio.sleep(3)
                    await busted.delete()
            elif str(reaction) == "🇩":
                users[user][1].append(self.randomCard())
                mention = await ctx.send(content=f"{list(users)[turn].mention} You got {users[user][1][-1]}. Total: {self.getCardValue(users[user][1])}")
                await asyncio.sleep(3)
                await mention.delete()
                users[user][0] = True
                if self.getCardValue(users[user][1]) > 21:
                    busted = await ctx.send(content=f"{list(users)[turn].mention} Busted.")
                    await asyncio.sleep(3)
                    await busted.delete()
            else:
                users[user][0] = True
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
        embed.set_field_at(0, name="```>Dealer:```", value=f"```{'/'.join(dealer_card)}\nTotal:{self.getCardValue(dealer_card)}```", inline=False)
        await msg.delete()
        msg = await ctx.send(embed=embed)
        await asyncio.sleep(1.5)

        while self.getCardValue(dealer_card) < 17:
            dealer_card.append(self.randomCard())
            embed.set_field_at(0, name="```>Dealer:```", value=f"```{'/'.join(dealer_card)}\nTotal:{self.getCardValue(dealer_card)}```", inline= False)
            await msg.edit(embed=embed)
            await asyncio.sleep(1.5)

        winner = self.win(users, self.getCardValue(dealer_card))

        if winner:
            await ctx.send(f"Congrats {'/'.join([user.mention for user in winner])}. You won.")
        else:
            await ctx.send("No one won.")

    def get_reaction_user(self, msg):
        for reaction in msg.reactions:
            if str(reaction.emoji) == "✅":
                return reaction
        return None

    def randomCard(self):
        return random.choice(list(self.cards.keys()))

    def getCardValue(self, cards):
        total = 0
        have_ace = False
        for card in cards:
            if card == "Ace":
                have_ace = True
            else:
                total += self.cards[card]
        if have_ace:
            if total <= 10:
                total += 11
            else:
                total += 1
        return total

    def displayUserCard(self, users: dict, turn: int, embed: discord.Embed):
        for i, (user, cards) in enumerate(users.items()):
            name = f"{user.display_name}:"
            value = f"{'/'.join(cards[1])}\nTotal:{self.getCardValue(cards[1])}"
            if i == turn:
                name = "```>"+name+"```"
                value = "```"+value+"```"
            embed.set_field_at(i+1, name=name, value=value, inline=False)

    async def addReaction(self, message):
        for emote in self.emotes:
            await message.add_reaction(emote)

    def isOver(self, users):
        for v in users.values():
            if v[0] == False:
                return False
        return True

    def getNextTurn(self, users, turn):
        while True:
            turn = (turn + 1) % len(users)
            if not users[list(users)[turn]][0]:
                return turn

    def win(self, users, dealer):
        winner = []
        for user, cards in users.items():
            value = self.getCardValue(cards[1])
            if value < 21 and (value > dealer or dealer > 21):
                winner.append(user)
        return winner

def setup(bot):
    bot.add_cog(Game(bot))