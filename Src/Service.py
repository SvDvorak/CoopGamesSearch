from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from Game import Game
from datetime import datetime, date
from Scraper import Scraper
from ScrapingThread import ScrapingThread

app = FastAPI()

app.add_middleware(
	CORSMiddleware,
	allow_origins=[
		"https://coopgames.anwilc.com",
		"http://coopgames.anwilc.com",
		"http://localhost:80",  # For local development
		"http://127.0.0.1:80"   # For local development
	],
	allow_credentials=True,
	allow_methods=["GET", "POST"],
	allow_headers=["*"],
)

games_file = "games.json"
allow_manual_scrape = True # If True, allows manual scraping via API endpoint

scraper = Scraper()
scrapingThread = ScrapingThread(scraper, games_file, scrape_interval_hours=12)

# Serve static files (HTML, CSS, JS)
app.mount("/static", StaticFiles(directory="."), name="static")

scrapingThread.load_games()
scrapingThread.start_continuous_scraping()

def is_within_date_range(game, from_date, to_date):
	if not game.release_date:
		return False

	if from_date and game.release_date < from_date:
		return False
	
	if to_date and game.release_date > to_date:
		return False
	
	return True

def validate_date_string(date_str, param_name):
	try:
		return datetime.strptime(date_str, "%Y-%m-%d").date()
	except ValueError:
		raise HTTPException(
			status_code=400, 
			detail=f"Invalid date format for {param_name}. Expected format: YYYY-MM-DD"
		)

def validate_player_count_range(min_players, max_players):
	if min_players < 1 or max_players < 1:
		raise HTTPException(
			status_code=400,
			detail="Player counts must be greater than 0"
		)
	if min_players > max_players:
		raise HTTPException(
			status_code=400,
			detail="min_supported_players cannot be greater than max_supported_players"
		)
	
def validate_date_ranges(from_date, to_date):
	if from_date and to_date and from_date > to_date:
		raise HTTPException(
			status_code=400,
			detail="release_date_from cannot be later than release_date_to"
		)

def validate_pagination(page):
	if page < 1:
		raise HTTPException(
			status_code=400,
			detail="Page number must be greater than 0"
		)

def validate_country_code(country_code):
	# TODO This does not actually validate against a list of countries
	if not country_code or len(country_code) != 2:
		raise HTTPException(
			status_code=400,
			detail="Invalid country code. Must be a 2-letter ISO code."
		)

def ceiling_division(a, b):
	return -(a // -b)

def matches_players(game, min_players, max_players, player_type):
	player_type = player_type.lower()
	if player_type == 'couch':
		return game.couch_players >= min_players and game.couch_players <= max_players
	elif player_type == 'lan':
		return game.lan_players >= min_players and game.lan_players <= max_players
	else:
		return game.online_players >= min_players and game.online_players <= max_players

def matches_tags(game, search_tags):
	if not search_tags:
		return True
	
	if not game.tags:
		return False
	
	game_tags_lower = [tag.lower() for tag in game.tags]
	return all(tag in game_tags_lower for tag in search_tags)

@app.get("/games")
async def get_games(min_supported_players: Optional[int] = 1, 
				   max_supported_players: Optional[int] = 100,
				   player_type: Optional[str] = 'online',								# Couch, lan, online
				   free_games: Optional[bool] = True,
				   unreleased_games: Optional[bool] = True,
				   release_date_from: Optional[str] = '1988-08-20',						# YYYY-MM-DD format
				   release_date_to: Optional[str] = date.today().strftime("%Y-%m-%d"),	# YYYY-MM-DD format
				   weight_rating: Optional[float] = 0.7,								# How much game the rating is taken into account
				   weight_price: Optional[float] = 0.3,									# How much price is taken into account
				   high_price: Optional[float] = 20,									# What an "expensive" game classifies as
				   min_reviews: Optional[int] = 0,										# Minimum number of reviews required
				   tags: Optional[str] = None,											# Pipe-separated list of tags
				   page: Optional[int] = 1,												# Page number (1-based)
				   country_code: Optional[str] = "SE"):									
	
	from_date = validate_date_string(release_date_from, "release_date_from")
	to_date = validate_date_string(release_date_to, "release_date_to")
	
	validate_player_count_range(min_supported_players, max_supported_players)
	validate_date_ranges(from_date, to_date)
	validate_pagination(page)
	validate_country_code(country_code)

	search_tags = []
	if tags:
		search_tags = [tag.strip().lower() for tag in tags.split('|') if tag.strip()]
	
	games = scrapingThread.get_games()
	filtered_games = [game for game in games if
					game.is_listed_in_country(country_code) and
					(matches_players(game, min_supported_players, max_supported_players, player_type) and
					(free_games or game.get_price(country_code) > 0) and
					(unreleased_games or game.is_released) and
					(game.number_of_reviews >= min_reviews) and
					is_within_date_range(game, from_date, to_date) and
					matches_tags(game, search_tags))]

	for game in filtered_games:
		game.compute_score(weight_rating, weight_price, high_price, country_code)
	
	# Sort by score (highest first)
	filtered_games.sort(key=lambda x: x.score, reverse=True)
	
	page_size = 40
	total_pages = ceiling_division(len(filtered_games), page_size)
	start_index = (page - 1) * page_size
	end_index = start_index + page_size
	paginated_games = filtered_games[start_index:end_index]
	
	status = scrapingThread.get_status()
	
	return {
		"games": [game.sendable_dict(country_code) for game in paginated_games],
		"pagination": {
			"total_pages": total_pages,
			"page_size": page_size,
			"total_games": len(filtered_games),
		},
		"scraping_in_progress": status["scraping_in_progress"],
		"last_scrape_hours_ago": status["last_scrape_hours_ago"]
	}

@app.get("/scrape/status")
async def get_scrape_status():
	return scrapingThread.get_status()

if allow_manual_scrape:
	@app.post("/scrape/start")
	async def start_manual_scrape():
		success, message = scrapingThread.manual_scrape()
		
		if not success:
			raise HTTPException(
				status_code=409,
				detail=message
			)
		
		return {
			"message": message,
			"scraping_in_progress": True
		}

@app.get("/logo")
async def serve_logo():
	return FileResponse("Logo.svg")

@app.get("/countries")
async def serve_logo():
	return FileResponse("Countries.json")

@app.get("/")
async def serve_frontend():
	return FileResponse("FilterPage.html")