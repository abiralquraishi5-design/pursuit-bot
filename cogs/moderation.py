"""
cogs/moderation.py
Replaces: Dyno, MEE6 moderation features.

Prefix commands: !warn / ?warn  (also slash)
"""

import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timezone
from database import (
    add_warning, get_warnings, clear_warnings, remove_warning,
    add_tempban
)
from utils import ordinal, parse_duration, format_duration, mod_embed, log_action

class Moderation(commands.Cog):
    """🛡️ Moderation — warn, ban, kick, mute, and more."""

    def __init__(self, bot):
        self.bot = bot

    # ── WARN ──────────────────────────────────────────────────────────────────

    async def _warn(self, guild, moderator, member: discord.Member, reason: str):
        await add_warning(guild.id, member.id, moderator.id, reason)
        warnings = await get_warnings(guild.id, member.id)
        count = len(warnings)
        ordinal_str = ordinal(count)
        return count, ordinal_str

    @commands.command(name="warn")
    @commands.has_permissions(moderate_members=True)
    async def warn_prefix(self, ctx, member: discord.Member, *, reason: str = "No reason provided"):
        """Warn a member. Usage: !warn @user [reason]"""
        count, ordinal_str = await self._warn(ctx.guild, ctx.author, member, reason)
        msg = f"⚠️ **{member.name}** has been warned. This is their **{ordinal_str}** warning. Reason: {reason}"
        await ctx.send(msg)
        embed = mod_embed(
            discord.Color.yellow(), "⚠️ Member Warned",
            member=str(member), moderator=str(ctx.author),
            warning_count=str(count), reason=reason
        )
        await log_action(self.bot, ctx.guild, embed)
        # Try to DM the user
        try:
            await member.send(
                f"You were warned in **{ctx.guild.name}**.\n"
                f"This is your **{ordinal_str}** warning.\nReason: {reason}"
            )
        except discord.Forbidden:
            pass

    @app_commands.command(name="warn", description="Warn a member")
    @app_commands.describe(member="Member to warn", reason="Reason for the warning")
    @app_commands.default_permissions(moderate_members=True)
    async def warn_slash(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        count, ordinal_str = await self._warn(interaction.guild, interaction.user, member, reason)
        msg = f"⚠️ **{member.name}** has been warned. This is their **{ordinal_str}** warning. Reason: {reason}"
        await interaction.response.send_message(msg)
        embed = mod_embed(
            discord.Color.yellow(), "⚠️ Member Warned",
            member=str(member), moderator=str(interaction.user),
            warning_count=str(count), reason=reason
        )
        await log_action(self.bot, interaction.guild, embed)

    @commands.command(name="warnings")
    @commands.has_permissions(moderate_members=True)
    async def warnings_prefix(self, ctx, member: discord.Member):
        """View warnings for a member. Usage: !warnings @user"""
        await self._show_warnings(ctx, member)

    @app_commands.command(name="warnings", description="View warnings for a member")
    @app_commands.default_permissions(moderate_members=True)
    async def warnings_slash(self, interaction: discord.Interaction, member: discord.Member):
        await self._show_warnings(interaction, member)

    async def _show_warnings(self, ctx_or_interaction, member: discord.Member):
        guild = ctx_or_interaction.guild if hasattr(ctx_or_interaction, "guild") else ctx_or_interaction.guild
        warnings = await get_warnings(guild.id, member.id)
        if not warnings:
            text = f"✅ **{member.name}** has no warnings."
        else:
            lines = [f"**{member.name}** has **{len(warnings)}** warning(s):\n"]
            for i, (wid, mod_id, reason, ts) in enumerate(warnings, 1):
                lines.append(f"`#{wid}` — {ordinal(i)} warning | Reason: {reason} | <t:{int(datetime.fromisoformat(ts).timestamp())}:R>")
            text = "\n".join(lines)
        if hasattr(ctx_or_interaction, "send"):
            await ctx_or_interaction.send(text)
        else:
            await ctx_or_interaction.response.send_message(text)

    @commands.command(name="clearwarnings")
    @commands.has_permissions(moderate_members=True)
    async def clear_warnings_prefix(self, ctx, member: discord.Member):
        """Clear all warnings for a member. Usage: !clearwarnings @user"""
        await clear_warnings(ctx.guild.id, member.id)
        await ctx.send(f"✅ Cleared all warnings for **{member.name}**.")

    @commands.command(name="delwarn")
    @commands.has_permissions(moderate_members=True)
    async def del_warn_prefix(self, ctx, warning_id: int):
        """Delete a specific warning by ID. Usage: !delwarn <id>"""
        await remove_warning(warning_id)
        await ctx.send(f"✅ Warning `#{warning_id}` removed.")

    # ── BAN ───────────────────────────────────────────────────────────────────

    async def _ban(self, guild, moderator, member: discord.Member, reason: str, duration_str: str = None):
        td = parse_duration(duration_str) if duration_str else None
        if td:
            from datetime import timezone
            unban_at = datetime.now(timezone.utc) + td
            await add_tempban(guild.id, member.id, unban_at)
            dur_text = format_duration(td)
            msg = f"🔨 **{member.name}** has been banned. Duration: {dur_text}. Reason: {reason}"
        else:
            msg = f"🔨 **{member.name}** has been banned indefinitely. Reason: {reason}"
        try:
            await member.send(
                f"You were banned from **{guild.name}**.\n"
                + (f"Duration: {format_duration(td)}\n" if td else "Duration: Indefinite\n")
                + f"Reason: {reason}"
            )
        except discord.Forbidden:
            pass
        await member.ban(reason=reason, delete_message_days=0)
        return msg

    @commands.command(name="ban")
    @commands.has_permissions(ban_members=True)
    async def ban_prefix(self, ctx, member: discord.Member, *, args: str = ""):
        """
        Ban a member, optionally with a duration.
        Usage: !ban @user [reason]
               !ban @user 1d 6h reason here
        """
        td = parse_duration(args)
        if td:
            # Try to split duration tokens from reason
            import re
            dur_part = " ".join(re.findall(r"\d+\s*[dhms]", args, re.I))
            reason = re.sub(r"(\d+\s*[dhms]\s*)+", "", args, flags=re.I).strip() or "No reason provided"
        else:
            dur_part = None
            reason = args or "No reason provided"
        msg = await self._ban(ctx.guild, ctx.author, member, reason, dur_part)
        await ctx.send(msg)
        embed = mod_embed(
            discord.Color.red(), "🔨 Member Banned",
            member=str(member), moderator=str(ctx.author),
            duration=format_duration(parse_duration(dur_part)) if dur_part and parse_duration(dur_part) else "Indefinite",
            reason=reason
        )
        await log_action(self.bot, ctx.guild, embed)

    @app_commands.command(name="ban", description="Ban a member")
    @app_commands.describe(member="Member to ban", duration="Optional duration e.g. 1d 6h 30m", reason="Reason for ban")
    @app_commands.default_permissions(ban_members=True)
    async def ban_slash(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided", duration: str = None):
        await interaction.response.defer()
        msg = await self._ban(interaction.guild, interaction.user, member, reason, duration)
        await interaction.followup.send(msg)

    @commands.command(name="unban")
    @commands.has_permissions(ban_members=True)
    async def unban_prefix(self, ctx, user_id: int, *, reason: str = "Manual unban"):
        """Unban a user by ID. Usage: !unban <user_id>"""
        user = await self.bot.fetch_user(user_id)
        await ctx.guild.unban(user, reason=reason)
        await ctx.send(f"✅ **{user}** has been unbanned.")

    # ── KICK ──────────────────────────────────────────────────────────────────

    async def _kick(self, guild, moderator, member: discord.Member, reason: str):
        try:
            await member.send(f"You were kicked from **{guild.name}**.\nReason: {reason}")
        except discord.Forbidden:
            pass
        await member.kick(reason=reason)
        return f"👢 **{member.name}** has been kicked. Reason: {reason}"

    @commands.command(name="kick")
    @commands.has_permissions(kick_members=True)
    async def kick_prefix(self, ctx, member: discord.Member, *, reason: str = "No reason provided"):
        """Kick a member. Usage: !kick @user [reason]"""
        msg = await self._kick(ctx.guild, ctx.author, member, reason)
        await ctx.send(msg)
        embed = mod_embed(
            discord.Color.orange(), "👢 Member Kicked",
            member=str(member), moderator=str(ctx.author), reason=reason
        )
        await log_action(self.bot, ctx.guild, embed)

    @app_commands.command(name="kick", description="Kick a member")
    @app_commands.describe(member="Member to kick", reason="Reason for kick")
    @app_commands.default_permissions(kick_members=True)
    async def kick_slash(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        await interaction.response.defer()
        msg = await self._kick(interaction.guild, interaction.user, member, reason)
        await interaction.followup.send(msg)

    # ── MUTE (timeout) ────────────────────────────────────────────────────────

    @commands.command(name="mute")
    @commands.has_permissions(moderate_members=True)
    async def mute_prefix(self, ctx, member: discord.Member, duration: str = "10m", *, reason: str = "No reason provided"):
        """Timeout a member. Usage: !mute @user [duration] [reason]  e.g. !mute @user 1h spamming"""
        td = parse_duration(duration)
        if not td:
            return await ctx.send("❌ Invalid duration. Examples: `10m`, `1h`, `1d`")
        from datetime import timezone
        await member.timeout(td, reason=reason)
        await ctx.send(f"🔇 **{member.name}** has been muted for **{format_duration(td)}**. Reason: {reason}")

    @commands.command(name="unmute")
    @commands.has_permissions(moderate_members=True)
    async def unmute_prefix(self, ctx, member: discord.Member):
        """Remove timeout from a member. Usage: !unmute @user"""
        await member.timeout(None)
        await ctx.send(f"🔊 **{member.name}** has been unmuted.")

    # ── CLEAR ─────────────────────────────────────────────────────────────────

    @commands.command(name="clear", aliases=["purge"])
    @commands.has_permissions(manage_messages=True)
    async def clear_prefix(self, ctx, amount: int = 10):
        """Delete messages. Usage: !clear [amount]"""
        await ctx.channel.purge(limit=amount + 1)
        m = await ctx.send(f"🧹 Cleared **{amount}** message(s).")
        await m.delete(delay=4)

    @app_commands.command(name="clear", description="Delete messages from this channel")
    @app_commands.describe(amount="Number of messages to delete (default 10)")
    @app_commands.default_permissions(manage_messages=True)
    async def clear_slash(self, interaction: discord.Interaction, amount: int = 10):
        await interaction.response.defer(ephemeral=True)
        await interaction.channel.purge(limit=amount)
        await interaction.followup.send(f"🧹 Cleared **{amount}** message(s).", ephemeral=True)

    # ── ROLE MANAGEMENT ───────────────────────────────────────────────────────

    @commands.command(name="addrole")
    @commands.has_permissions(manage_roles=True)
    async def addrole_prefix(self, ctx, member: discord.Member, role: discord.Role):
        """Add a role to a member. Usage: !addrole @user @role"""
        await member.add_roles(role)
        await ctx.send(f"✅ Added **{role.name}** to **{member.name}**.")

    @commands.command(name="removerole")
    @commands.has_permissions(manage_roles=True)
    async def removerole_prefix(self, ctx, member: discord.Member, role: discord.Role):
        """Remove a role from a member. Usage: !removerole @user @role"""
        await member.remove_roles(role)
        await ctx.send(f"✅ Removed **{role.name}** from **{member.name}**.")

    # ── SLOWMODE ──────────────────────────────────────────────────────────────

    @commands.command(name="slowmode")
    @commands.has_permissions(manage_channels=True)
    async def slowmode_prefix(self, ctx, seconds: int = 0):
        """Set slowmode. Usage: !slowmode [seconds] (0 to disable)"""
        await ctx.channel.edit(slowmode_delay=seconds)
        if seconds == 0:
            await ctx.send("✅ Slowmode disabled.")
        else:
            await ctx.send(f"✅ Slowmode set to **{seconds}** second(s).")

    # ── LOCK / UNLOCK ─────────────────────────────────────────────────────────

    @commands.command(name="lock")
    @commands.has_permissions(manage_channels=True)
    async def lock_prefix(self, ctx):
        """Lock the current channel. Usage: !lock"""
        overwrite = ctx.channel.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = False
        await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        await ctx.send("🔒 Channel locked.")

    @commands.command(name="unlock")
    @commands.has_permissions(manage_channels=True)
    async def unlock_prefix(self, ctx):
        """Unlock the current channel. Usage: !unlock"""
        overwrite = ctx.channel.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = None
        await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        await ctx.send("🔓 Channel unlocked.")

async def setup(bot):
    await bot.add_cog(Moderation(bot))
