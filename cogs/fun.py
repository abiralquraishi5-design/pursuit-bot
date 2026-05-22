"""
cogs/fun.py — Fun commands.
"""

import discord
from discord.ext import commands
import random, aiohttp, re

EIGHT_BALL = [
    "🎱 It is certain.", "🎱 Without a doubt.", "🎱 You may rely on it.",
    "🎱 Yes, definitely.", "🎱 Most likely.", "🎱 Outlook good.",
    "🎱 Signs point to yes.", "🎱 Reply hazy, try again.", "🎱 Ask again later.",
    "🎱 Cannot predict now.", "🎱 Don't count on it.", "🎱 My reply is no.",
    "🎱 My sources say no.", "🎱 Outlook not so good.", "🎱 Very doubtful.",
]

class Fun(commands.Cog):
    """🎉 Fun commands."""

    def __init__(self, bot):
        self.bot = bot
        self.trivia_answers: dict[int, str] = {}

    @commands.command(name="8ball")
    async def eight_ball(self, ctx, *, question: str):
        """Ask the magic 8-ball. Usage: !8ball <question>"""
        embed = discord.Embed(color=discord.Color.purple())
        embed.add_field(name="❓ Question", value=question, inline=False)
        embed.add_field(name="Answer", value=random.choice(EIGHT_BALL), inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="roll")
    async def roll(self, ctx, dice: str = "1d6"):
        """Roll dice. Usage: !roll 2d20"""
        try:
            count, sides = map(int, dice.lower().split("d"))
            if not (1 <= count <= 100 and sides >= 2):
                raise ValueError
        except ValueError:
            return await ctx.send("❌ Use format like `2d6`.")
        rolls = [random.randint(1, sides) for _ in range(count)]
        await ctx.send(f"🎲 Rolled **{dice}**: [{', '.join(map(str,rolls))}] = **{sum(rolls)}**")

    @commands.command(name="coinflip")
    async def coinflip(self, ctx):
        """Flip a coin. Usage: !coinflip"""
        await ctx.send(random.choice(["🪙 **Heads!**", "🪙 **Tails!**"]))

    @commands.command(name="rps")
    async def rps(self, ctx, choice: str):
        """Rock Paper Scissors. Usage: !rps rock"""
        opts = ["rock","paper","scissors"]
        choice = choice.lower()
        if choice not in opts:
            return await ctx.send("❌ Choose `rock`, `paper`, or `scissors`.")
        bot_c = random.choice(opts)
        if choice == bot_c:
            result = "🤝 Tie!"
        elif (choice,bot_c) in [("rock","scissors"),("paper","rock"),("scissors","paper")]:
            result = "🎉 You win!"
        else:
            result = "😈 I win!"
        await ctx.send(f"You: **{choice}** | Me: **{bot_c}** — {result}")

    @commands.command(name="trivia")
    async def trivia(self, ctx):
        """Random trivia question. Usage: !trivia"""
        async with aiohttp.ClientSession() as s:
            async with s.get("https://opentdb.com/api.php?amount=1&type=multiple") as r:
                data = await r.json()
        q = data["results"][0]
        clean = lambda t: t.replace("&quot;",'"').replace("&#039;","'").replace("&amp;","&").replace("&lt;","<").replace("&gt;",">")
        question = clean(q["question"])
        correct  = clean(q["correct_answer"])
        wrong    = [clean(a) for a in q["incorrect_answers"]]
        answers  = wrong + [correct]
        random.shuffle(answers)
        emojis   = ["🇦","🇧","🇨","🇩"]
        correct_e = emojis[answers.index(correct)]
        self.trivia_answers[ctx.channel.id] = correct_e
        choices  = "\n".join(f"{emojis[i]} {a}" for i, a in enumerate(answers))
        embed = discord.Embed(title="🧠 Trivia!", description=f"**{question}**\n\n{choices}", color=discord.Color.gold())
        embed.set_footer(text=f"Category: {q['category']} | Answer with !answer 🇦/🇧/🇨/🇩")
        await ctx.send(embed=embed)

    @commands.command(name="answer")
    async def answer(self, ctx, choice: str):
        """Answer the current trivia question. Usage: !answer 🇦"""
        correct = self.trivia_answers.get(ctx.channel.id)
        if not correct:
            return await ctx.send("❌ No active trivia question. Use !trivia first.")
        if choice == correct:
            await ctx.send(f"✅ {ctx.author.mention} got it right! 🎉")
        else:
            await ctx.send(f"❌ Wrong! The correct answer was **{correct}**.")
        del self.trivia_answers[ctx.channel.id]

    @commands.command(name="meme")
    async def meme(self, ctx):
        """Get a random meme. Usage: !meme"""
        async with aiohttp.ClientSession() as s:
            async with s.get("https://meme-api.com/gimme") as r:
                data = await r.json()
        embed = discord.Embed(title=data["title"], color=discord.Color.orange())
        embed.set_image(url=data["url"])
        embed.set_footer(text=f"👍 {data['ups']} | r/{data['subreddit']}")
        await ctx.send(embed=embed)

    @commands.command(name="joke")
    async def joke(self, ctx):
        """Get a random joke. Usage: !joke"""
        async with aiohttp.ClientSession() as s:
            async with s.get("https://official-joke-api.appspot.com/random_joke") as r:
                data = await r.json()
        await ctx.send(f"😂 **{data['setup']}**\n||{data['punchline']}||")

async def setup(bot):
    await bot.add_cog(Fun(bot))
