# Co-op Games Docker Application

A web application for finding co-op games to play with support for a specified number of players, ordered based on how cheap and good they are.

## Features

- Filter games by player count & release date
- Customizable scoring weights for rating vs price importance
- Docker containerized for easy deployment

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
- `Service.py` - FastAPI backend server
- `Game.py` - Game model and scoring logic  
- `FilterPage.html` - Vue.js frontend

## API Endpoints

- `GET /` - Serves the main frontend page
- `GET /games` - Returns filtered and scored games

## Environment

- Python 3.11
- FastAPI
- Uvicorn ASGI server
- Vue.js 3 (via CDN)
