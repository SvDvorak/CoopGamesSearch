import asyncio
import json
import aiosqlite
from Price import Price
from os import listdir
from os.path import isfile, join
from datetime import date, datetime
from Game import Game

class Filters:
    def __init__(self,
                 country_code: str,
                 min_supported_players: int,
                 max_supported_players: int, 
                 player_type: str,
                 free_games: bool,
                 unreleased_games: bool,
                 from_date: date, 
                 to_date: date,
                 min_reviews: int,
                 search_tags: list[str]):
        self.country_code = country_code
        self.min_supported_players = min_supported_players
        self.max_supported_players = max_supported_players
        self.player_type = player_type
        self.free_games = free_games
        self.unreleased_games = unreleased_games
        self.from_date = from_date
        self.to_date = to_date
        self.min_reviews = min_reviews
        self.search_tags = search_tags

class Scoring:
    def __init__(self,
                 rating_weight: float,
                 price_weight: float,
                 sale_weight: float, 
                 number_of_reviews_weight: float,
                 high_price: float):
        self.rating_weight = rating_weight
        self.price_weight = price_weight
        self.sale_weight = sale_weight
        self.number_of_reviews_weight = number_of_reviews_weight
        self.high_price = high_price

class Pagination:
    def __init__(self,
                 limit: int,
                 offset: int):
        self.limit = limit
        self.offset = offset

class GameCountryData:
    def __init__(self):
        self.prices: dict[str, Price] = { }      # Prices for each country (country code)
        self.delisted: set[str] = set()          # Countries game is delisted in (country code)

    def delist(self, country_code: str):
        self.delisted.add(country_code)

    def add_price(self, country_code: str, price: Price):
        self.prices[country_code] = price

