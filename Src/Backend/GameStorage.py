import json
from Game import Game
from Country import Country

def load_from_file(file_path):
	try:
		with open(file_path, "r", encoding="utf-8") as f:
			data = json.load(f)
		return data
	except FileNotFoundError:
		print(f"\n{file_path} not found. Starting with empty games list.")
		return []
	except Exception as e:
		print(f"\nError loading games from {file_path}: {e}")
		return []

def load_games_from_file(games_file="games.json"):
	data = load_from_file(games_file)
	print(f"\nLoaded {len(data)} games from {games_file}")
	return [Game.from_dict(item) for item in data]

def load_countries_from_file(countries_file="countries.json"):
	data = load_from_file(countries_file)
	return [Country(item["name"], item["code"], item["currency"]) for item in data]