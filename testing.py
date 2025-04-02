import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
from dotenv import load_dotenv
import asyncio
# import logging
# import sqlite3
# import asqlite
import pygame
import datetime
import pygame_scheme

# import twitchio
# from twitchio.ext import commands
# from twitchio import eventsub

SCREEN_WIDTH= pygame_scheme.SCREEN_WIDTH
SCREEN_HEIGHT= pygame_scheme.SCREEN_HEIGHT
TEXT_COLOR = pygame_scheme.TEXT_COLOR
WINDOW_BG = pygame_scheme.WINDOW_BG
GRID_COLOR = pygame_scheme.GRID_COLOR

class Connection:
    def __init__(self):
        self.last_raider_name = "None"
        self.last_raider_count = 0
        self.last_raid_time = datetime.datetime.now()
        self.bot_name = "Kamui_Kazi"
        self.channel_name = "Kamui_Kazi"

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
            match running:
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
    dt = datetime.datetime.now()
    print(dt.strftime("%I:%M%p"))

    link = Connection()
    
    async def runner() -> None:
        interface = Interface(connection=link)  # Create the Pygame interface object
        await interface.run(),    # Start Pygame loop (make sure it's an async function!)
    
    asyncio.run(runner())

if __name__ == "__main__":
    
    main()