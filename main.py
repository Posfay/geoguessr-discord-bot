import os

import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv

from game_state import GameState

load_dotenv()

# Bot Access Token -----------------------------------------------------------------------------------------------------
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
# Bot Access Token -----------------------------------------------------------------------------------------------------

# Logger setup ---------------------------------------------------------------------------------------------------------
logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)
# Logger setup ---------------------------------------------------------------------------------------------------------

# Meta data ------------------------------------------------------------------------------------------------------------
github_url = 'https://github.com/Posfay/geoguessr-discord-bot'
description = f'''GeoGuessr Bot

Guess the country based on an image. The player who guesses right, could either send a picture of their own, or 
let the bot generate the next location.

Follow the project on GitHub: {github_url}'''
# Meta data ------------------------------------------------------------------------------------------------------------


class GuessrBot(commands.Bot):
    def __init__(self, command_prefix, **options):
        super().__init__(command_prefix, **options)
        self.guild_games = {}

    async def on_ready(self):
        print("Bot connected")
        print('Bot username: {0.name}\nID: {0.id}'.format(self.user))

    async def on_message(self, message):
        # Guessing phase
        if message.channel.type != discord.ChannelType.private:
            if message.guild.id in self.guild_games \
                    and self.guild_games[message.guild.id].guess_channel.id == message.channel.id \
                    and self.guild_games[message.guild.id].round_state.active_round:
                await self.guild_games[message.guild.id].handle_guess(message)

        # Waiting for image/country phase
        elif message.channel.type == discord.ChannelType.private:
            for key in self.guild_games:

                # Waiting for image
                if message.author.id == self.guild_games[key].last_winner.id \
                        and self.guild_games[key].waiting_for_image:
                    await self.guild_games[key].handle_waiting_for_image(message)
                    break

                # Waiting for country
                if message.author.id == self.guild_games[key].last_winner.id \
                        and self.guild_games[key].waiting_for_country:
                    await self.guild_games[key].handle_waiting_for_country(message)
                    break

        # Commands
        await self.process_commands(message)


# Bot setup ------------------------------------------------------------------------------------------------------------
intents = discord.Intents.default()
activity = discord.Game(name="GeoGuessin")
bot = GuessrBot(command_prefix='?', activity=activity, description=description, intents=intents, case_insensitive=True)
# Bot setup ------------------------------------------------------------------------------------------------------------


# Bot commands ---------------------------------------------------------------------------------------------------------
@bot.command()
async def channel(ctx):
    if ctx.channel.type != discord.ChannelType.private:
        if ctx.guild.id in bot.guild_games:
            bot.guild_games[ctx.guild.id].set_guess_channel(ctx.channel)
        else:
            bot.guild_games[ctx.guild.id] = GameState()
            bot.guild_games[ctx.guild.id].set_guess_channel(ctx.channel)
    embed = discord.Embed(
        title="Channel",
        description=f"{ctx.channel.mention} set as guessing channel!",
        color=discord.Color.green()
    )
    await ctx.message.channel.send(embed=embed)


@bot.command()
async def image(ctx):
    if ctx.channel.type != discord.ChannelType.private:
        if ctx.guild.id in bot.guild_games and bot.guild_games[ctx.guild.id].guess_channel.id == ctx.channel.id:
            await bot.guild_games[ctx.guild.id].get_image(ctx.message)


@bot.command()
async def helpme(ctx):
    if ctx.channel.type != discord.ChannelType.private:
        if ctx.guild.id in bot.guild_games and bot.guild_games[ctx.guild.id].guess_channel.id == ctx.channel.id:
            await bot.guild_games[ctx.guild.id].handle_help(ctx.message)


@bot.command()
async def guesses(ctx):
    if ctx.channel.type != discord.ChannelType.private:
        if ctx.guild.id in bot.guild_games and bot.guild_games[ctx.guild.id].guess_channel.id == ctx.channel.id:
            await bot.guild_games[ctx.guild.id].get_guesses(ctx.message)


@bot.command()
async def generate(ctx):
    if ctx.channel.type != discord.ChannelType.private:
        if ctx.guild.id in bot.guild_games and bot.guild_games[ctx.guild.id].guess_channel.id == ctx.channel.id:
            embed = discord.Embed(
                title="Generating Random Location",
                description="This might take a couple of seconds...",
                color=discord.Color.dark_blue()
            )
            await bot.guild_games[ctx.guild.id].guess_channel.send(embed=embed)
            await bot.guild_games[ctx.guild.id].generate_image()
# Bot commands ---------------------------------------------------------------------------------------------------------


# Running the bot ------------------------------------------------------------------------------------------------------
bot.run(DISCORD_TOKEN)
# Running the bot ------------------------------------------------------------------------------------------------------
