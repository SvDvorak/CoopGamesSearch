from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from Game import Game
from datetime import datetime, date
from GameStorage import load_games_from_file
from Scraper import Scraper

app = FastAPI()

# Enable CORS for frontend-backend communication
app.add_middleware(
	CORSMiddleware,
	allow_origins=["*"],  # In production, specify your frontend domain
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)

games_file = "games.json"
allow_manual_scrape = True # If True, allows manual scraping via API endpoint

# Initialize scraper
scraper = Scraper(games_file, scrape_interval_hours=12)

# Serve static files (HTML, CSS, JS)
app.mount("/static", StaticFiles(directory="."), name="static")

# Load games on startup and start continuous scraping
initial_games = load_games_from_file(games_file)
scraper.load_initial_games(initial_games)
scraper.start_continuous_scraping()

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

@app.get("/games")
async def get_games(min_supported_players: Optional[int] = 1, 
				   max_supported_players: Optional[int] = 100,
				   free_games: Optional[bool] = True,
				   unreleased_games: Optional[bool] = True,
				   release_date_from: Optional[str] = '1988-08-20',
				   release_date_to: Optional[str] = date.today().strftime("%Y-%m-%d"),
				   weight_rating: Optional[float] = 0.7,	# How much game the rating is taken into account
				   weight_price: Optional[float] = 0.3,		# How much price is taken into account
				   high_price: Optional[float] = 20):		# What an "expensive" game classifies as
	
	from_date = validate_date_string(release_date_from, "release_date_from")
	to_date = validate_date_string(release_date_to, "release_date_to")

	# Check if min_supported_players is less than max_supported_players
	if min_supported_players > max_supported_players:
		raise HTTPException(
			status_code=400,
			detail="min_supported_players cannot be greater than max_supported_players"
		)
	
	# Check if from_date is after to_date
	if from_date and to_date and from_date > to_date:
		raise HTTPException(
			status_code=400,
			detail="release_date_from cannot be later than release_date_to"
		)
	
	games = scraper.get_games()
	filtered_games = [game for game in games if
					  (game.online_players >= min_supported_players and
					   game.online_players <= max_supported_players and
					   (free_games or game.price > 0) and
					   (unreleased_games or game.is_released) and
					   is_within_date_range(game, from_date, to_date))]

	for game in filtered_games:
		game.compute_score(weight_rating, weight_price, high_price)
	
	# Sort by score (highest first)
	filtered_games.sort(key=lambda x: x.score, reverse=True)
	
	# Get scraping status
	status = scraper.get_status()
	
	return {
		"games": [game.to_dict() for game in filtered_games],
		"scraping_in_progress": status["scraping_in_progress"],
		"last_scrape_hours_ago": status["last_scrape_hours_ago"]
	}

@app.get("/scrape/status")
async def get_scrape_status():
	"""Get current scraping status"""
	return scraper.get_status()

if allow_manual_scrape:
	@app.post("/scrape/start")
	async def start_manual_scrape():
		"""Manually trigger a scraping operation"""
		success, message = scraper.manual_scrape()
		
		if not success:
			raise HTTPException(
				status_code=409,
				detail=message
			)
		
		return {
			"message": message,
			"scraping_in_progress": True
		}

@app.get("/logo.svg")
async def serve_logo():
	return FileResponse("Logo.svg")

@app.get("/")
async def serve_frontend():
	return FileResponse("FilterPage.html")