"""
cogs/ai.py — AI commands powered by Claude API.
Replaces: iTranslator + general AI needs.
"""

import discord
from discord.ext import commands
from discord import app_commands
import aiohttp, os

MODEL = "claude-sonnet-4-20250514"
MAX_HISTORY = 10

class AI(commands.Cog):
    """🤖 AI — powered by Claude. Chat, summarize, translate, and more."""

    def __init__(self, bot):
        self.bot = bot
        self.conversations: dict[int, list] = {}

    def _history(self, channel_id):
        return self.conversations.setdefault(channel_id, [])

    def _add(self, channel_id, role, content):
        h = self._history(channel_id)
        h.append({"role": role, "content": content})
        if len(h) > MAX_HISTORY * 2:
            self.conversations[channel_id] = h[-(MAX_HISTORY * 2):]

    async def _claude(self, channel_id, prompt, system=None):
        key = os.getenv("ANTHROPIC_API_KEY")
        if not key:
            return "❌ ANTHROPIC_API_KEY is not set in .env"
        self._add(channel_id, "user", prompt)
        headers = {
            "x-api-key": key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        body = {
            "model": MODEL,
            "max_tokens": 1000,
            "system": system or "You are a helpful, friendly Discord bot. Keep responses concise and suitable for chat.",
            "messages": self._history(channel_id)
        }
        async with aiohttp.ClientSession() as s:
            async with s.post("https://api.anthropic.com/v1/messages", headers=headers, json=body) as r:
                data = await r.json()
        if "content" not in data:
            return f"❌ API error: {data.get('error',{}).get('message','Unknown')}"
        reply = data["content"][0]["text"]
        self._add(channel_id, "assistant", reply)
        return reply[:1990] if len(reply) > 1990 else reply

    @commands.command(name="ask")
    async def ask(self, ctx, *, question: str):
        """Ask the AI a question (no memory). Usage: !ask <question>"""
        async with ctx.typing():
            # Fresh conversation for !ask
            temp_id = f"ask_{ctx.message.id}"
            resp = await self._claude(temp_id, question)
            self.conversations.pop(temp_id, None)
        await ctx.send(resp)

    @commands.command(name="chat")
    async def chat(self, ctx, *, message: str):
        """Chat with AI (remembers context per channel). Usage: !chat <message>"""
        async with ctx.typing():
            resp = await self._claude(ctx.channel.id, message)
        await ctx.send(resp)

    @commands.command(name="clearchat")
    async def clearchat(self, ctx):
        """Clear AI chat history for this channel. Usage: !clearchat"""
        self.conversations.pop(ctx.channel.id, None)
        await ctx.send("🧹 AI chat history cleared.")

    @commands.command(name="summarize")
    async def summarize(self, ctx, *, text: str):
        """Summarize text. Usage: !summarize <text>"""
        async with ctx.typing():
            resp = await self._claude(
                f"sum_{ctx.message.id}",
                f"Summarize this concisely:\n\n{text}",
                system="You are a concise summarizer. Give bullet points."
            )
        await ctx.send(f"📝 **Summary:**\n{resp}")

    @commands.command(name="roast")
    async def roast(self, ctx, member: discord.Member = None):
        """Roast a member (all in good fun). Usage: !roast [@user]"""
        target = member or ctx.author
        async with ctx.typing():
            resp = await self._claude(
                f"roast_{ctx.message.id}",
                f"Give a funny, light-hearted roast of a Discord user named '{target.display_name}'. Keep it playful and not mean-spirited.",
                system="You are a comedy roast writer. Be funny, not cruel."
            )
        await ctx.send(f"🔥 {target.mention} {resp}")

    @commands.command(name="compliment")
    async def compliment(self, ctx, member: discord.Member = None):
        """Compliment a member. Usage: !compliment [@user]"""
        target = member or ctx.author
        async with ctx.typing():
            resp = await self._claude(
                f"compliment_{ctx.message.id}",
                f"Give a genuine, creative compliment to a Discord user named '{target.display_name}'.",
                system="You give warm, creative compliments."
            )
        await ctx.send(f"💖 {target.mention} {resp}")

    @app_commands.command(name="ask", description="Ask Claude a question")
    @app_commands.describe(question="Your question")
    async def ask_slash(self, interaction: discord.Interaction, question: str):
        await interaction.response.defer()
        temp_id = f"slash_{interaction.id}"
        resp = await self._claude(temp_id, question)
        self.conversations.pop(temp_id, None)
        await interaction.followup.send(resp)

async def setup(bot):
    await bot.add_cog(AI(bot))
