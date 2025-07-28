from contextlib import asynccontextmanager
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, date
from Scraper import Scraper
from ScrapingThread import ScrapingThread
from Database import Database, Filters, Pagination, Scoring

allow_manual_scrape = True # If True, allows manual scraping via API endpoint

database = Database()
scraper = Scraper(database)
scrapingThread = ScrapingThread(scraper, scrape_interval_hours=12)

@asynccontextmanager
async def lifespan(app: FastAPI):
	await database.init_database()
	scrapingThread.start_continuous_scraping()
	yield

app = FastAPI(lifespan=lifespan)

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

# Serve static files (HTML, CSS, JS)
app.mount("/static", StaticFiles(directory="."), name="static")

def validate_date_string(date_str, param_name) -> date:
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

def validate_pagination(next_index):
	if next_index < 0:
		raise HTTPException(
			status_code=400,
			detail="Next index number must be greater or equal to 0"
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

@app.get("/games")
async def get_games(min_supported_players: Optional[int] = 1, 
				   max_supported_players: Optional[int] = 100,
				   player_type: Optional[str] = 'online',								# Couch, lan, online
				   free_games: Optional[bool] = True,
				   unreleased_games: Optional[bool] = True,
				   release_date_from: Optional[str] = '1988-08-20',						# YYYY-MM-DD format
				   release_date_to: Optional[str] = date.today().strftime("%Y-%m-%d"),	# YYYY-MM-DD format
				   min_reviews: Optional[int] = 0,										# Minimum number of reviews required
				   tags: Optional[str] = None,											# Pipe-separated list of tags
				   rating_weight: Optional[float] = 0.7,								# How much game the rating is taken into account
				   price_weight: Optional[float] = 0.3,									# How much price is taken into account
				   sale_weight: Optional[float] = 0.0,									# How much sale is taken into account
				   number_of_reviews_weight: Optional[float] = 0.0,						# How much number of reviews is taken into account
				   high_price: Optional[float] = 20,									# What an "expensive" game classifies as
				   next_index: Optional[int] = 0,										# Index of the first game in the response, used for pagination
				   country_code: Optional[str] = "SE"):									
	
	from_date = validate_date_string(release_date_from, "release_date_from")
	to_date = validate_date_string(release_date_to, "release_date_to")
	
	validate_player_count_range(min_supported_players, max_supported_players)
	validate_date_ranges(from_date, to_date)
	validate_pagination(next_index)
	validate_country_code(country_code)

	search_tags = []
	if tags:
		search_tags = [tag.strip().lower() for tag in tags.split('|') if tag.strip()]

	filters = Filters(
		country_code=country_code,
		min_supported_players=min_supported_players,
		max_supported_players=max_supported_players,
		player_type=player_type,
		free_games=free_games,
		unreleased_games=unreleased_games,
		from_date=from_date,
		to_date=to_date,
		min_reviews=min_reviews,
		search_tags=search_tags
	)
    
	scoring = Scoring(
		rating_weight=rating_weight,
		price_weight=price_weight,
		sale_weight=sale_weight,
		number_of_reviews_weight=number_of_reviews_weight,
		high_price=high_price
	)

	max_games_returned = 10
	pagination = Pagination(limit=max_games_returned, offset=next_index)

	games, total_count = await database.get_games(filters, scoring, pagination)
	
	status = scrapingThread.get_status()
	
	return {
		"games": [game.to_dict() for game in games],
		"total_games": total_count,
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
    return FileResponse("../Frontend/Resources/Logo.svg")

@app.get("/countries")
async def serve_countries():
    return FileResponse("../Countries.json")

# Serve built Vue app static assets
app.mount("/assets", StaticFiles(directory="../Frontend/dist/assets"), name="assets")

@app.get("/")
async def serve_frontend():
    return FileResponse("../Frontend/dist/index.html")

# Catch-all route for Vue Router - Enable this when you add routing
@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    # Don't catch API routes
    if full_path.startswith(("games", "countries", "logo", "scrape", "assets")):
        raise HTTPException(status_code=404, detail="Not found")
    return FileResponse("../Frontend/dist/index.html")