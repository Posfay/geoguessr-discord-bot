import io
import random
import requests
import discord


class ImageGenerator:
    def __init__(self):
        f = open("img_gen_token.txt", "r")
        self.img_gen_token = f.read()
        f.close()
        f = open("rsw_country_codes.txt", "r")
        self.country_codes = f.read().splitlines()
        f.close()

        self.img_width = "1000"
        self.req_base_url = "https://url-to-screenshot.p.rapidapi.com/get"
        self.req_headers = {
            "Accept": "image/png",
            "X-RapidAPI-Host": "url-to-screenshot.p.rapidapi.com",
            "X-RapidAPI-Key": self.img_gen_token
        }

    def generate_image(self):
        country_code = self.country_codes[random.randint(0, len(self.country_codes) - 1)]

        screenshot_url = f"https://randomstreetview.com/{country_code}#fullscreen"
        req_querystring = {
            "url": screenshot_url,
            "base64": "0",
            "width": self.img_width,
            "allocated_time": "5",
            "mobile": "false",
            "height": "-1"
        }

        response = requests.request("GET", self.req_base_url, headers=self.req_headers, params=req_querystring)
        if country_code == "gb":
            country_code = "uk"
        discord_image_file = discord.File(io.BytesIO(response.content), filename=f"valami.png")
        return country_code, discord_image_file
