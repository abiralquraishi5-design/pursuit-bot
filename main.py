import os
import discord
from discord.ext import commands

TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(
    command_prefix=["!", "?"],
    intents=intents
)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

@bot.command()
async def ping(ctx):
    await ctx.send("pong")

@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason="No reason provided"):

    await member.kick(reason=reason)

    embed = discord.Embed(
        title="User Kicked",
        description=f"{member.name} has been kicked.\nReason: {reason}",
        color=discord.Color.red()
    )

    await ctx.send(embed=embed)

bot.run(TOKEN)