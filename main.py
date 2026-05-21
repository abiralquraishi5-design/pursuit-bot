import discord
from discord.ext import commands

TOKEN = "MTUwNzA0NTkzMDM5NzA3NzYzNQ.GeQsLp.Wf_71lXx7oLDaW5ptR8KIm-gZRlAOgb4tbt8gQ"

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
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason="No reason provided"):

    await member.kick(reason=reason)

    embed = discord.Embed(
        title="User Kicked",
        description=f"{member.name} has been kicked.\nReason: {reason}",
        color=discord.Color.red()
    )

    await ctx.send(embed=embed)

@bot.command()
async def ping(ctx):
    await ctx.send("pong")

bot.run(TOKEN)