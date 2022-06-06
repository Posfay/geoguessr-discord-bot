import io
import pandas
import discord
import flag

from image_generator import ImageGenerator

CHECK_MARK = '\N{WHITE HEAVY CHECK MARK}'
CROSS_MARK = '\N{CROSS MARK}'


class RoundState:
    def __init__(self):
        self.all_countries = pandas.read_csv("countries_regions_list.csv")
        self.flag = flag.Flag(prefix_str="", suffix_str="", warn=False)
        self.guessed_countries = []
        self.correct_country_name = ""
        self.correct_country_alpha2 = ""
        self.correct_country_alpha3 = ""
        self.active_round = False
        self.image = ""

    def reset(self):
        self.guessed_countries = []
        self.correct_country_name = ""
        self.correct_country_alpha2 = ""
        self.correct_country_alpha3 = ""
        self.active_round = False
        self.image = ""

    def get_country(self, country_str):
        name = alpha2 = alpha3 = None

        if len(country_str) == 2:
            country_str = self.flag.dflagize(country_str, subregions=False).lower()
            if country_str == "gb":
                country_str = "uk"
            row = self.all_countries.loc[self.all_countries["alpha2"].str.lower() == country_str.lower()]
            if row.empty:
                return None, None, None
            name = row["name"].values[0].lower()
            alpha2 = country_str
            alpha3 = row["alpha3"].values[0].lower()

        elif len(country_str) == 3:
            row = self.all_countries.loc[self.all_countries["alpha3"].str.lower() == country_str.lower()]
            if row.empty:
                return None, None, None
            name = row["name"].values[0].lower()
            alpha2 = row["alpha2"].values[0].lower()
            alpha3 = country_str

        elif len(country_str) > 3:
            row = self.all_countries.loc[self.all_countries["name"].str.lower() == country_str.lower()]
            if row.empty:
                return None, None, None
            name = country_str
            alpha2 = row["alpha2"].values[0].lower()
            alpha3 = row["alpha3"].values[0].lower()

        return name, alpha2, alpha3

    def set_correct_country(self, country):
        self.correct_country_name, self.correct_country_alpha2, self.correct_country_alpha3 = self.get_country(country)
        if self.correct_country_name is None:
            return False
        self.active_round = True
        return True

    def set_image(self, img):
        self.image = img

    def get_guessed_countries(self):
        self.guessed_countries.sort()
        return self.guessed_countries.copy()

    def guess_country(self, country):
        name, alpha2, alpha3 = self.get_country(country)
        if name is None:
            return None

        if name not in self.guessed_countries:
            self.guessed_countries.append(name)

        if alpha2 == self.correct_country_alpha2:
            return True
        else:
            return False


class GameState:
    def __init__(self):
        self.guess_channel = None
        self.round_state = RoundState()
        self.waiting_for_image = False
        self.waiting_for_country = False
        self.winners = []
        self.last_winner = 0
        self.image_generator = ImageGenerator()

    def set_guess_channel_id(self, guess_channel):
        self.guess_channel = guess_channel

    def set_next_round(self):
        self.round_state.reset()
        self.waiting_for_image = False
        self.waiting_for_country = False

    async def get_guesses(self, message):
        guessed_countries_str = str(self.round_state.get_guessed_countries())
        await message.channel.send(guessed_countries_str)

    async def get_image(self, message):
        if self.round_state.image == "":
            await message.channel.send("Meg nincs ervenyes kep")
            return
        await message.channel.send(self.round_state.image)

    async def generate_image(self):
        self.set_next_round()
        country_code, image_buffer_str = await self.image_generator.generate_image()
        self.round_state.set_correct_country(country_code)
        await self.guess_channel.send("Kep generalva")
        image_message = await self.guess_channel.send(file=discord.File(io.BytesIO(image_buffer_str), filename="img.png"))
        image_url = image_message.attachments[0].url
        self.round_state.set_image(image_url)

    async def win_procedure(self, message):
        await message.channel.send(self.round_state.get_guessed_countries())
        await message.channel.send(f"A helyes valasz \"{self.round_state.correct_country_name}\" volt, "
                                   f"{len(self.round_state.get_guessed_countries())} tipp kellett hozza")
        self.set_next_round()

        winner = message.author
        self.last_winner = winner.id
        self.winners.append(winner.id)
        await winner.send("Na gratu, most kuldj egy ujabb kepet, aztan ird le, hogy melyik orszagbol valo! "
                          "Vagy irj valamit (pl. \"ok\"), hogy generaljak egy random kepet!")
        self.waiting_for_image = True

    async def handle_guess(self, message):
        if 2 <= len(message.content) <= 50:
            success = self.round_state.guess_country(message.content)
            if success is None:
                return
            elif success:
                await message.add_reaction(CHECK_MARK)
                await self.win_procedure(message)
            elif not success:
                await message.add_reaction(CROSS_MARK)

    async def handle_waiting_for_image(self, message):
        if len(message.attachments) >= 1:
            self.round_state.set_image(message.attachments[0].url)
            await message.channel.send("Szuper, most johet az orszag")
            self.waiting_for_image = False
            self.waiting_for_country = True
            return
        else:
            await message.channel.send("Random kep generalasa...")
            await self.generate_image()
            self.last_winner = 0
            await message.channel.send("Random kep generalva, nincs mas teendod!")
            return

    async def handle_waiting_for_country(self, message):
        a, b, c = self.round_state.get_country(message.content)
        if a is not None:
            self.round_state.set_correct_country(message.content)
            await message.channel.send("Megvagyunk")
            self.waiting_for_country = False
            self.last_winner = 0

            await self.guess_channel.send(self.round_state.image)
            await self.guess_channel.send(f"Bekuldte: {message.author.mention}")
            return
        else:
            await message.channel.send(f"{message.content} nem ervenyes orszag, kuldj egy masikat")
            return
