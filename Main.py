import os
from dotenv import load_dotenv
import asyncio
import logging
import sqlite3
import asqlite
import time

import twitchio
from twitchio.ext import commands
from twitchio import eventsub

LOGGER: logging.Logger = logging.getLogger("Bot")


class Bot(commands.Bot):
    def __init__(self, *, token_database: asqlite.Pool) -> None:
        self.token_database = token_database

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
        
        self.shout_queue = asyncio.Queue()
        self.shout_task = None
        self.shout_cooldown = 121
        self.last_shout_time = 0

    async def event_ready(self):
        # When the bot is ready
        LOGGER.info("Successfully logged in as: %s", self.bot_id)
        # target = self.create_partialuser(user_id=self.target_id, user_login=self.target_name)
        # await target.send_message(sender=self.bot_id, message='Bot has landed')

    #oauth token portion
    #   setting up the webhooks and adding compontent object
    async def setup_hook(self) -> None:
        await self.add_component(MyComponent(self))

        subscription = eventsub.ChannelRaidSubscription(to_broadcaster_user_id=self.target_id)
        await self.subscribe_websocket(payload=subscription)
        
        subscription = eventsub.ShoutoutCreateSubscription(broadcaster_user_id=self.target_id, moderator_user_id=self.owner_id)
        await self.subscribe_websocket(payload=subscription)
    
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
    
    async def start_shout_timer(self):
        try:
            while True:
                now = time.monotonic()
                time_since_last = now - self.last_shout_time
                
                if time_since_last < self.shout_cooldown:
                    delay = self.shout_cooldown - time_since_last
                    LOGGER.info("Waiting %.1f seconds for cooldown to expire", delay)
                    await asyncio.sleep(delay)
                    LOGGER.info("Cooldown to expired, ready to shout")
                
                raid_payload:twitchio.ChannelRaid = await self.shout_queue.get()
                await self.send_shoutout(raid_payload)
                self.last_shout_time = time.monotonic()
                LOGGER.info("Shouted out %s, cooldown reset.", raid_payload.from_broadcaster.display_name)
        except asyncio.CancelledError:
            LOGGER.info("Shoutout loop cancelled.")
            # Let the loop restart cleanly on next shoutout
            raise
    
    async def send_shoutout(self, payload: twitchio.ChannelRaid):
        await payload.to_broadcaster.send_shoutout(
            to_broadcaster=payload.from_broadcaster.id,
            moderator=self.bot_id,
        )
        # await asyncio.sleep(1)
        # await payload.to_broadcaster.send_message(
        #     sender=self.bot_id,
        #     message="!raiders",
        # )

    
class MyComponent(commands.Component):
    def __init__(self, bot: Bot):
        self.bot = bot
        
    @commands.Component.listener()
    async def event_shoutout_created(self, payload: twitchio.ShoutoutCreate) -> None:
        LOGGER.info("Manual shoutout for %s detected. Resetting timer.", payload.to_broadcaster.display_name)
        self.bot.last_shout_time = time.monotonic()

        # Reset the loop if it's already running
        if self.bot.shout_task and not self.bot.shout_task.done():
            self.bot.shout_task.cancel()

        self.shoutout_task = asyncio.create_task(self.bot.start_shout_timer())
        
    @commands.Component.listener()
    async def event_raid(self, payload: twitchio.ChannelRaid) -> None:
        # Event dispatched when a user gets a raid from the subscription we made above...
        await self.bot.shout_queue.put(payload)  # Add raid to the queue
        if not self.bot.shout_task or self.bot.shout_task.done():
            self.bot.shout_task = asyncio.create_task(self.bot.start_shout_timer())
        LOGGER.info(f"[Raid detected] - {payload.from_broadcaster.display_name} is raiding {payload.to_broadcaster.display_name} with {payload.viewer_count} viewers!")

def main() -> None:
    load_dotenv()
    twitchio.utils.setup_logging(level=logging.INFO)

    async def runner() -> None:
        async with asqlite.create_pool("tokens.db") as tdb, Bot(token_database=tdb) as bot:
            await bot.setup_database()
            await bot.start()

    try:
        asyncio.run(runner())
    except KeyboardInterrupt:
        LOGGER.warning("Shutting down due to KeyboardInterrupt...")


if __name__ == "__main__":
    main()