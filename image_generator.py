import random

from url_screenshot_apis import AsyncURLToSSApi


class ImageGenerator:
    def __init__(self):
        f = open("rsw_country_codes.txt", "r")
        self.country_codes = f.read().splitlines()
        f.close()
        self.img_width = 1000

        self.url_to_ss_api = AsyncURLToSSApi()

    async def generate_image(self):
        country_code = self.country_codes[random.randint(0, len(self.country_codes) - 1)]

        screenshot_url = f"https://randomstreetview.com/{country_code}#fullscreen"

        image = await self.url_to_ss_api.send_request(screenshot_url, self.img_width, 6)

        if country_code == "gb":
            country_code = "uk"

        return country_code, image
