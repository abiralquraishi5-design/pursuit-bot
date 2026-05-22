"""
cogs/utility.py
Replaces: Dyno, Carl-bot utility features.
"""

import discord
from discord.ext import commands
from discord import app_commands
import aiohttp

class Utility(commands.Cog):
    """🔧 Utility — info, polls, embeds, and more."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="ping")
    async def ping(self, ctx):
        """Check bot latency. Usage: !ping"""
        await ctx.send(f"🏓 Pong! **{round(self.bot.latency * 1000)}ms**")

    @commands.command(name="serverinfo")
    async def serverinfo(self, ctx):
        """Show server info. Usage: !serverinfo"""
        g = ctx.guild
        embed = discord.Embed(title=f"📊 {g.name}", color=discord.Color.blurple())
        if g.icon:
            embed.set_thumbnail(url=g.icon.url)
        embed.add_field(name="Owner", value=str(g.owner), inline=True)
        embed.add_field(name="Members", value=g.member_count, inline=True)
        embed.add_field(name="Channels", value=len(g.channels), inline=True)
        embed.add_field(name="Roles", value=len(g.roles), inline=True)
        embed.add_field(name="Boost Level", value=g.premium_tier, inline=True)
        embed.add_field(name="Created", value=f"<t:{int(g.created_at.timestamp())}:R>", inline=True)
        await ctx.send(embed=embed)

    @commands.command(name="userinfo")
    async def userinfo(self, ctx, member: discord.Member = None):
        """Show user info. Usage: !userinfo [@user]"""
        m = member or ctx.author
        embed = discord.Embed(title=f"👤 {m}", color=m.color)
        embed.set_thumbnail(url=m.display_avatar.url)
        embed.add_field(name="ID", value=m.id, inline=True)
        embed.add_field(name="Nickname", value=m.nick or "None", inline=True)
        embed.add_field(name="Bot", value="Yes" if m.bot else "No", inline=True)
        embed.add_field(name="Joined Server", value=f"<t:{int(m.joined_at.timestamp())}:R>", inline=True)
        embed.add_field(name="Account Created", value=f"<t:{int(m.created_at.timestamp())}:R>", inline=True)
        roles = [r.mention for r in m.roles if r.name != "@everyone"]
        embed.add_field(name=f"Roles ({len(roles)})", value=" ".join(roles[:10]) or "None", inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="avatar")
    async def avatar(self, ctx, member: discord.Member = None):
        """Show avatar. Usage: !avatar [@user]"""
        m = member or ctx.author
        embed = discord.Embed(title=f"🖼️ {m.display_name}'s Avatar", color=discord.Color.blurple())
        embed.set_image(url=m.display_avatar.url)
        await ctx.send(embed=embed)

    @commands.command(name="poll")
    async def poll(self, ctx, question: str, *options):
        """Create a poll. Usage: !poll "Question" "Option 1" "Option 2" ..."""
        if len(options) < 2:
            return await ctx.send('❌ Provide at least 2 options. Use quotes: `!poll "Q" "A" "B"`')
        if len(options) > 9:
            return await ctx.send("❌ Maximum 9 options.")
        emojis = ["1️⃣","2️⃣","3️⃣","4️⃣","5️⃣","6️⃣","7️⃣","8️⃣","9️⃣"]
        desc = "\n".join(f"{emojis[i]} {opt}" for i, opt in enumerate(options))
        embed = discord.Embed(title=f"📊 {question}", description=desc, color=discord.Color.green())
        embed.set_footer(text=f"Poll by {ctx.author.display_name}")
        msg = await ctx.send(embed=embed)
        for i in range(len(options)):
            await msg.add_reaction(emojis[i])

    @commands.command(name="say")
    @commands.has_permissions(manage_messages=True)
    async def say(self, ctx, *, message: str):
        """Make the bot say something. Usage: !say <message>"""
        await ctx.message.delete()
        await ctx.send(message)

    @commands.command(name="embed")
    @commands.has_permissions(manage_messages=True)
    async def embed_cmd(self, ctx, title: str, *, description: str):
        """Send an embed. Usage: !embed "Title" Description text"""
        embed = discord.Embed(title=title, description=description, color=discord.Color.blurple())
        embed.set_footer(text=f"Sent by {ctx.author.display_name}")
        await ctx.send(embed=embed)

    @commands.command(name="translate")
    async def translate(self, ctx, language: str, *, text: str):
        """Translate text via AI. Usage: !translate Spanish Hello world"""
        async with ctx.typing():
            import os, aiohttp as aio
            headers = {"x-api-key": os.getenv("ANTHROPIC_API_KEY"), "anthropic-version": "2023-06-01", "content-type": "application/json"}
            payload = {
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 500,
                "messages": [{"role": "user", "content": f"Translate the following text to {language}. Reply with ONLY the translation, no explanations:\n\n{text}"}]
            }
            async with aio.ClientSession() as session:
                async with session.post("https://api.anthropic.com/v1/messages", headers=headers, json=payload) as resp:
                    data = await resp.json()
            result = data["content"][0]["text"] if "content" in data else "❌ Translation failed."
        await ctx.send(f"🌐 **{language}:** {result}")

    @commands.command(name="roleinfo")
    async def roleinfo(self, ctx, role: discord.Role):
        """Show role info. Usage: !roleinfo @role"""
        embed = discord.Embed(title=f"🏷️ {role.name}", color=role.color)
        embed.add_field(name="ID", value=role.id, inline=True)
        embed.add_field(name="Color", value=str(role.color), inline=True)
        embed.add_field(name="Mentionable", value=role.mentionable, inline=True)
        embed.add_field(name="Hoisted", value=role.hoist, inline=True)
        embed.add_field(name="Members", value=len(role.members), inline=True)
        embed.add_field(name="Created", value=f"<t:{int(role.created_at.timestamp())}:R>", inline=True)
        await ctx.send(embed=embed)

    @commands.command(name="channelinfo")
    async def channelinfo(self, ctx):
        """Show info about this channel. Usage: !channelinfo"""
        ch = ctx.channel
        embed = discord.Embed(title=f"📢 #{ch.name}", color=discord.Color.blurple())
        embed.add_field(name="ID", value=ch.id, inline=True)
        embed.add_field(name="Type", value=str(ch.type).title(), inline=True)
        embed.add_field(name="Category", value=ch.category.name if ch.category else "None", inline=True)
        embed.add_field(name="Slowmode", value=f"{ch.slowmode_delay}s", inline=True)
        embed.add_field(name="Created", value=f"<t:{int(ch.created_at.timestamp())}:R>", inline=True)
        if ch.topic:
            embed.add_field(name="Topic", value=ch.topic, inline=False)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Utility(bot))
