import json
from Game import Game

def load_games_from_file(games_file="games.json"):
	"""Load games from JSON file"""
	try:
		with open(games_file, "r", encoding="utf-8") as f:
			data = json.load(f)
		print(f"\nLoaded {len(data)} games from {games_file}")
		return [Game.from_dict(item) for item in data]
	except FileNotFoundError:
		print(f"\n{games_file} not found. Starting with empty games list.")
		return []
	except Exception as e:
		print(f"\nError loading games from {games_file}: {e}")
		return []

def save_games_to_file(games, games_file="games.json"):
	"""Save games to JSON file"""
	with open(games_file, "w", encoding="utf-8") as f:
		json.dump([g.to_dict() for g in games], f, ensure_ascii=False, indent=2)
	print(f"\nSaved {len(games)} games to {games_file}")
