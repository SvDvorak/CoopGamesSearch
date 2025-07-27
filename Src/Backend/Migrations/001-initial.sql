--------------------------------------------------------------------------------
-- Up
--------------------------------------------------------------------------------
CREATE TABLE Game (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    steam_id INTEGER UNIQUE NOT NULL,
    steam_rating REAL DEFAULT 0.0,
    number_of_reviews INTEGER DEFAULT 0,
    release_date TEXT,
    couch_players INTEGER DEFAULT 0,
    lan_players INTEGER DEFAULT 0,
    online_players INTEGER DEFAULT 0,
    cooptimus_url TEXT DEFAULT '',
    steam_url TEXT DEFAULT '',
    header_image TEXT,
    short_description TEXT DEFAULT '',
    tags TEXT DEFAULT '[]', -- JSON array as text
    is_released BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE GamePrice (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id INTEGER REFERENCES Game(id),
    country_code TEXT NOT NULL,
    initial_price INTEGER DEFAULT 0,
    final_price INTEGER DEFAULT 0,
    UNIQUE(game_id, country_code)
);

CREATE TABLE GameDelisted (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id INTEGER REFERENCES Game(id),
    country_code TEXT NOT NULL,
    UNIQUE(game_id, country_code)
);

--------------------------------------------------------------------------------
-- Down
--------------------------------------------------------------------------------
DROP TABLE GameDelisted;
DROP TABLE GamePrice;
DROP TABLE Game;