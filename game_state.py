import io
import pandas
import discord
import flag

from image_generator import ImageGenerator

CHECK_MARK = '\N{WHITE HEAVY CHECK MARK}'
CROSS_MARK = '\N{CROSS MARK}'
GUESSES_PAGE_SIZE = 50


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
        self.generated_image = False

    def reset(self):
        self.guessed_countries = []
        self.correct_country_name = ""
        self.correct_country_alpha2 = ""
        self.correct_country_alpha3 = ""
        self.active_round = False
        self.image = ""
        self.generated_image = False

    def get_country(self, country_str):
        name = alpha2 = alpha3 = None

        if len(country_str) == 2:
            country_str = self.flag.dflagize(country_str, subregions=False).lower()
            if country_str == "gb":
                country_str = "uk"
            row = self.all_countries.loc[self.all_countries["alpha2"].str.lower() == country_str.lower()]
            if row.empty:
                return None, None, None
            name = row["name"].values[0]
            alpha2 = row["alpha2"].values[0]
            alpha3 = row["alpha3"].values[0]

        elif len(country_str) == 3:
            row = self.all_countries.loc[self.all_countries["alpha3"].str.lower() == country_str.lower()]
            if row.empty:
                return None, None, None
            name = row["name"].values[0]
            alpha2 = row["alpha2"].values[0]
            alpha3 = row["alpha3"].values[0]

        elif len(country_str) > 3:
            row = self.all_countries.loc[self.all_countries["name"].str.lower() == country_str.lower()]
            if row.empty:
                return None, None, None
            name = row["name"].values[0]
            alpha2 = row["alpha2"].values[0]
            alpha3 = row["alpha3"].values[0]

        return name, alpha2, alpha3

    def set_correct_country(self, country):
        self.correct_country_name, self.correct_country_alpha2, self.correct_country_alpha3 = self.get_country(country)
        if self.correct_country_name is None:
            return False
        self.active_round = True
        return True

    def set_image(self, img):
        self.image = img

    def set_generated_image(self):
        self.generated_image = True

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
        self.last_winner = None
        self.image_generator = ImageGenerator()

    def set_guess_channel_id(self, guess_channel):
        self.guess_channel = guess_channel

    def set_next_round(self):
        self.round_state.reset()
        self.waiting_for_image = False
        self.waiting_for_country = False

    async def get_guesses(self, message):
        guesses_count = len(self.round_state.get_guessed_countries())
        if guesses_count == 0:
            embed = discord.Embed(
                title="Wrong Guesses",
                description="Start guessing! Not much to see here...",
                color=discord.Color.dark_red()
            )
            await message.channel.send(embed=embed)
            return
        embed_count = int(guesses_count / GUESSES_PAGE_SIZE) + 1
        if guesses_count % GUESSES_PAGE_SIZE == 0:
            embed_count -= 1
        for i in range(0, guesses_count, GUESSES_PAGE_SIZE):
            page = "\n\n".join(self.round_state.get_guessed_countries()[i:i + GUESSES_PAGE_SIZE])
            embed = discord.Embed(
                title=f"Wrong Guesses ({int(i/GUESSES_PAGE_SIZE)+1}/{embed_count})",
                description=page,
                color=discord.Color.dark_red()
            )
            embed.set_footer(text=f"Total wrong guesses: {guesses_count}")
            await message.channel.send(embed=embed)

    async def get_image(self, message):
        if self.round_state.image == "":
            embed = discord.Embed(
                title="No Image",
                description="No image has been uploaded or generated yet!",
                color=discord.Color.dark_blue()
            )
            await message.channel.send(embed=embed)
            return
        embed = None
        if self.round_state.generated_image:
            embed = discord.Embed(
                title="Current Image",
                description="The current image was generated by the bot.",
                color=discord.Color.dark_blue()
            )
        else:
            embed = discord.Embed(
                title="Current Image",
                description=f"The current image was sent by {self.last_winner.mention}.",
                color=discord.Color.dark_blue()
            )
        await message.channel.send(embed=embed)
        await message.channel.send(self.round_state.image)

    async def generate_image(self):
        self.set_next_round()
        country_code, image_buffer_str = await self.image_generator.generate_image()
        self.round_state.set_correct_country(country_code)
        embed = discord.Embed(
            title="Current Image",
            description="The current image was generated by the bot.",
            color=discord.Color.dark_blue()
        )
        await self.guess_channel.send(embed=embed)
        image_msg = await self.guess_channel.send(file=discord.File(io.BytesIO(image_buffer_str), filename="img.png"))
        image_url = image_msg.attachments[0].url
        self.round_state.set_image(image_url)

    async def win_procedure(self, message):
        guesses = len(self.round_state.get_guessed_countries())
        guesses_str = f"{guesses} guesses" if guesses > 1 else f"{guesses} guess"
        embed = discord.Embed(
            title="Country Guessed Correctly",
            description=f"Congratulations! {message.author.mention} guessed the correct country, "
                        f"which was **{self.round_state.correct_country_name}**! It took {guesses_str}. \n\n"
                        f"They can either send the bot a new image to be guessed "
                        f"or let it generate a random location.",
            color=discord.Color.green()
        )
        await message.channel.send(embed=embed)
        self.set_next_round()

        self.last_winner = message.author
        self.winners.append(message.author)
        embed = discord.Embed(
            title="Next Image",
            description="Well done on guessing the correct country!\n\n"
                        "You can send your own image to be guessed or let the bot generate a random location.\n\n"
                        "Please send your image and then send the country name (or code) to be guessed.\n\n"
                        "If you don't want to send an image, just type something and the bot will automatically "
                        "generate the next location randomly.",
            color=discord.Color.dark_blue()
        )
        await self.last_winner.send(embed=embed)
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
            embed = discord.Embed(
                title="Image Selected",
                description="The image has been selected. Now please send the country!",
                color=discord.Color.dark_blue()
            )
            await message.channel.send(embed=embed)
            self.waiting_for_image = False
            self.waiting_for_country = True
            return
        else:
            self.round_state.set_generated_image()
            embed = discord.Embed(
                title="Generating Random Location",
                description="This might take a couple of seconds...",
                color=discord.Color.dark_blue()
            )
            await message.channel.send(embed=embed)
            await self.generate_image()
            embed = discord.Embed(
                title="Random Location Generated",
                description="Thank you, everything is set!",
                color=discord.Color.green()
            )
            await message.channel.send(embed=embed)
            return

    async def handle_waiting_for_country(self, message):
        a, b, c = self.round_state.get_country(message.content)
        if a is not None:
            self.waiting_for_country = False
            self.round_state.set_correct_country(message.content)
            embed = discord.Embed(
                title="Image and Country Selected",
                description="Thank you, everything is set!",
                color=discord.Color.green()
            )
            await message.channel.send(embed=embed)

            embed = discord.Embed(
                title="Current Image",
                description=f"The current image was sent by {self.last_winner.mention}.",
                color=discord.Color.dark_blue()
            )
            await self.guess_channel.send(embed=embed)
            await self.guess_channel.send(self.round_state.image)
            return
        else:
            embed = discord.Embed(
                title="Invalid Country",
                description=f"{message.content} is not a valid country or country code, please try again!",
                color=discord.Color.dark_red()
            )
            await message.channel.send(embed=embed)
            return
