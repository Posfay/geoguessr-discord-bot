import random
import discord
from discord.ext import commands
import logging
import countries
from countries import RoundStore

# Bot Access Token -----------------------------------------------------------------------------------------------------
f = open("token.txt", "r")
token = f.read()
# Bot Access Token -----------------------------------------------------------------------------------------------------

# Logger setup ---------------------------------------------------------------------------------------------------------
logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)
# Logger setup ---------------------------------------------------------------------------------------------------------

description = '''GeoGuessr Bot

Guess the country based on an image. The player, who guesses right, could either send a picture of their own, or 
let the bot generate the next location.'''

intents = discord.Intents.default()


class ReactContext(commands.Context):
    async def tick(self, value):
        emoji = '\N{WHITE HEAVY CHECK MARK}' if value else '\N{CROSS MARK}'
        try:
            await self.message.add_reaction(emoji)
        except discord.HTTPException:
            pass


class GuessrBot(commands.Bot):
    def __init__(self, command_prefix, **options):
        super().__init__(command_prefix, **options)
        self.guess_channel_id = 0
        self.round_store = RoundStore()
        self.waiting_for_image = False
        self.waiting_for_country = False
        self.last_winner_id = 0
        self.CHECK_MARK = '\N{WHITE HEAVY CHECK MARK}'
        self.CROSS_MARK = '\N{CROSS MARK}'

    def set_guess_channel_id(self, channel_id):
        self.guess_channel_id = channel_id

    def set_next_round(self):
        self.round_store.reset()

    async def on_ready(self):
        print("Bot connected")
        print('Bot username: {0.name}\nID: {0.id}'.format(self.user))

    async def get_context(self, message, *, cls=ReactContext):
        return await super().get_context(message, cls=cls)

    async def win_procedure(self, prev_message):
        await prev_message.channel.send(self.round_store.get_guessed_countries())
        await prev_message.channel.send(f"{len(self.round_store.get_guessed_countries())} tipp kellett hozza")
        self.set_next_round()

        winner = prev_message.author
        self.last_winner_id = winner.id
        await winner.send("Na gratu, most kuldj egy ujabb kepet, aztan ird le, hogy melyik orszagbol valo!")
        self.waiting_for_image = True

    # async def on_message(self, message):
    #     if len(message.attachments) >= 1:
    #         url = message.attachments[0].url
    #         await message.channel.send(url)
    #
    #     await self.process_commands(message)

    async def on_message(self, message):
        if self.waiting_for_image and message.author.id == self.last_winner_id:
            self.round_store.set_image(message.attachments[0].url)
            await message.channel.send("Szuper, most johet az orszag")
            self.waiting_for_image = False
            self.waiting_for_country = True
            return

        if self.waiting_for_country and message.author.id == self.last_winner_id:
            self.round_store.set_correct_country(message.content)
            await message.channel.send("Megvagyunk")
            self.waiting_for_country = False

            guess_channel = self.get_channel(self.guess_channel_id)
            await guess_channel.send(self.round_store.image)
            winner = message.author
            await guess_channel.send(f"Bekuldte: {winner.mention}")
            return

        if message.channel.id == self.guess_channel_id and self.round_store.active_round:
            if 2 <= len(message.content) <= 50:
                success = self.round_store.guess_country(message.content)
                if success is None:
                    pass
                elif success:
                    await message.add_reaction(self.CHECK_MARK)
                    await self.win_procedure(message)
                elif not success:
                    await message.add_reaction(self.CROSS_MARK)

        await self.process_commands(message)


bot = GuessrBot(command_prefix='?', description=description, intents=intents, case_insensitive=True)


@bot.command()
async def channel(ctx):
    bot.set_guess_channel_id(ctx.message.channel.id)
    await ctx.message.channel.send(f"{ctx.message.channel.name} beallitva csatornanak")


@bot.command()
async def image(ctx):
    if bot.round_store.image == "":
        await ctx.message.channel.send("Meg nincs ervenyes kep")
    await ctx.message.channel.send(bot.round_store.image)


@bot.command()
async def setcountry(ctx, country):
    bot.set_next_round()
    valid_country = bot.round_store.set_correct_country(country)
    if valid_country:
        await ctx.message.channel.send(f"{bot.round_store.correct_country_name} beallitva megoldasnak")
    else:
        await ctx.message.channel.send(f"\"{country}\" nem ervenyes orszag")

bot.run(token)
