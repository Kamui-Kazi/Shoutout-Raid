import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
from dotenv import load_dotenv
import asyncio
# import logging
# import sqlite3
# import asqlite
import pygame
import datetime
import color_scheme

# import twitchio
# from twitchio.ext import commands
# from twitchio import eventsub

SCREEN_WIDTH= color_scheme.SCREEN_WIDTH
SCREEN_HEIGHT= color_scheme.SCREEN_HEIGHT
TEXT_COLOR = color_scheme.TEXT_COLOR
WINDOW_BG = color_scheme.WINDOW_BG
GRID_COLOR = color_scheme.GRID_COLOR

class Connection:
    def __init__(self):
        self.last_raider_name = "None"
        self.last_raider_count = 0
        self.last_raid_time = datetime.datetime.now()

class Interface:
    def __init__(self, connection: Connection):
        self.connection = connection
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Twitch Raid Bot")
        self.font = pygame.font.Font(None, 36)
    
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
            self.screen.fill(color=WINDOW_BG)  # Clear screen

            

            text = self.font.render("Twitch Raid Bot Running...", True, TEXT_COLOR)
            self.screen.blit(text, (50, 50))

            # Draw last raid
            raid_info = f"{self.connection.last_raid_time.strftime("%I:%M%p")} - {self.connection.last_raider_name} just raided with {self.connection.last_raider_count} viewers"
            text = self.font.render(raid_info,True, TEXT_COLOR)
            self.screen.blit(text, (50, 100))

            pygame.display.flip()  # Update screen
            await asyncio.sleep(0.01)  # Yield control to async tasks (replaces tick)

        pygame.quit()
        asyncio.get_event_loop().stop()  # Stop the asyncio loop

def main() -> None:
    load_dotenv()
    dt = datetime.datetime.now()
    print(dt.strftime("%I:%M%p"))

    link = Connection()
    
    async def runner() -> None:
        interface = Interface(connection=link)  # Create the Pygame interface object
        await interface.run(),    # Start Pygame loop (make sure it's an async function!)
    
    asyncio.run(runner())

if __name__ == "__main__":
    
    main()