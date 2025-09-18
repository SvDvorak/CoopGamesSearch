import requests
import time
from bs4 import BeautifulSoup
from datetime import datetime
from Database import Database, GameCountryData
from Game import Game
from Price import Price
from GameStorage import load_countries_from_file
from dprint import dprint

class Scraper:
	def __init__(self, database: Database):
		self.database = database
		self.scraping_state = "None"
		self.scraping_start_year = 1988
		self.scraping_end_year = datetime.now().year 
		self.country_codes = load_countries_from_file("../Countries.json")
		self.steam_delay = 2  # Delay between Steam API requests

	async def scrape_games(self, last_scrape_time: float):
		self.last_scrape_time = last_scrape_time
		self.scraping_state = "Finding games"
		games = self.fetch_coop_games()
		games = self.remove_duplicates(games)

		count = len(games)
		i = 1
		for game in games:
			self.scraping_state = f"Getting Steam data ({i}/{count})"
			if not self.validate_steam_id(game):
				count -= 1
				continue
			self.add_steam_data(game)
			if game.is_removed:
				count -= 1
				continue
			self.add_rating(game)
			self.add_tags(game)
			i += 1
			await self.database.save_game(game)
			# We're hitting steam twice with both details and ratings
			time.sleep(self.steam_delay * 2)

		return await self.database.get_total_games_count(), count
	
	def fetch_coop_games(self):
		all_games = []
		if self.last_scrape_time is None:
			all_games = self.fetch_all_coop_games()
		else:
			all_games = self.fetch_updated_since_last()

		games = []
		for game in all_games:
			try:
				if not game.find("steam"):
					continue

				g = Game()
				g.title = game.find("title").text
				g.steam_id = game.find("steam").text
				g.couch_players = int(game.find("local").text or 0)
				g.lan_players = int(game.find("lan").text or 0)
				g.online_players = int(game.find("online").text or 0)
				g.cooptimus_url = game.find("url").text
				g.steam_url = f"https://store.steampowered.com/app/{g.steam_id}"

				games.append(g)
			except Exception as e:
				dprint(f"Failed to parse game entry: {e}")
		
		return games
	
	def fetch_all_coop_games(self):
		all_games = []
		for year in range(self.scraping_start_year, self.scraping_end_year + 1):
			yearly = self.get_cooptimus_games_data({"releaseyear": year})
			dprint(f"Year: {year}, Games found: {len(yearly)}")
			if len(yearly) == 40:
				dprint("Found more than 40 games, scraping by month...")
				yearly.extend(self.fetch_all_coop_games_for_year(year))
			
			dprint(f"Total games for {year}: {len(yearly)}")
			all_games.extend(yearly)

		dprint(f"Found {len(all_games)} games")
		return all_games
	
	def fetch_all_coop_games_for_year(self, year):
		yearly = []
		for month in range(1, 13):
			monthly = self.get_cooptimus_games_data({"releaseyear": year, "releasemonth": month})
			dprint(f"Year: {year}, Month: {month}, Games found: {len(monthly)}")
			yearly.extend(monthly)
		return yearly
	
	def fetch_updated_since_last(self):
		#return self.get_cooptimus_games_data({"updatedsince": self.last_scrape_time.strftime('%Y-%m-%dT%H:%M:%S')})
		return self.fetch_all_coop_games_for_year(datetime.now().year)

	def get_cooptimus_games_data(self, params):
		url = "https://api.co-optimus.com/games.php"
		params["search"] = "true"
		params["systemName"] = "pc"
		r = self.try_request(url, params=params)

		root = BeautifulSoup(r.content, "lxml-xml")
		return root.find_all("game")

	def remove_duplicates(self, games):
		seen_steam_ids = set()
		return list(filter(lambda game: game.steam_id not in seen_steam_ids and not seen_steam_ids.add(game.steam_id), games))
	
	def validate_steam_id(self, game):
		if game.steam_id in self.invalid_steam_id_mappings:
			game.steam_id = self.invalid_steam_id_mappings[game.steam_id]
		if game.steam_id in self.ignored_steam_ids:
			game.is_removed = True
			return False
		return True

	def add_steam_data(self, game):
		url = f"https://store.steampowered.com/api/appdetails"
		params = {"appids": game.steam_id}
		response = self.try_request(url, params)

		game_response = {}
		try:
			game_response = response.json()[str(game.steam_id)]
			if not game_response["success"]:
				raise Exception("Removed game")
		except:
			dprint(f"{game.title} ({game.steam_id}), no data found")
			game.is_removed = True
			return

		data = game_response["data"]
		game.header_image = data["header_image"]
		game.short_description = data["short_description"]
		game.is_removed = False

		try:
			if data["release_date"]["coming_soon"]:
				game.is_released = False
			else:
				game.release_date = datetime.strptime(data["release_date"]["date"], "%d %b, %Y").date()
		except:
			game.is_released = False

	def add_rating(self, game):
		url = f"https://store.steampowered.com/appreviews/{game.steam_id}"
		params = {"json": 1, "num_per_page": 1, "language": "all", "purchase_type": "all"}
		r = self.try_request(url, params=params).json()
		q = r.get("query_summary", {})
		game.number_of_reviews = q.get("total_reviews")
		if game.number_of_reviews == 0:
			game.steam_rating = 0
		else:
			game.steam_rating = q.get("total_positive") / game.number_of_reviews

	def add_tags(self, game):
		"""Add tags to game via SteamSpy"""
		params = {"request": "appdetails", "appid": game.steam_id}
		response = self.try_request(f"https://steamspy.com/api.php", params=params)
		data = response.json()
		try:
			game.tags = list(data.get("tags", {}).keys())
		except:
			return

	async def scrape_country_data(self):
		steam_ids = await self.database.get_all_steam_ids()
		batch_size = 200

		dprint(f"Fetching country data (prices, delistings) for {len(steam_ids)} games")
		for i in range(0, len(steam_ids), batch_size):
			self.scraping_state = f"Getting prices ({i}/{len(steam_ids)})"
			batch = steam_ids[i:i+batch_size]
			steam_ids_str = ",".join([str(steam_id) for steam_id in batch])

			countries_data: dict[int, GameCountryData] = {}
			for steam_id in batch:
				countries_data[steam_id] = GameCountryData()

			for country in self.country_codes:
				url = f"https://store.steampowered.com/api/appdetails"
				params = {"appids": steam_ids_str, "cc": country.code, "filters": "price_overview"}
				game_data = self.try_request(url, params=params).json()

				for steam_id in batch:
					game_response = game_data[str(steam_id)]
					
					if not game_response.get("success", False):
						# If we can't get the game at all, assume it's delisted in this country
						countries_data[steam_id].delist(country.code)
						continue
					
					# TODO remove, never happens
					if "data" not in game_response:
						dprint(f"!!!!! No data field for steam id {steam_id} in {country.code}")
						continue

					data = game_response["data"]

					if "price_overview" not in data:
						continue

					price_info = data["price_overview"]
					price = Price(price_info["initial"], price_info["final"])
					countries_data[steam_id].add_price(country.code, price)

				time.sleep(self.steam_delay)

			await self.database.save_country_data(countries_data)
		
	def try_request(self, url, params=None, retries=15):
		for attempt in range(retries):
			try:
				response = requests.get(url, params=params)
				response.raise_for_status()
				return response
			except requests.RequestException as e:
				dprint(f"Request failed ({attempt + 1}/{retries}): {e}")
				time.sleep(self.steam_delay ** attempt)
		raise Exception(f"Failed to fetch {url} after {retries} attempts")

	invalid_steam_id_mappings = {
		"8110": "8100",
		"12799": "12790",
		"10199": "1962660",
		"12819": "12810",
		"48129": "965320",
		"22700": "225640",
		"8989": "8980",
		"12219": "12210",
		"1259": "1250",
		"206940": "321800",
		"42749": "42700",
		"271290": "705040",
		"212180": "1263550",
		"22359": "22350",
		"362003": "3240220",
		"41010": "41014",
		"32690": "32770",
		"21019": "21010",
		"35709": "35700",
		"11202": "11200",
		"204140": "209360",
	}

	ignored_steam_ids = {
		"38209",
		"23100",
		"33420",
		"235760",
		"240380",
		"10530",
		"20590",
		"463680",
		"206950",
		"9930",
		"1501980",
		"32700",
		"21649",
		"1368440",
		"9990",
	}