class Database:
    migrationsFolder = "Migrations"

    def __init__(self, db_path: str = "games.db"):
        self.db_path = db_path

    async def _connect(self) -> aiosqlite.Connection:
        return await aiosqlite.connect(self.db_path)

    async def init_database(self):
        conn = await self._connect()
        await self.run_migrations(conn)
        await conn.commit()
        await conn.close()
    
    async def run_migrations(self, conn):
        cursor = await conn.cursor()
        await cursor.execute("PRAGMA user_version")
        version = (await cursor.fetchone())[0]
        migration_files = self.get_migration_files(version)
        running_version = version
        for file in migration_files:
            running_version = file["version"]
            try:
                with open(join(self.migrationsFolder, file["file_name"]), 'r') as f:
                    sql = f.read()
                    # Extract the UP section
                    up_section = sql.split('-- Up')[1].split('-- Down')[0]
                    await conn.executescript(up_section)
                    await conn.commit()
                version = running_version
                print(f"Ran migration {version:03d}")
            except Exception as e:
                print(f"ERROR! Unable to run migration {running_version:03d}: {e}")
        await cursor.execute("PRAGMA user_version = {v:d}".format(v=version))
    
    def get_migration_files(self, version: int) -> list:
        files = [{ "file_name": f, "version": int(f[:3])} for f in listdir(self.migrationsFolder) if isfile(join(self.migrationsFolder, f))]
        files = filter(lambda x: x["version"] > version, files)
        return sorted(files, key=lambda x: x["version"])

    async def get_games(self,
        filters: Filters,
        scoring: Scoring,
        pagination: Pagination
    ) -> list[Game]:
        conn = await self._connect()
        conn.row_factory = aiosqlite.Row

        cursor = await conn.cursor()

        where_conditions = []
        params = []
        # Delisted
        where_conditions.append("""
            g.steam_id NOT IN (SELECT steam_id FROM GameDelisted WHERE country_code = ?)
        """)
        params.append(filters.country_code)
        
        # Player count
        if filters.player_type.lower() == 'couch':
            where_conditions.append("g.couch_players BETWEEN ? AND ?")
        elif filters.player_type.lower() == 'lan':
            where_conditions.append("g.lan_players BETWEEN ? AND ?")
        else:  # online
            where_conditions.append("g.online_players BETWEEN ? AND ?")
        params.extend([filters.min_supported_players, filters.max_supported_players])

        if not filters.free_games:
            where_conditions.append("""
                EXISTS (SELECT 1 FROM GamePrice gp WHERE gp.steam_id = g.steam_id 
                        AND gp.country_code = ? AND gp.final_price > 0)
            """)
            params.append(filters.country_code)

        if not filters.unreleased_games:
            where_conditions.append("g.is_released = 1")

        if filters.min_reviews > 0:
            where_conditions.append("g.number_of_reviews >= ?")
            params.append(filters.min_reviews)

        if filters.search_tags:
            for tag in filters.search_tags:
                where_conditions.append("g.tags LIKE ?")
                params.append(f'%"{tag.lower()}"%')
        
        if filters.from_date:
            where_conditions.append("g.release_date >= ?")
            params.append(filters.from_date.strftime("%Y-%m-%d"))
        if filters.to_date:
            where_conditions.append("g.release_date <= ?")
            params.append(filters.to_date.strftime("%Y-%m-%d"))
        
        where_clause = "WHERE " + " AND ".join(where_conditions)

        score_calculation = f"""
            (
                (g.steam_rating * g.steam_rating) * {scoring.rating_weight} +
                -(COALESCE(gp.final_price, 0) / 100.0 / {scoring.high_price}) * {scoring.price_weight} +
                CASE 
                    WHEN COALESCE(gp.initial_price, 0) > 0 
                    THEN (1.0 - CAST(COALESCE(gp.final_price, 0) AS REAL) / COALESCE(gp.initial_price, 1)) * {scoring.sale_weight}
                    ELSE 0 
                END +
                (LOG(g.number_of_reviews + 1) / LOG(100000)) * {scoring.number_of_reviews_weight}
            )
        """

        query = f"""
            SELECT 
                g.*,
                gp.initial_price,
                gp.final_price,
                {score_calculation} as calculated_score,
                COUNT(*) OVER() as total_count
            FROM Game g
            LEFT JOIN GamePrice gp ON g.steam_id = gp.steam_id AND gp.country_code = ?
            {where_clause}
            ORDER BY {score_calculation} DESC
            LIMIT ? OFFSET ?
        """

        # Add country_code for price join as first parameter
        all_params = [filters.country_code] + params + [pagination.limit, pagination.offset]
        await cursor.execute(query, all_params)

        games = []
        total_count = 0

        for row in await cursor.fetchall():
            games.append(self._row_to_game(row))
            total_count = row["total_count"]

        await conn.close()

        return games, total_count

    async def save_games(self, games: list[Game]):
        conn = await self._connect()
        cursor = await conn.cursor()

        for game in games:
            await self.save_game_batch(game, cursor)

        await conn.commit()
        await conn.close()
    
    async def save_game(self, game: Game):
        conn = await self._connect()
        cursor = await conn.cursor()

        await self.save_game_batch(game, cursor)

        await conn.commit()
        await conn.close()

    async def save_game_batch(self, game: Game, cursor: aiosqlite.Cursor):
        await cursor.execute("""
               INSERT INTO Game (
                    title, steam_id, steam_rating, number_of_reviews, release_date,
                    couch_players, lan_players, online_players, cooptimus_url, steam_url,
                    header_image, short_description, tags, is_released, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(steam_id) DO UPDATE SET
                    title = excluded.title,
                    steam_rating = excluded.steam_rating,
                    number_of_reviews = excluded.number_of_reviews,
                    release_date = excluded.release_date,
                    couch_players = excluded.couch_players,
                    lan_players = excluded.lan_players,
                    online_players = excluded.online_players,
                    cooptimus_url = excluded.cooptimus_url,
                    steam_url = excluded.steam_url,
                    header_image = excluded.header_image,
                    short_description = excluded.short_description,
                    tags = excluded.tags,
                    is_released = excluded.is_released,
                    updated_at = CURRENT_TIMESTAMP
            """, (
                game.title, game.steam_id, game.steam_rating, game.number_of_reviews,
                game.release_date.strftime("%Y-%m-%d") if game.release_date else None,
                game.couch_players, game.lan_players, game.online_players,
                game.cooptimus_url, game.steam_url, game.header_image,
                game.short_description, json.dumps(game.tags), game.is_released
            ))

        # TODO temp
        print(f"Imported {game.title}")

    async def save_country_data(self, countries_data: dict[int, GameCountryData]):
        conn = await self._connect()
        cursor = await conn.cursor()

        for steam_id, country_data in countries_data.items():
            for country_code, price in country_data.prices.items():
                await cursor.execute("""
                        INSERT OR REPLACE INTO GamePrice (steam_id, country_code, initial_price, final_price)
                        VALUES (?, ?, ?, ?)
                    """, (steam_id, country_code, price.initial, price.final))

            await cursor.execute("DELETE FROM GameDelisted WHERE steam_id = ?", (steam_id,))
            for country_code in country_data.delisted:
                await cursor.execute("""
                        INSERT OR REPLACE INTO GameDelisted (steam_id, country_code)
                        VALUES (?, ?)
                    """, (steam_id, country_code))

        await conn.commit()
        await conn.close()

        # TODO temp
        print(f"Saved {len(countries_data)} prices")

    
    def _row_to_game(self, row) -> Game:
        game = Game()
        game.title = row['title']
        game.steam_id = int(row['steam_id'])
        game.steam_rating = float(row['steam_rating'])
        game.number_of_reviews = int(row['number_of_reviews'])
        game.couch_players = int(row['couch_players'])
        game.lan_players = int(row['lan_players'])
        game.online_players = int(row['online_players'])
        game.cooptimus_url = row['cooptimus_url']
        game.steam_url = row['steam_url']
        game.header_image = row['header_image']
        game.short_description = row['short_description']
        game.is_released = bool(row['is_released'])
        game.score = float(row['calculated_score'])
        
        if row['release_date']:
            game.release_date = datetime.strptime(row['release_date'], "%Y-%m-%d").date()
        
        game.tags = json.loads(row['tags']) if row['tags'] else []
        
        # Add price if country_code provided and price data exists in row
        if 'initial_price' in row.keys() and row['initial_price'] is not None:
            game.price = Price(row['initial_price'], row['final_price'])
        
        return game

    async def get_total_games_count(self) -> int:
        conn = await self._connect()
        cursor = await conn.cursor()
        await cursor.execute("SELECT COUNT(*) FROM Game")
        count = (await cursor.fetchone())[0]
        await conn.close()
        return count

    async def get_all_steam_ids(self) -> list[int]:
        conn = await self._connect()
        cursor = await conn.cursor()
        await cursor.execute("SELECT steam_id FROM Game")
        rows = await cursor.fetchall()
        steam_ids = [row[0] for row in rows]
        await conn.close()
        return steam_ids


# TODO REMOVE TESTING STUFF
def get_date(dateStr):
    return datetime.strptime(dateStr, "%Y-%m-%d").date()

async def test():
    db = Database()
    await db.init_database()
    
    filters = Filters(
        country_code="SE",
        min_supported_players=10,
        max_supported_players=12,
        player_type="LAN",
        free_games=False,
        unreleased_games=False,
        from_date=get_date("1990-01-01"),
        to_date=get_date("2025-08-20"),
        min_reviews=50,
        search_tags=[]
    )
    
    scoring = Scoring(
        rating_weight=1,
        price_weight=0,
        sale_weight=0.0,
        number_of_reviews_weight=0.0,
        high_price=20
    )
    
    pagination = Pagination(limit=10, offset=9)
    
    games, count = await db.get_games(filters, scoring, pagination)
    for game in games:
        print(f"{game.title} - {game.steam_rating}")
    print(f"Total: {count}")
    #await db.save_games(load_games_from_file())
    
if __name__ == "__main__":
    asyncio.run(test())