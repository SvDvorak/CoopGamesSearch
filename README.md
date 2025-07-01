# Co-op Games Search

A web application for finding co-operative games by player count, price, and Steam ratings. Scrapes game data from Co-Optimus and Steam APIs to build a searchable database of co-op games.

## Features

- Scrapes co-op games from Co-Optimus for 2-100 players
- Integrates Steam data including prices, ratings, descriptions, and tags
- Filter by player count, release date, and scoring preferences
- Customizable weighting between game rating and price
- Automatic game database updates every 4 hours
- Real-time scraping progress monitoring
- Docker containerized

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
python Service.py
```

3. **Access the application**:
Open `http://localhost:8000` in your browser

## API Endpoints

- `GET /` - Serves the main frontend page
- `GET /games` - Returns filtered and scored games

## Technology Stack

- **Backend**: Python 3.11, FastAPI, Uvicorn ASGI server
- **Frontend**: Vue.js 3 (via CDN), HTML5, CSS3
- **Data Processing**: BeautifulSoup4, Requests
- **Containerization**: Docker, Docker Compose
- **Data Storage**: JSON file-based persistence

## Game Scoring Algorithm

Games are scored using a weighted combination of:
- **Steam Rating**: Percentage of positive reviews (0.0-1.0)
- **Price Factor**: Inverse relationship to price (cheaper = higher score)
- **User Weight**: Configurable balance between rating and price importance

Formula: `score = (rating_weight × steam_rating) + ((1 - rating_weight) × price_factor)`

## Notes

- Initial scraping can take 10-15 minutes for the full game database
- Games with invalid Steam IDs are automatically corrected using a mapping table
- Delisted or unavailable games are filtered out during scraping
- The application includes rate limiting to respect Steam API guidelines
