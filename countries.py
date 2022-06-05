import pandas


class RoundStore:
    def __init__(self):
        self.all_countries = pandas.read_csv("countries_regions_list.csv")
        self.guessed_countries = []
        self.correct_country_name = ""
        self.correct_country_alpha2 = ""
        self.correct_country_alpha3 = ""
        self.active_round = False
        self.image = ""
        self.image_file = None

    def reset(self):
        self.guessed_countries = []
        self.correct_country_name = ""
        self.correct_country_alpha2 = ""
        self.correct_country_alpha3 = ""
        self.active_round = False
        self.image = ""
        self.image_file = None

    def get_country(self, country_str):
        name = alpha2 = alpha3 = ""

        if len(country_str) == 2:
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

    def set_image_file(self, img_file):
        self.image_file = img_file

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
