import os
from dotenv import load_dotenv
import asyncio
import logging
import sqlite3
import asqlite
import pygame
import datetime
import pygame_scheme
from fake_objects import FakeChannelRaid

import twitchio
from twitchio.ext import commands
from twitchio import eventsub

LOGGER: logging.Logger = logging.getLogger("Bot")

SCREEN_WIDTH= pygame_scheme.SCREEN_WIDTH
SCREEN_HEIGHT= pygame_scheme.SCREEN_HEIGHT
TEXT_COLOR = pygame_scheme.TEXT_COLOR
WINDOW_BG = pygame_scheme.WINDOW_BG
GRID_COLOR = pygame_scheme.GRID_COLOR

class Connection:
    def __init__(self):
        self.raids = [FakeChannelRaid()] * 5
        self.bot_name = "None"
        self.bot_status = False
        self.channel_name = "None"


class Bot(commands.Bot):
    def __init__(self, connection: Connection, *, token_database: asqlite.Pool) -> None:
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
        
        self.connection = connection
        self.connection.bot_name = self.bot_name
        self.connection.channel_name = self.target_name

    async def event_ready(self):
        # When the bot is ready
        self.connection.bot_status = True
        LOGGER.info("Successfully logged in as: %s", self.bot_id)
        # target = self.create_partialuser(user_id=self.target_id, user_login=self.target_name)
        # await target.send_message(sender=self.bot_id, message='Bot has landed')

    #oauth token portion
    #   setting up the webhooks and adding compontent object
    async def setup_hook(self) -> None:
        # Add our component which contains our commands...
        await self.add_component(MyComponent(self))

        # Subscribe and listen to when a stream gets a raid..
        # For this example listen to our target's stream...
        subscription = eventsub.ChannelRaidSubscription(to_broadcaster_user_id=self.target_id)
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


class MyComponent(commands.Component):
    def __init__(self, bot: Bot):
        self.bot = bot
        
    @commands.Component.listener()
    async def event_raid(self, payload: twitchio.ChannelRaid) -> None:
        # Event dispatched when a user gets a raid from the subscription we made above...
        await payload.to_broadcaster.send_shoutout(
            to_broadcaster=payload.from_broadcaster.id,
            moderator=self.bot.bot_id,
        )
        # await asyncio.sleep(1)
        # await payload.to_broadcaster.send_message(
        #     sender=self.bot_id,
        #     message="!raiders",
        # )
        self.bot.connection.raids.pop()
        self.bot.connection.raids.insert(0, payload)
        LOGGER.info(f"[Raid detected] - {payload.from_broadcaster.display_name} is raiding {payload.to_broadcaster.display_name} with {payload.viewer_count} viewers!")


class Interface:
    def __init__(self, connection: Connection):
        self.connection = connection
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Twitch Raid Bot")
        self.font = pygame.font.Font(None, 24)
    
    async def run(self):
        #Runs the Pygame UI in an async loop.
        clock = pygame.time.Clock()
        running = True
        while running:
            # Check events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
            #designing interface
            #   Clear screen
            self.screen.fill(color=WINDOW_BG)
            #   Drawing Boxes
            pygame.draw.line(self.screen, GRID_COLOR, (0,0), (500, 0))
            pygame.draw.line(self.screen, GRID_COLOR, (0,24), (500, 24), 3)
            pygame.draw.line(self.screen, GRID_COLOR, (87,0), (87, 23))
            pygame.draw.line(self.screen, GRID_COLOR, (272,0), (272, 23))
            pygame.draw.line(self.screen, GRID_COLOR, (500,0), (500, 23))
            
            #   drawing header text
            match self.connection.bot_status:
                case True:
                    status = "Y"
                case False:
                    status = "N"
            text = self.font.render(f"Running: {status}", True, TEXT_COLOR)
            self.screen.blit(text, (0, 5))
            
            text = self.font.render(f"Bot name: {self.connection.bot_name}", True, TEXT_COLOR)
            self.screen.blit(text, (90, 5))
            
            text = self.font.render(f"Channel name: {self.connection.channel_name}", True, TEXT_COLOR)
            self.screen.blit(text, (275, 5))

            # drawing history of raids
            for i in range(self.connection.raids.__len__()):
                #print(f"{self.connection.raids[i].timestamp} - {self.connection.raids[i].from_broadcaster.name} with {self.connection.raids[i].viewer_count} viewers")
                text = self.font.render(f"{self.connection.raids[i].timestamp} - {self.connection.raids[i].from_broadcaster.name[0]} with {self.connection.raids[i].viewer_count} viewers", True, TEXT_COLOR)
                self.screen.blit(text, (0, 50*(i+1)))
            
            
            

            # text = self.font.render("Twitch Raid Bot Running...", True, TEXT_COLOR)
            # self.screen.blit(text, (50, 50))

            # # Draw last raid
            # raid_info = f"{self.connection.last_raid_time.strftime("%I:%M%p")} - {self.connection.last_raider_name} just raided with {self.connection.last_raider_count} viewers"
            # text = self.font.render(raid_info,True, TEXT_COLOR)
            # self.screen.blit(text, (50, 100))

            pygame.display.flip()  # Update screen
            await asyncio.sleep(0.01)  # Yield control to async tasks (replaces tick)
            
        pygame.quit()
        asyncio.get_event_loop().stop()  # Stop the asyncio loop

def main() -> None:
    load_dotenv()
    twitchio.utils.setup_logging(level=logging.INFO)

    link = Connection()
    
    async def runner() -> None:
        async with asqlite.create_pool("tokens.db") as tdb, Bot(connection=link, token_database=tdb) as bot:
            interface = Interface(connection=link)  # Create the Pygame interface object
            await bot.setup_database()
            
            # Run both Pygame UI and TwitchIO bot together
            await asyncio.gather(
                bot.start(),        # Start Twitch bot
                interface.run(),    # Start Pygame loop (make sure it's an async function!)
            )
    try:
        asyncio.run(runner())
    except KeyboardInterrupt:
        LOGGER.warning("Shutting down due to KeyboardInterrupt...")


if __name__ == "__main__":
    main()