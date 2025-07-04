import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from Game import Game

class Scraper:
	def __init__(self):
		self.scraping_state = "None"
		self.scraping_start_year = 1988
		self.scraping_end_year = datetime.now().year 
		
		# Scraping configuration
		self.min_supported_players = 2
		self.max_supported_players = 100
		self.country_code = "SE"

	def scrape_games(self, last_scrape_time):
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
			if game.is_delisted:
				count -= 1
				continue
			self.add_rating(game)
			self.add_tags(game)
			i += 1
			time.sleep(2)  # Avoid hitting Steam API too hard

		games = list(filter(lambda x: not x.is_delisted, games))

		return games
	
	def fetch_coop_games(self):
		all_games = []
		if self.last_scrape_time is not None:
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
				print(f"Failed to parse game entry: {e}")
		
		return games
	
	def fetch_all_coop_games(self):
		all_games = []
		for year in range(self.scraping_start_year, self.scraping_end_year + 1):
			yearly = self.get_cooptimus_games_data({"releaseyear": year})
			print(f"Year: {year}, Games found: {len(yearly)}")
			if len(yearly) == 40:
				print("Found more than 40 games, scraping by month...")
				yearly.extend(self.fetch_all_coop_games_for_year(year))
			
			print(f"Total games for {year}: {len(yearly)}")
			all_games.extend(yearly)

		print(len(all_games))
		return all_games
	
	def fetch_all_coop_games_for_year(self, year):
		yearly = []
		for month in range(1, 13):
			monthly = self.get_cooptimus_games_data({"releaseyear": year, "releasemonth": month})
			print(f"Year: {year}, Month: {month}, Games found: {len(monthly)}")
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
		if game.steam_id in invalid_steam_id_mappings:
			game.steam_id = invalid_steam_id_mappings[game.steam_id]
		if game.steam_id in ignored_steam_ids:
			game.is_delisted = True
			return False
		return True

	def add_steam_data(self, game):
		url = f"https://store.steampowered.com/api/appdetails?appids={game.steam_id}&cc={self.country_code}"
		response = self.try_request(url)

		game_response = {}
		try:
			game_response = response.json()[str(game.steam_id)]
			if not game_response["success"]:
				raise Exception("Delisted game")
		except:
			print(f"{game.title} ({game.steam_id}), no data found")
			game.is_delisted = True
			return

		data = game_response["data"]
		game.header_image = data["header_image"]
		game.short_description = data["short_description"]

		try:
			if data["release_date"]["coming_soon"]:
				game.is_released = False
			else:
				game.release_date = datetime.strptime(data["release_date"]["date"], "%d %b, %Y").date()
		except:
			game.is_released = False

		try:
			game.price = data["price_overview"]["final"]
		except:
			game.price = 0

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
		response = self.try_request(f"https://steamspy.com/api.php?request=appdetails&appid={game.steam_id}")
		data = response.json()
		try:
			game.tags = list(data.get("tags", {}).keys())
		except:
			return
		
	def try_request(self, url, params=None, retries=15):
		for attempt in range(retries):
			try:
				response = requests.get(url, params=params)
				response.raise_for_status()
				return response
			except requests.RequestException as e:
				print(f"Request failed ({attempt + 1}/{retries}): {e}")
				time.sleep(2 ** attempt)
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