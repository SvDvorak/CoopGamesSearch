
from Game import *
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# Fetch games with x number of online co‑op players via Co‑Optimus
def fetch_coop_games(players):
	url = "https://api.co-optimus.com/games.php"
	params = {"search": "true", "systemName": "pc", "online_num": f"{players}"}
	r = requests.get(url, params=params)
	r.raise_for_status()  # Raise error if request failed

	root = BeautifulSoup(r.content, "lxml-xml")
	games = []

	for game in root.find_all("game"):
		try:
			if not game.find("steam"):
				continue

			g = Game()
			g.title = game.find("title").text
			g.steam_id = game.find("steam").text
			g.online_players = int(game.find("online").text or 0)
			#"featurelist": game.find("featurelist").text,
			g.cooptimus_url = game.find("url").text
			g.steam_url = f"https://store.steampowered.com/app/{g.steam_id}"
			#"art": game.find("art").text

			games.append(g)
		except Exception as e:
			print(f"Failed to parse game entry: {e}")
	
	return games

def add_steam_data(game):
	url = f"https://store.steampowered.com/api/appdetails?appids={game.steam_id}&cc={country_code}"
	response = requests.get(url).json()
	game_response = {}
	try:
		game_response = response[str(game.steam_id)]
		if not game_response["success"]:
			raise Exception("Delisted game")
	except:
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

def add_rating(game):
	url = f"https://store.steampowered.com/appreviews/{game.steam_id}"
	params = {"json": 1, "num_per_page": 1, "language": "all", "purchase_type": "all"}
	r = requests.get(url, params=params).json()
	q = r.get("query_summary", {})
	game.number_of_reviews = q.get("total_reviews")
	if game.number_of_reviews == 0:
		game.steam_rating = 0
	else:
		game.steam_rating = q.get("total_positive") / game.number_of_reviews

def add_tags(game):
	url = f"https://steamspy.com/api.php?request=appdetails&appid={game.steam_id}"
	response = requests.get(url)
	data = response.json()
	try:
		game.tags = list(data.get("tags", {}).keys())
	except:
		return

def find_best_coop_games():
	games = []
	for i in range(min_supported_players, max_supported_players + 1):
		print(f"\rFinding games with {i} supported players (max search: {max_supported_players})", end="", flush=True)
		games.extend(fetch_coop_games(i))
	print(f"\nFound {len(games)} games")
	
	print("\nFinding Steam metadata, prices & ratings (skipping delisted)")
	count = len(games)
	i = 1
	for game in games:
		add_steam_data(game)
		if game.is_delisted:
			count -= 1
			continue
		add_rating(game)
		add_tags(game)
		print(f"\rProgress: {i}/{count}", end="", flush=True)
		i += 1
	print("\nDone")

	games = list(filter(lambda x: not x.is_delisted, games))

	return games

def save_games_to_file(games):
	with open(games_file, "w", encoding="utf-8") as f:
		json.dump([g.to_dict() for g in games], f, ensure_ascii=False, indent=2)
	print(f"\nSaved {len(games)} games to {games_file}")