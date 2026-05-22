"""
cogs/help.py — Custom help command.
"""

import discord
from discord.ext import commands

class Help(commands.Cog):
    """❓ Help system."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="help")
    async def help_cmd(self, ctx, category: str = None):
        """Show help. Usage: !help [category]"""

        categories = {
            "mod": {
                "title": "🛡️ Moderation",
                "commands": [
                    ("!warn @user [reason]", "Warn a member"),
                    ("!warnings @user", "View warnings"),
                    ("!delwarn <id>", "Delete a warning"),
                    ("!clearwarnings @user", "Clear all warnings"),
                    ("!ban @user [duration] [reason]", "Ban (use 1d/2h/30m for temp-ban)"),
                    ("!unban <user_id>", "Unban by user ID"),
                    ("!kick @user [reason]", "Kick a member"),
                    ("!mute @user [duration] [reason]", "Timeout a member"),
                    ("!unmute @user", "Remove timeout"),
                    ("!clear [amount]", "Delete messages"),
                    ("!lock / !unlock", "Lock/unlock channel"),
                    ("!slowmode [seconds]", "Set channel slowmode"),
                    ("!addrole @user @role", "Add a role"),
                    ("!removerole @user @role", "Remove a role"),
                ]
            },
            "utility": {
                "title": "🔧 Utility",
                "commands": [
                    ("!ping", "Check latency"),
                    ("!serverinfo", "Server info"),
                    ("!userinfo [@user]", "User info"),
                    ("!avatar [@user]", "Show avatar"),
                    ("!roleinfo @role", "Role info"),
                    ("!channelinfo", "Channel info"),
                    ('!poll "Q" "A" "B"', "Create a poll"),
                    ("!say <message>", "Bot says something"),
                    ('!embed "Title" Body', "Send an embed"),
                    ("!translate <lang> <text>", "Translate text"),
                ]
            },
            "rr": {
                "title": "🎭 Reaction Roles",
                "commands": [
                    ("!rr add #ch <msg_id> <emoji> @role", "Add reaction role"),
                    ("!rr remove <msg_id> <emoji>", "Remove reaction role"),
                    ("!rr list", "List all reaction roles"),
                ]
            },
            "verify": {
                "title": "✅ Verification",
                "commands": [
                    ("!setverifyrole @role", "Set the verified role"),
                    ("!sendverify [message]", "Send the verify panel"),
                ]
            },
            "level": {
                "title": "⭐ Leveling",
                "commands": [
                    ("!rank [@user]", "Check your rank"),
                    ("!leaderboard", "Server leaderboard"),
                    ("!givexp @user <amount>", "Give XP (admin)"),
                ]
            },
            "fun": {
                "title": "🎉 Fun",
                "commands": [
                    ("!8ball <question>", "Magic 8-ball"),
                    ("!roll [NdN]", "Roll dice"),
                    ("!coinflip", "Flip a coin"),
                    ("!rps <choice>", "Rock paper scissors"),
                    ("!trivia", "Trivia question"),
                    ("!answer <emoji>", "Answer trivia"),
                    ("!meme", "Random meme"),
                    ("!joke", "Random joke"),
                ]
            },
            "ai": {
                "title": "🤖 AI",
                "commands": [
                    ("!ask <question>", "Ask Claude (no memory)"),
                    ("!chat <message>", "Chat with memory"),
                    ("!clearchat", "Clear chat memory"),
                    ("!summarize <text>", "Summarize text"),
                    ("!roast [@user]", "Roast someone"),
                    ("!compliment [@user]", "Compliment someone"),
                    ("!translate <lang> <text>", "Translate via AI"),
                ]
            },
            "settings": {
                "title": "⚙️ Settings",
                "commands": [
                    ("!setlogchannel #channel", "Set mod log channel"),
                    ("!setwelcome #ch <message>", "Set welcome message"),
                    ("!setprefix <prefix>", "Set custom prefix"),
                    ("!autorole add/remove @role", "Auto-role on join"),
                    ("!autoroles", "List auto-roles"),
                    ("!botsettings", "View all settings"),
                ]
            },
        }

        if category and category.lower() in categories:
            cat = categories[category.lower()]
            embed = discord.Embed(title=cat["title"], color=discord.Color.blurple())
            for cmd, desc in cat["commands"]:
                embed.add_field(name=f"`{cmd}`", value=desc, inline=False)
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                title="📖 Help — All-in-One Bot",
                description=(
                    "Use `!help <category>` for details.\n"
                    "Both `!` and `?` prefixes work. Slash commands also available.\n\n"
                    "**Categories:**"
                ),
                color=discord.Color.blurple()
            )
            descs = {
                "mod": "🛡️ Moderation — warn, ban, kick, mute...",
                "utility": "🔧 Utility — serverinfo, polls, embeds...",
                "rr": "🎭 Reaction Roles — self-assignable roles",
                "verify": "✅ Verification — button-based verify",
                "level": "⭐ Leveling — XP, ranks, leaderboard",
                "fun": "🎉 Fun — 8ball, trivia, memes, jokes",
                "ai": "🤖 AI — Claude-powered chat & tools",
                "settings": "⚙️ Settings — configure the bot",
            }
            for key, desc in descs.items():
                embed.add_field(name=f"`!help {key}`", value=desc, inline=False)
            embed.set_footer(text="Replaces: Dyno • MEE6 • Carl-bot • Arcane • iTranslator")
            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Help(bot))
