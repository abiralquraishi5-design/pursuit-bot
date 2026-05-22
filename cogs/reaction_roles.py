"""
cogs/reaction_roles.py
Replaces: Carl-bot reaction roles.
"""

import discord
from discord.ext import commands
from database import add_reaction_role, get_reaction_role, get_all_reaction_roles, remove_reaction_role

class ReactionRoles(commands.Cog):
    """🎭 Reaction Roles — self-assignable roles via emoji reactions."""

    def __init__(self, bot):
        self.bot = bot

    @commands.group(name="rr", invoke_without_command=True)
    @commands.has_permissions(manage_roles=True)
    async def rr(self, ctx):
        """Reaction role commands. Usage: !rr help"""
        await ctx.send(
            "**Reaction Role Commands:**\n"
            "`!rr add <#channel> <message_id> <emoji> <@role>` — Add a reaction role\n"
            "`!rr remove <message_id> <emoji>` — Remove a reaction role\n"
            "`!rr list` — List all reaction roles"
        )

    @rr.command(name="add")
    @commands.has_permissions(manage_roles=True)
    async def rr_add(self, ctx, channel: discord.TextChannel, message_id: int, emoji: str, role: discord.Role):
        """
        Add a reaction role.
        Usage: !rr add #channel 123456789 🎮 @Gamer
        """
        try:
            message = await channel.fetch_message(message_id)
        except discord.NotFound:
            return await ctx.send("❌ Message not found in that channel.")
        await add_reaction_role(ctx.guild.id, channel.id, message_id, emoji, role.id)
        await message.add_reaction(emoji)
        await ctx.send(f"✅ Reaction role added: {emoji} → **{role.name}** on message `{message_id}`")

    @rr.command(name="remove")
    @commands.has_permissions(manage_roles=True)
    async def rr_remove(self, ctx, message_id: int, emoji: str):
        """
        Remove a reaction role.
        Usage: !rr remove 123456789 🎮
        """
        await remove_reaction_role(ctx.guild.id, message_id, emoji)
        await ctx.send(f"✅ Removed reaction role {emoji} from message `{message_id}`")

    @rr.command(name="list")
    @commands.has_permissions(manage_roles=True)
    async def rr_list(self, ctx):
        """List all reaction roles in this server. Usage: !rr list"""
        entries = await get_all_reaction_roles(ctx.guild.id)
        if not entries:
            return await ctx.send("📭 No reaction roles set up.")
        lines = ["**Reaction Roles:**"]
        for ch_id, msg_id, emoji, role_id in entries:
            role = ctx.guild.get_role(int(role_id))
            role_name = role.name if role else f"Unknown ({role_id})"
            lines.append(f"{emoji} → **{role_name}** | Channel: <#{ch_id}> | Message: `{msg_id}`")
        await ctx.send("\n".join(lines))

    # ── Events ─────────────────────────────────────────────────────────────────

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if payload.user_id == self.bot.user.id:
            return
        role_id = await get_reaction_role(payload.guild_id, payload.message_id, str(payload.emoji))
        if not role_id:
            return
        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return
        member = guild.get_member(payload.user_id)
        role = guild.get_role(int(role_id))
        if member and role:
            try:
                await member.add_roles(role, reason="Reaction role")
            except discord.Forbidden:
                pass

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        if payload.user_id == self.bot.user.id:
            return
        role_id = await get_reaction_role(payload.guild_id, payload.message_id, str(payload.emoji))
        if not role_id:
            return
        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return
        member = guild.get_member(payload.user_id)
        role = guild.get_role(int(role_id))
        if member and role:
            try:
                await member.remove_roles(role, reason="Reaction role removed")
            except discord.Forbidden:
                pass

async def setup(bot):
    await bot.add_cog(ReactionRoles(bot))
