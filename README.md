# Co-op Games Search

A web application for finding co-operative games by player count, price, and Steam ratings. Scrapes game data from Co-Optimus and Steam APIs to build a searchable database of co-op games.

## Features

- Scrapes Co-Optimus for local, LAN & online games
- Integrates Steam data including localized prices, ratings, descriptions, and tags
- Filter by player count, release date, tags, free, unreleased, minimum reviews
- Order games based on Steam rating, price, sale and number of reviews
- Pagination support for large result sets
- Hide uninteresting games
- Re-scrapes new games and all prices every 12 hours (configurable)
- Light/Dark mode support
- Docker container support

## Data Sources

The application combines data from multiple sources:
- **Co-Optimus API**: Co-op game discovery and player counts. 
    - Co-Optimus parameters: https://api.co-optimus.com/games.php?params=true
- **Steam API**: Game details, pricing, descriptions, availability, and user ratings
    - Example getting app details: https://store.steampowered.com/api/appdetails?appids=1466390
    - Example getting multiple app prices for single country: https://store.steampowered.com/api/appdetails?appids=1395030,1466390,631570,553850,1172470&cc=SE&filters=price_overview
- **SteamSpy API**: Game tags and categorization
    - Example getting app tags: https://steamspy.com/api.php?request=appdetails&appid=1466390

## Installation

### Quick Start with Docker Compose

```bash
docker-compose up
```
### Local Development Install

Install dependencies for backend & frontend and starts both (with frontend watching for changes)
```bash
sh Run-dev.sh
```

### Access the application:
Open your browser and navigate to `http://localhost`

## Development

The application consists of:
- FastAPI backend server with REST API endpoints
- Game scraping engine with background threading starting scraping every 12 hours
- SQLite database persistance
- Vue.js 3 frontend with responsive UI

## Notes

- Manually triggered scraping can be turned off by setting allow_manual_scrape to False in Service.py
- Initial scraping (runs first when scraping first time after startup) will take several hours for the full game database.
- Fully delisted or unavailable games are filtered out during scraping. Regionally delisted games will still show for those regions.
- Some games on Co-optimus has old/wrong Steam IDs, so we map them correct ones.
- Scraping is rate limited by delaying Steam calls by a few seconds for each game, so we don't trigger 429 Too Many Requests.
- If you're going to host it yourself, do make sure to edit the CORS origins in Service.py

## Game Scoring Algorithm

Games are scored using a weighted combination of:
- **Steam rating**: Percentage of positive reviews on an exponential scale (0.0 to 1.0) (higher = higher score)
- **Price**: Price of the game (cheaper = higher score)
- **Sale**: Sale percentage game has (0.0 to 1.0) (higher = higher score)
- **Number of reviews**: Number of reviews calculated on a logarithmic scale where 100000 reviews is considered very high (-1.0 to 1.0) (higher = more reviews is better)
- **User defined 'high price'**: What the user considers to be an expensive game; higher value gives less penalty for expensive games.

Formula: `score = (steam_rating ^ 2) * rating_weight + (price / high_price) * price_weight + (1.0 - current_price / base_price) * sale_weight + (LOG(number_of_reviews + 1) / LOG(100000)) * number_of_reviews_weight`

## API Endpoints

- `GET /` - Serves the main frontend page
- `GET /logo` - The appicon logo
- `GET /countries` - JSON file with countries (country codes, names and currency)
- `GET /games` - Returns filtered and scored games. Parameters:
    - `min_supported_players` (int: Min players for player_type)
    - `max_supported_players` (int: Max players for player_type)
    - `player_type` (string: Couch, LAN or Online for min/max_supported_players)
    - `free_games` (bool: Should include free games)
    - `unreleased_games` (bool: Should include unreleased games)
    - `release_date_from` (string: YYYY-MM-DD format)
    - `release_date_to` (string: YYYY-MM-DD format)
    - `min_reviews` (int: Require games to have this many reviews)
    - `tags` (string: Pipe-separated list of tags that games must have)
    - `rating_weight` (float: How much game the rating is taken into account)
    - `price_weight` (float: How much price is taken into account)
    - `sale_weight` (float: How much sale is taken into account)
    - `number_of_reviews_weight` (float: How much number of reviews is taken into account)
    - `high_price` (float: What an "expensive" game classifies as)
    - `next_index` (int: First index of expected returned games, used for pagination)
    - `country_code` (string: Two letter ISO 3166 country code, used for figuring out prices and delistings)
- `GET /scrape/status")` - Returns current state of scraping
- `POST /scrape/start")` - Triggers a new scraping. This endpoint can be disabled by changing allow_manual_scrape in Service.py 

## Technology Stack

- **Backend**: Python 3.11, FastAPI, Uvicorn ASGI server
- **Frontend**: Vue.js 3, HTML5, CSS3
- **Data Processing**: BeautifulSoup4, Requests
- **Data Storage**: SQLite3 persistence
- **Containerization**: Docker, Docker Compose