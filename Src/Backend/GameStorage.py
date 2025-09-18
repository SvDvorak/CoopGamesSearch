import json
from Game import Game
from Country import Country
from dprint import dprint

# TODO Remove all this, since we're using DB
def load_from_file(file_path):
	try:
		with open(file_path, "r", encoding="utf-8") as f:
			data = json.load(f)
		return data
	except FileNotFoundError:
		dprint(f"\n{file_path} not found. Starting with empty games list.")
		return []
	except Exception as e:
		dprint(f"\nError loading games from {file_path}: {e}")
		return []

def load_games_from_file(games_file="games.json"):
	data = load_from_file(games_file)
	dprint(f"\nLoaded {len(data)} games from {games_file}")
	return [Game.from_dict(item) for item in data]

def load_countries_from_file(countries_file="countries.json"):
	data = load_from_file(countries_file)
	return [Country(item["name"], item["code"], item["currency"]) for item in data]

def save_games_to_file(games, games_file="games.json"):
	with open(games_file, "w", encoding="utf-8") as f:
		json.dump([g.to_dict() for g in games], f, ensure_ascii=False, indent=2)
	dprint(f"\nSaved {len(games)} games to {games_file}")

def save_missing_to_file(games, games_file="missing.json"):
	with open(games_file, "w", encoding="utf-8") as f:
		json.dump(games, f, ensure_ascii=False, indent=2)
	dprint(f"\nSaved {len(games)} games to {games_file}")