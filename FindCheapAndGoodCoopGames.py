
import argparse
from Scraping import *

parser = argparse.ArgumentParser(description="Co-Op Game Scraper")
parser.add_argument(
	"--mode", 
	choices=["fetch", "generate"], 
	required=True, 
	help="Mode to run: 'fetch' to retrieve game data, 'generate' to calculate scores and generate HTML output"
)
args = parser.parse_args()

if args.mode == "fetch":
	games = find_best_coop_games()
	save_games_to_file(games)
elif args.mode == "generate":
	games = load_games_from_file()
	export_games(games)