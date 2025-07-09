export interface CountryData {
    code: string
    name: string
    currency: string
}

export interface PaginationData {
    current_page: number
    total_pages: number
    page_size: number
    total_games: number
}

export interface FiltersData {
    country_code: string
    min_supported_players: number
    max_supported_players: number
    player_type: string
    free_games: boolean
    unreleased_games: boolean
    release_date_from: string
    release_date_to: string
    min_reviews: number
    tags: string[]
}

export interface ScoringData {
    rating: number
    price: number
    sale: number
    number_of_reviews: number
    high_price: number
}

export interface GameData {
    steam_id: string
    title: string
    header_image: string
    short_description: string
    steam_url: string
    cooptimus_url: string
    score: number
    price: {
        initial: number
        final: number
    } | null
    steam_rating: number
    number_of_reviews: number
    release_date: string
    is_released: boolean
    couch_players: number
    lan_players: number
    online_players: number
    tags: string[]
}