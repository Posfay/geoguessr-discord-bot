import requests


class URLToSSApi:
    def __init__(self):
        f = open("img_gen_token.txt", "r")
        self.img_gen_token = f.read()
        f.close()

        self.base_url = "https://url-to-screenshot.p.rapidapi.com/get"
        self.headers = {
            "Accept": "image/png",
            "X-RapidAPI-Host": "url-to-screenshot.p.rapidapi.com",
            "X-RapidAPI-Key": self.img_gen_token
        }

    def get_querystring(self, screenshot_url, width=1000, timeout=5):
        req_querystring = {
            "url": screenshot_url,
            "base64": "0",
            "width": width,
            "allocated_time": f"{timeout}",
            "mobile": "false",
            "height": "-1"
        }
        return req_querystring

    def get_base_url(self):
        return self.base_url

    def get_headers(self):
        return self.headers

    def send_request(self, screenshot_url, width=1000, timeout=5):
        req_querystring = self.get_querystring(screenshot_url, width, timeout)
        response = requests.request(
            "GET",
            self.get_base_url(),
            headers=self.get_headers(),
            params=req_querystring
        )
        return response
