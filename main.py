import discord
from discord.ext import commands
import logging
from game_state import GameState

# Bot Access Token -----------------------------------------------------------------------------------------------------
f = open("discord_token.txt", "r")
token = f.read()
f.close()
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

Guess the country based on an image. The player, who guesses right, could either send a picture of their own, or 
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
                if message.author.id == self.guild_games[key].last_winner and self.guild_games[key].waiting_for_image:
                    await self.guild_games[key].handle_waiting_for_image(message)
                    break

                # Waiting for country
                if message.author.id == self.guild_games[key].last_winner and self.guild_games[key].waiting_for_country:
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
            bot.guild_games[ctx.guild.id].guess_channel = ctx.channel
        else:
            bot.guild_games[ctx.guild.id] = GameState()
            bot.guild_games[ctx.guild.id].guess_channel = ctx.channel
    await ctx.message.channel.send(f"{ctx.message.channel.mention} beallitva csatornanak")


@bot.command()
async def image(ctx):
    if ctx.channel.type != discord.ChannelType.private:
        if ctx.guild.id in bot.guild_games and bot.guild_games[ctx.guild.id].guess_channel.id == ctx.channel.id:
            await bot.guild_games[ctx.guild.id].get_image(ctx.message)


@bot.command()
async def guesses(ctx):
    if ctx.channel.type != discord.ChannelType.private:
        if ctx.guild.id in bot.guild_games and bot.guild_games[ctx.guild.id].guess_channel.id == ctx.channel.id:
            await bot.guild_games[ctx.guild.id].get_guesses(ctx.message)


@bot.command()
async def generate(ctx):
    if ctx.channel.type != discord.ChannelType.private:
        if ctx.guild.id in bot.guild_games and bot.guild_games[ctx.guild.id].guess_channel.id == ctx.channel.id:
            await ctx.message.channel.send("Random kep generalasa...")
            await bot.guild_games[ctx.guild.id].generate_image()
# Bot commands ---------------------------------------------------------------------------------------------------------


# Running the bot ------------------------------------------------------------------------------------------------------
bot.run(token)
# Running the bot ------------------------------------------------------------------------------------------------------
