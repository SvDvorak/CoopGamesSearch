import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import threading
import time
from Game import Game
from GameStorage import save_games_to_file

class Scraper:
	def __init__(self, games_file, scrape_interval_hours):
		self.games_file = games_file
		self.scrape_interval_hours = scrape_interval_hours
		self.scraping_start_year = 1988
		self.scraping_end_year = datetime.now().year 
		self.scraping_in_progress = False
		self.last_scrape_time = 0
		self.games_lock = threading.RLock()
		self.games = []
		self.continuous_thread = None
		self.scraping_state = "None"
		
		# Scraping configuration
		self.min_supported_players = 2
		self.max_supported_players = 100
		self.country_code = "SE"
	
	def get_games(self):
		"""Get current games list (thread-safe)"""
		with self.games_lock:
			return self.games.copy()
	
	def load_initial_games(self, games):
		self.set_games(games)
		self.last_scrape_time = time.time()

	def set_games(self, new_games):
		"""Set games list (thread-safe)"""
		with self.games_lock:
			self.games = new_games
	
	def get_status(self):
		return {
			"scraping_in_progress": self.scraping_in_progress,
			"scraping_state": self.scraping_state,
			"last_scrape_hours_ago": self.last_scrape_hours_ago() if self.last_scrape_time > 0 else None,
			"scrape_interval_hours": self.scrape_interval_hours,
			"number_of_games": len(self.games) if self.games else 0
		}

	def last_scrape_hours_ago(self):
		return (time.time() - self.last_scrape_time) / 3600 # Convert to hours

	def scrape_games(self):
		self.scraping_state = "Finding games"
		games = self.fetch_coop_games("local")
		
		self.scraping_state = f"Removing duplicates ({len(games)})"
		# Remove duplicates based on steam_id
		seen_steam_ids = set()
		games = list(filter(lambda game: game.steam_id not in seen_steam_ids and not seen_steam_ids.add(game.steam_id), games))

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
			time.sleep(5)  # Avoid hitting Steam API too hard

		games = list(filter(lambda x: not x.is_delisted, games))

		return games
	
	def fetch_coop_games(self, mode):
		all_games = []
		for year in range(self.scraping_start_year, self.scraping_end_year + 1):
			yearly = self.get_cooptimus_games_data({"releaseyear": year})
			print(f"Year: {year}, Games found: {len(yearly)}")
			if len(yearly) == 40:
				print("Found more than 40 games, scraping by month...")
				yearly = []
				for month in range(1, 13):
					monthly = self.get_cooptimus_games_data({"releaseyear": year, "releasemonth": month})
					print(f"Year: {year}, Month: {month}, Games found: {len(monthly)}")
					yearly.extend(monthly)
			
			print(f"Total games for {year}: {len(yearly)}")
			all_games.extend(yearly)

		print(len(all_games))

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

	def get_cooptimus_games_data(self, params):
		url = "https://api.co-optimus.com/games.php"
		params["search"] = "true"
		params["systemName"] = "pc"
		r = requests.get(url, params=params)
		r.raise_for_status()

		root = BeautifulSoup(r.content, "lxml-xml")
		return root.find_all("game")
	
	def validate_steam_id(self, game):
		if game.steam_id in invalid_steam_id_mappings:
			game.steam_id = invalid_steam_id_mappings[game.steam_id]
		if game.steam_id in ignored_steam_ids:
			game.is_delisted = True
			return False
		return True

	def add_steam_data(self, game):
		url = f"https://store.steampowered.com/api/appdetails?appids={game.steam_id}&cc={self.country_code}"
		response = requests.get(url)
		response.raise_for_status()  # Raise error if request failed
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
		r = requests.get(url, params=params).json()
		q = r.get("query_summary", {})
		game.number_of_reviews = q.get("total_reviews")
		if game.number_of_reviews == 0:
			game.steam_rating = 0
		else:
			game.steam_rating = q.get("total_positive") / game.number_of_reviews

	def add_tags(self, game):
		"""Add tags to game via SteamSpy"""
		url = f"https://steamspy.com/api.php?request=appdetails&appid={game.steam_id}"
		response = requests.get(url)
		data = response.json()
		try:
			game.tags = list(data.get("tags", {}).keys())
		except:
			return

	
	def scrape_games_background(self):
		try:
			self.scraping_in_progress = True
			print("\n=== Starting background scraping ===")
			
			# Run the scraping (this takes several minutes)
			new_games = self.scrape_games()
			
			save_games_to_file(new_games, self.games_file)
			
			self.set_games(new_games)
			
			self.last_scrape_time = time.time()
			print(f"\n=== Background scraping completed. Found {len(new_games)} games ===\n")
		finally:
			self.scraping_in_progress = False
			self.scraping_state = "None"

	def continuous_scraping_thread(self):
		print(f"\n=== Starting continuous scraping thread (every {self.scrape_interval_hours} hours) ===\n")
		
		while True:
			try:
				time_since_last = self.last_scrape_hours_ago()
				if not self.scraping_in_progress and time_since_last >= self.scrape_interval_hours:
					self.scrape_games_background()
				
				# Check every 10 minutes
				time.sleep(600)
				
			except Exception as e:
				print(f"\nError in continuous scraping thread: {e}")
				# Wait a bit before retrying
				time.sleep(300)  # 5 minutes
	
	def start_continuous_scraping(self):
		if self.continuous_thread is None or not self.continuous_thread.is_alive():
			self.continuous_thread = threading.Thread(target=self.continuous_scraping_thread, daemon=True)
			self.continuous_thread.start()
	
	def manual_scrape(self):
		if self.scraping_in_progress:
			return False, "Scraping is already in progress"
		
		print("\nManual scraping triggered\n")
		scraping_thread = threading.Thread(target=self.scrape_games_background, daemon=True)
		scraping_thread.start()
		return True, "Scraping started"

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