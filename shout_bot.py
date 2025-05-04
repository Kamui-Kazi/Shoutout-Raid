import os
import logging
import sqlite3
import asqlite

import twitchio
from twitchio.ext import commands
from twitchio import eventsub

LOGGER: logging.Logger = logging.getLogger("Shout Bot")

class ShoutBot(commands.Bot):
    def __init__(self, *, token_database: asqlite.Pool, auth_mode:bool = False) -> None:
        self.token_database = token_database
        self.auth_mode:bool = auth_mode

        self.owner_name=os.environ['OWNER_NAME']
        self.bot_name=os.environ['BOT_NAME']
        self.target_id=os.environ['TARGET_ID']
        self.target_name=os.environ['TARGET_NAME']
        
        super().__init__(
            client_id=os.environ['CLIENT_ID'],
            client_secret=os.environ['CLIENT_SECRET'],
            bot_id=os.environ['BOT_ID'],
            owner_id=os.environ['OWNER_ID'],
            prefix=os.environ['BOT_PREFIX'],
        )
        
    async def event_ready(self): # When the bot is ready
        LOGGER.info("Successfully logged in as: %s(%s)", self.bot_name, self.bot_id)

    #oauth token portion
    async def setup_hook(self) -> None:
        # Add our component which contains our commands...
        await self.add_component(ShoutComponent(self))

        if not self.auth_mode:
            # Subscribe to raid events (EventSub)
            subscription = eventsub.ChannelRaidSubscription(to_broadcaster_user_id=self.target_id)
            await self.subscribe_websocket(payload=subscription)
            
        else:
            # This is the first run, so skip EventSub subscription and mark it as completed
            LOGGER.info("First run — skipping EventSub subscription")
            LOGGER.info("visit this link with both accounts to authenticate this program: http://localhost:4343/oauth?scopes=channel:bot%20user:read:chat%20user:write:chat%20user:bot%20moderator:manage:shoutouts")
            async with self.token_database.acquire() as connection:
                await connection.execute(
                    """CREATE TABLE IF NOT EXISTS tokens(user_id TEXT PRIMARY KEY, token TEXT NOT NULL, refresh TEXT NOT NULL)"""
                )
    
    #   adds tokens from localhost:433
    async def add_token(self, token: str, refresh: str) -> twitchio.authentication.ValidateTokenPayload:
        # Make sure to call super() as it will add the tokens interally and return us some data...
        resp: twitchio.authentication.ValidateTokenPayload = await super().add_token(token, refresh)

        # Store our tokens in a simple SQLite Database when they are authorized...
        query = """
        INSERT INTO tokens (user_id, token, refresh)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id)
        DO UPDATE SET
            token = excluded.token,
            refresh = excluded.refresh;
        """

        async with self.token_database.acquire() as connection:
            await connection.execute(query, (resp.user_id, token, refresh))

        LOGGER.info("Added token to the database for user: %s", resp.user_id)
        return resp

    #   loads tokens from database
    async def load_tokens(self, path: str | None = None) -> None:
        # We don't need to call this manually, it is called in .login() from .start() internally...

        async with self.token_database.acquire() as connection:
            rows: list[sqlite3.Row] = await connection.fetchall("""SELECT * from tokens""")

        for row in rows:
            await self.add_token(row["token"], row["refresh"])

    #   sets the structure of the token database
    async def setup_database(self) -> None:
        # Create our token table, if it doesn't exist..
        query = """CREATE TABLE IF NOT EXISTS tokens(user_id TEXT PRIMARY KEY, token TEXT NOT NULL, refresh TEXT NOT NULL)"""
        async with self.token_database.acquire() as connection:
            await connection.execute(query)


class ShoutComponent(commands.Component):
    def __init__(self, bot: ShoutBot):
        self.bot = bot
        
    @commands.Component.listener()
    async def event_raid(self, payload: twitchio.ChannelRaid) -> None:
        # Event dispatched when a user gets a raid from the subscription we made above...
        await payload.to_broadcaster.send_shoutout(
            to_broadcaster=payload.from_broadcaster.id,
            moderator=self.bot.bot_id,
        )
        LOGGER.info(f"[Raid detected] - {payload.from_broadcaster.display_name} is raiding {payload.to_broadcaster.display_name} with {payload.viewer_count} viewers!")

