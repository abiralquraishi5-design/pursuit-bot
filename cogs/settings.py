"""
cogs/settings.py — Per-server configuration.
"""

import discord
from discord.ext import commands
from database import set_setting, get_setting, add_auto_role, remove_auto_role, get_auto_roles

class Settings(commands.Cog):
    """⚙️ Server Settings — configure the bot for your server."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="setlogchannel")
    @commands.has_permissions(administrator=True)
    async def set_log(self, ctx, channel: discord.TextChannel):
        """Set the moderation log channel. Usage: !setlogchannel #channel"""
        await set_setting(ctx.guild.id, "log_channel", channel.id)
        await ctx.send(f"✅ Log channel set to {channel.mention}.")

    @commands.command(name="setwelcome")
    @commands.has_permissions(administrator=True)
    async def set_welcome(self, ctx, channel: discord.TextChannel, *, message: str):
        """
        Set welcome channel and message.
        Variables: {user} {server} {count}
        Usage: !setwelcome #welcome Welcome {user} to {server}! You are member #{count}.
        """
        await set_setting(ctx.guild.id, "welcome_channel", channel.id)
        await set_setting(ctx.guild.id, "welcome_message", message)
        await ctx.send(f"✅ Welcome message set in {channel.mention}.\nPreview: {message.replace('{user}','@User').replace('{server}',ctx.guild.name).replace('{count}',str(ctx.guild.member_count))}")

    @commands.command(name="setprefix")
    @commands.has_permissions(administrator=True)
    async def set_prefix(self, ctx, prefix: str):
        """Set a custom prefix (! and ? always work). Usage: !setprefix $"""
        if len(prefix) > 3:
            return await ctx.send("❌ Prefix must be 3 characters or fewer.")
        await set_setting(ctx.guild.id, "prefix", prefix)
        await ctx.send(f"✅ Custom prefix set to `{prefix}`. (! and ? still work)")

    @commands.command(name="autorole")
    @commands.has_permissions(administrator=True)
    async def autorole(self, ctx, action: str, role: discord.Role):
        """
        Add or remove an auto-role (given on member join).
        Usage: !autorole add @role
               !autorole remove @role
        """
        action = action.lower()
        if action == "add":
            await add_auto_role(ctx.guild.id, role.id)
            await ctx.send(f"✅ Auto-role added: **{role.name}**")
        elif action == "remove":
            await remove_auto_role(ctx.guild.id, role.id)
            await ctx.send(f"✅ Auto-role removed: **{role.name}**")
        else:
            await ctx.send("❌ Use `add` or `remove`.")

    @commands.command(name="autoroles")
    @commands.has_permissions(administrator=True)
    async def list_autoroles(self, ctx):
        """List all auto-roles. Usage: !autoroles"""
        ids = await get_auto_roles(ctx.guild.id)
        if not ids:
            return await ctx.send("📭 No auto-roles configured.")
        roles = [ctx.guild.get_role(int(r)) for r in ids]
        names = [r.mention for r in roles if r]
        await ctx.send(f"🤖 Auto-roles: {', '.join(names)}")

    @commands.command(name="botsettings")
    @commands.has_permissions(administrator=True)
    async def bot_settings(self, ctx):
        """View current bot settings. Usage: !botsettings"""
        log_id  = await get_setting(ctx.guild.id, "log_channel")
        wch_id  = await get_setting(ctx.guild.id, "welcome_channel")
        wmsg    = await get_setting(ctx.guild.id, "welcome_message")
        prefix  = await get_setting(ctx.guild.id, "prefix") or "!"
        vrole   = await get_setting(ctx.guild.id, "verify_role")
        embed = discord.Embed(title="⚙️ Bot Settings", color=discord.Color.blurple())
        embed.add_field(name="Prefix", value=f"`{prefix}` (and `!`, `?`)", inline=True)
        embed.add_field(name="Log Channel", value=f"<#{log_id}>" if log_id else "Not set", inline=True)
        embed.add_field(name="Welcome Channel", value=f"<#{wch_id}>" if wch_id else "Not set", inline=True)
        embed.add_field(name="Welcome Message", value=wmsg or "Not set", inline=False)
        embed.add_field(name="Verify Role", value=f"<@&{vrole}>" if vrole else "Not set", inline=True)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Settings(bot))
