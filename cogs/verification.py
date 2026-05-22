"""
cogs/verification.py
Simple button-based verification system.
"""

import discord
from discord.ext import commands
from discord import app_commands
from database import get_setting, set_setting

class VerifyButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)  # Persistent

    @discord.ui.button(label="✅ Verify", style=discord.ButtonStyle.green, custom_id="verify_button")
    async def verify(self, interaction: discord.Interaction, button: discord.ui.Button):
        role_id = await get_setting(interaction.guild.id, "verify_role")
        if not role_id:
            return await interaction.response.send_message(
                "❌ No verification role set. Ask an admin to run `!setverifyrole @role`.",
                ephemeral=True
            )
        role = interaction.guild.get_role(int(role_id))
        if not role:
            return await interaction.response.send_message("❌ Verification role not found.", ephemeral=True)
        if role in interaction.user.roles:
            return await interaction.response.send_message("✅ You're already verified!", ephemeral=True)
        await interaction.user.add_roles(role, reason="Verification")
        await interaction.response.send_message("✅ You've been verified! Welcome to the server.", ephemeral=True)

class Verification(commands.Cog):
    """✅ Verification — button-based member verification."""

    def __init__(self, bot):
        self.bot = bot
        bot.add_view(VerifyButton())  # Re-register persistent view on restart

    @commands.command(name="setverifyrole")
    @commands.has_permissions(administrator=True)
    async def set_verify_role(self, ctx, role: discord.Role):
        """Set the role given after verification. Usage: !setverifyrole @role"""
        await set_setting(ctx.guild.id, "verify_role", role.id)
        await ctx.send(f"✅ Verification role set to **{role.name}**.")

    @commands.command(name="sendverify")
    @commands.has_permissions(administrator=True)
    async def send_verify(self, ctx, *, message: str = "Click the button below to verify and gain access to the server."):
        """
        Send the verification panel in this channel.
        Usage: !sendverify [custom message]
        """
        embed = discord.Embed(
            title="🔐 Verification",
            description=message,
            color=discord.Color.green()
        )
        embed.set_footer(text=ctx.guild.name)
        await ctx.send(embed=embed, view=VerifyButton())
        await ctx.message.delete()

async def setup(bot):
    await bot.add_cog(Verification(bot))
