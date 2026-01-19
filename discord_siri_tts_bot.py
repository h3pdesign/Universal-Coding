import discord
import subprocess
TOKEN = "'$MTQxMjUwMjQzNzUzNjcyNzE5MA.GE9sC4.WVlKbvb9QEeL-RfKKyYsBs3h9GY-tH3YHCWTqw'"
VOICE = "Siri"
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
@client.event
async def on_ready():
    print(f"Bot logged in as {client.user}")
    print("All messages will now be read aloud using Siri.")
@client.event
async def on_message(message):
    try:
        if message.author == client.user:
            return
        text_to_speak = message.content.strip()
        if text_to_speak:
            subprocess.run(["say", "-v", VOICE, text_to_speak])
    except Exception as e:
        print(f"Error reading message: {e}")
try:
    client.run(TOKEN)
except discord.LoginFailure:
    print("Invalid bot token. Check your TOKEN variable!")
