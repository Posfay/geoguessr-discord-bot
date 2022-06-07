import io
import random
import numpy as np
from PIL import Image

from url_screenshot_apis import AsyncURLToSSApi


class ImageGenerator:
    def __init__(self):
        f = open("rsw_country_codes.txt", "r")
        self.country_codes = f.read().splitlines()
        f.close()
        self.img_width = 1000

        self.url_to_ss_api = AsyncURLToSSApi()

    def check_image_black(self, image_data):
        image = Image.open(io.BytesIO(image_data))
        img_arr = np.array(image)
        img_arr = img_arr[:, :, 0]
        img_arr = img_arr < 10
        return np.sum(img_arr) > img_arr.size * 0.8

    async def generate_one_image(self):
        country_code = self.country_codes[random.randint(0, len(self.country_codes) - 1)]

        screenshot_url = f"https://randomstreetview.com/{country_code}#fullscreen"

        image_data = await self.url_to_ss_api.send_request(screenshot_url, self.img_width, 6)

        if country_code == "gb":
            country_code = "uk"

        return country_code, image_data

    async def generate_image(self):
        country_code, image_data = await self.generate_one_image()

        while self.check_image_black(image_data):
            print("black image")
            country_code, image_data = await self.generate_one_image()

        return country_code, image_data
