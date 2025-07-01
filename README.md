# Co-op Games Search

A web application for finding co-operative games by player count, price, and Steam ratings. Scrapes game data from Co-Optimus and Steam APIs to build a searchable database of co-op games.

## Features

- Scrapes Co-Optimus for local, LAN & online games
- Integrates Steam data including prices, ratings, descriptions, and tags
- Filter by player count, release date, and scoring preferences
- Customizable weighting between game rating and price
- Re-scrapes games every 4 hours
- Scraping progress monitoring
- Docker container support

## Data Sources

The application combines data from multiple sources:
- **Co-Optimus API**: Co-op game discovery and player counts
- **Steam API**: Game details, pricing, descriptions, availability, and user ratings
- **SteamSpy API**: Game tags and categorization

## Quick Start with Docker

### Build the Docker image:
```bash
docker build -t coop-games-app .
```

### Run the container:
```bash
docker run -p 8000:8000 coop-games-app
```

### Access the application:
Open your browser and navigate to `http://localhost:8000`

## Docker Compose (Alternative)

If you prefer using Docker Compose:

```bash
docker-compose up
```

## Development

The application consists of:
- **`Service.py`** - FastAPI backend server with REST API endpoints
- **`Scraper.py`** - Game scraping engine with background threading
- **`GameStorage.py`** - JSON-based game data persistence layer
- **`Game.py`** - Game model with scoring algorithms and data validation
- **`FilterPage.html`** - Vue.js 3 frontend with responsive UI

### Local Development

1. **Install dependencies**:
```bash
pip install -r requirements.txt
```

2. **Run the application**:
```bash
uvicorn Service:app --host 0.0.0.0 --port 8000
```

3. **Access the application**:
Open `http://localhost:8000` in your browser

## Notes

- Initial scraping can take 10-20 minutes for the full game database.
- Delisted or unavailable games are filtered out during scraping
- Some games on Co-optimus has the wrong Steam IDs so we manually map them to correct ones.
- The application includes rate limiting by delaying Steam calls by a few seconds for each game, so we don't trigger 429 Too Many Requests.

## Game Scoring Algorithm

Games are scored using a weighted combination of:
- **Steam rating**: Percentage of positive reviews (0.0-1.0) (higher = higher score)
- **Price**: Price of the game (cheaper = higher score)
- **User weight**: Configurable balance between rating and price importance
- **User defined 'high price'**: What the user considers to be an expensive game; higher value gives less penalty for expensive games.

Formula: `score = (steam_rating ^ 2 × rating_weight) - (price / high_price × (1 - rating_weight))`

## API Endpoints

- `GET /` - Serves the main frontend page
- `GET /logo.svg` - The appicon logo
- `GET /games` - Returns filtered and scored games
- `GET /scrape/status")` - Returns current state of scraping
- `POST /scrape/start")` - Triggers a new scraping. This endpoint can be disabled by changing allow_manual_scrape in Service.py 

## Technology Stack

- **Backend**: Python 3.11, FastAPI, Uvicorn ASGI server
- **Frontend**: Vue.js 3 (via CDN), HTML5, CSS3
- **Data Processing**: BeautifulSoup4, Requests
- **Containerization**: Docker, Docker Compose
- **Data Storage**: JSON file persistence