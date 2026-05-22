"""
database.py — SQLite manager for the bot.
All persistent data (warnings, reaction roles, settings, etc.) lives here.
"""

import aiosqlite
import os

DB_PATH = os.getenv("DB_PATH", "bot.db")

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript("""
        CREATE TABLE IF NOT EXISTS warnings (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id    TEXT NOT NULL,
            user_id     TEXT NOT NULL,
            moderator   TEXT NOT NULL,
            reason      TEXT NOT NULL,
            timestamp   DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS tempbans (
            guild_id    TEXT NOT NULL,
            user_id     TEXT NOT NULL,
            unban_at    DATETIME NOT NULL,
            PRIMARY KEY (guild_id, user_id)
        );

        CREATE TABLE IF NOT EXISTS reaction_roles (
            guild_id    TEXT NOT NULL,
            channel_id  TEXT NOT NULL,
            message_id  TEXT NOT NULL,
            emoji       TEXT NOT NULL,
            role_id     TEXT NOT NULL,
            PRIMARY KEY (guild_id, message_id, emoji)
        );

        CREATE TABLE IF NOT EXISTS guild_settings (
            guild_id    TEXT PRIMARY KEY,
            prefix      TEXT DEFAULT '!',
            log_channel TEXT,
            mute_role   TEXT,
            verify_role TEXT,
            welcome_channel TEXT,
            welcome_message TEXT
        );

        CREATE TABLE IF NOT EXISTS auto_roles (
            guild_id    TEXT NOT NULL,
            role_id     TEXT NOT NULL,
            PRIMARY KEY (guild_id, role_id)
        );

        CREATE TABLE IF NOT EXISTS user_levels (
            guild_id    TEXT NOT NULL,
            user_id     TEXT NOT NULL,
            xp          INTEGER DEFAULT 0,
            level       INTEGER DEFAULT 0,
            PRIMARY KEY (guild_id, user_id)
        );
        """)
        await db.commit()

# ── Warnings ──────────────────────────────────────────────────────────────────

async def add_warning(guild_id, user_id, moderator, reason):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO warnings (guild_id, user_id, moderator, reason) VALUES (?,?,?,?)",
            (str(guild_id), str(user_id), str(moderator), reason)
        )
        await db.commit()

async def get_warnings(guild_id, user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT id, moderator, reason, timestamp FROM warnings WHERE guild_id=? AND user_id=? ORDER BY timestamp",
            (str(guild_id), str(user_id))
        ) as cur:
            return await cur.fetchall()

async def clear_warnings(guild_id, user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "DELETE FROM warnings WHERE guild_id=? AND user_id=?",
            (str(guild_id), str(user_id))
        )
        await db.commit()

async def remove_warning(warning_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM warnings WHERE id=?", (warning_id,))
        await db.commit()

# ── Temp-bans ─────────────────────────────────────────────────────────────────

async def add_tempban(guild_id, user_id, unban_at):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO tempbans (guild_id, user_id, unban_at) VALUES (?,?,?)",
            (str(guild_id), str(user_id), unban_at.isoformat())
        )
        await db.commit()

async def get_expired_tempbans(now):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT guild_id, user_id FROM tempbans WHERE unban_at <= ?",
            (now.isoformat(),)
        ) as cur:
            return await cur.fetchall()

async def remove_tempban(guild_id, user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "DELETE FROM tempbans WHERE guild_id=? AND user_id=?",
            (str(guild_id), str(user_id))
        )
        await db.commit()

# ── Reaction Roles ─────────────────────────────────────────────────────────────

async def add_reaction_role(guild_id, channel_id, message_id, emoji, role_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO reaction_roles VALUES (?,?,?,?,?)",
            (str(guild_id), str(channel_id), str(message_id), str(emoji), str(role_id))
        )
        await db.commit()

async def get_reaction_role(guild_id, message_id, emoji):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT role_id FROM reaction_roles WHERE guild_id=? AND message_id=? AND emoji=?",
            (str(guild_id), str(message_id), str(emoji))
        ) as cur:
            row = await cur.fetchone()
            return row[0] if row else None

async def get_all_reaction_roles(guild_id):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT channel_id, message_id, emoji, role_id FROM reaction_roles WHERE guild_id=?",
            (str(guild_id),)
        ) as cur:
            return await cur.fetchall()

async def remove_reaction_role(guild_id, message_id, emoji):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "DELETE FROM reaction_roles WHERE guild_id=? AND message_id=? AND emoji=?",
            (str(guild_id), str(message_id), str(emoji))
        )
        await db.commit()

# ── Guild Settings ─────────────────────────────────────────────────────────────

async def get_setting(guild_id, key):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            f"SELECT {key} FROM guild_settings WHERE guild_id=?",
            (str(guild_id),)
        ) as cur:
            row = await cur.fetchone()
            return row[0] if row else None

async def set_setting(guild_id, key, value):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            f"""INSERT INTO guild_settings (guild_id, {key}) VALUES (?, ?)
                ON CONFLICT(guild_id) DO UPDATE SET {key}=excluded.{key}""",
            (str(guild_id), str(value) if value is not None else None)
        )
        await db.commit()

# ── Auto Roles ─────────────────────────────────────────────────────────────────

async def add_auto_role(guild_id, role_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO auto_roles VALUES (?,?)",
            (str(guild_id), str(role_id))
        )
        await db.commit()

async def remove_auto_role(guild_id, role_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "DELETE FROM auto_roles WHERE guild_id=? AND role_id=?",
            (str(guild_id), str(role_id))
        )
        await db.commit()

async def get_auto_roles(guild_id):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT role_id FROM auto_roles WHERE guild_id=?",
            (str(guild_id),)
        ) as cur:
            return [r[0] for r in await cur.fetchall()]

# ── XP / Leveling ──────────────────────────────────────────────────────────────

async def add_xp(guild_id, user_id, amount):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO user_levels (guild_id, user_id, xp) VALUES (?,?,?)
               ON CONFLICT(guild_id, user_id) DO UPDATE SET xp = xp + ?""",
            (str(guild_id), str(user_id), amount, amount)
        )
        await db.commit()

async def get_level_data(guild_id, user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT xp, level FROM user_levels WHERE guild_id=? AND user_id=?",
            (str(guild_id), str(user_id))
        ) as cur:
            row = await cur.fetchone()
            return row if row else (0, 0)

async def set_level(guild_id, user_id, xp, level):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO user_levels (guild_id, user_id, xp, level) VALUES (?,?,?,?)
               ON CONFLICT(guild_id, user_id) DO UPDATE SET xp=?, level=?""",
            (str(guild_id), str(user_id), xp, level, xp, level)
        )
        await db.commit()

async def get_leaderboard(guild_id, limit=10):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT user_id, xp, level FROM user_levels WHERE guild_id=? ORDER BY xp DESC LIMIT ?",
            (str(guild_id), limit)
        ) as cur:
            return await cur.fetchall()
