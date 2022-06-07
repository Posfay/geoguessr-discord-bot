import os
import aiohttp
from dotenv import load_dotenv

load_dotenv()

RAPID_API_KEY = os.getenv('RAPID_API_KEY')


class AsyncURLToSSApi:
    def __init__(self):
        self.session = aiohttp.ClientSession()
        self.base_url = "https://url-to-screenshot.p.rapidapi.com/get"
        self.headers = {
            "Accept": "image/png",
            "X-RapidAPI-Host": "url-to-screenshot.p.rapidapi.com",
            "X-RapidAPI-Key": RAPID_API_KEY
        }

    def get_params(self, screenshot_url, width=1000, timeout=5):
        params = {
            "url": screenshot_url,
            "base64": "0",
            "width": width,
            "allocated_time": f"{timeout}",
            "mobile": "false",
            "height": "-1"
        }
        return params

    def get_base_url(self):
        return self.base_url

    def get_headers(self):
        return self.headers

    async def send_request(self, screenshot_url, width=1000, timeout=5):
        async with self.session.get(
            self.get_base_url(),
            headers=self.get_headers(),
            params=self.get_params(screenshot_url, width, timeout)
        ) as response:
            image_data = await response.content.read()
            return image_data
