# bot.py
import os

import discord
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

client = discord.Client()

@client.event
async def on_ready():
    print(f'{client.user.name} has connected to Discord!')

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    
    await message.author.create_dm()
    await message.author.dm_channel.send(
        f'Hi {message.author.name}, I hope you are having a great day!'
    )

client.run(TOKEN)
