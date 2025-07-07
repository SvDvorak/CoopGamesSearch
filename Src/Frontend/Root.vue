<script setup lang="ts">

import { ref, reactive, onMounted } from 'vue'
import Filters from './Filters.vue'
import Scoring from './Scoring.vue'

interface Country {
    code: string
    name: string
    currency: string
}

interface Pagination {
    current_page: number
    total_pages: number
    page_size: number
    total_games: number
}

interface Filters {
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

interface Scoring {
    rating: number
    price: number
    high_price: number
}

const games = ref<any[]>([])
const loading = ref<boolean>(false)
const error = ref<string | null>(null)
const debounceTimer = ref<number | null>(null)
const debounceTime = 300
const tagInput = ref<string>('')
const countries = ref<Country[]>([])

const pagination = reactive<Pagination>({
    current_page: 1,
    total_pages: 1,
    page_size: 1, // Will be updated from API response
    total_games: 0
})

const filters = reactive<Filters>({
    country_code: 'SE',
    min_supported_players: 1,
    max_supported_players: 1000,
    player_type: 'online',
    free_games: true,
    unreleased_games: true,
    release_date_from: '1988-08-20',
    release_date_to: new Date().toISOString().split('T')[0], // Format: YYYY-MM-DD
    min_reviews: 50,
    tags: []
})

const scoring = reactive<Scoring>({
    rating: 0.7,
    price: 0.3,
    high_price: 30.0
})

const loadCountries = async () => {
    try {
        const response = await fetch('/countries')
        countries.value = await response.json()
        countries.value.sort((a, b) => a.name.localeCompare(b.name))
    } catch (err: any) {
        error.value = err.message || 'Failed to load countries. Please reload page.'
    }
}

const setDefaultCountryFromLocale = () => {
    // Get user's locale (e.g., "en-US", "sv-SE", "de-DE")
    const userLocale = navigator.language || navigator.languages[0]
    
    if (userLocale && userLocale.includes('-')) {
        const countryCode = userLocale.split('-')[1]
        
        const countryExists = countries.value.some(c => c.code === countryCode)
        if (countryExists) {
            filters.country_code = countryCode
        }
    }
}

const validFilters = () => {
    return filters.min_supported_players != null &&
        filters.max_supported_players != null &&
        filters.min_reviews != null &&
        scoring.high_price != null
}

const fetchGames = async () => {
    if (!validFilters())
        return

    loading.value = true
    error.value = null
    try {
        const response = await fetch(`/games?${new URLSearchParams(getSearchParameters())}`)
        
        if (!response.ok) {
            const errorData = await response.json()
            throw new Error(errorData.detail || `Server error: ${response.status}`)
        }

        const data = await response.json()
        games.value = data.games
        pagination.total_pages = data.pagination.total_pages
        pagination.page_size = data.pagination.page_size
        pagination.total_games = data.pagination.total_games
    } catch (err: any) {
        console.error('Error fetching games:', err)
        error.value = err.message || 'Failed to load games. Please try again.'
        games.value = [] // Clear games on error
    } finally {
        loading.value = false
    }
}

const getSearchParameters = () => {
    const search_params = { ...filters }

    search_params.rating_weight = scoring.rating
    search_params.price_weight = scoring.price
    search_params.high_price = scoring.high_price

    search_params.page = pagination.current_page
    if (search_params.tags && search_params.tags.length > 0) {
        search_params.tags = search_params.tags.join('|')
    }
    return search_params
}

const updateFilters = () => {
    if (debounceTimer.value) {
        clearTimeout(debounceTimer.value)
    }
    
    debounceTimer.value = setTimeout(() => {
        // Reset to page 1 when filters change
        pagination.current_page = 1
        fetchGames()
    }, debounceTime)
}

const formatDate = (dateStr: string) => {
    const options: Intl.DateTimeFormatOptions = { year: 'numeric', month: 'short', day: '2-digit' }
    return new Date(dateStr).toLocaleDateString(undefined, options)
}

const getCurrency = () => {
    if (countries.value.length === 0) return ''

    const country = countries.value.find(c => c.code === filters.country_code)
    const currency = country ? country.currency : ''
    if (currency === "EUR") return '€'
    else if (currency === "USD") return '$'
    return currency
}

const getCurrencyPrice = (price: string) => {
    const country = countries.value.find(c => c.code === filters.country_code)
    const currency = country ? country.currency : ''
    if (currency === "EUR") return price + getCurrency()
    else if (currency === "USD") return getCurrency() + price
    return `${price} ${currency}`
}

const getPrice = (game: any) => {
    if (game.price == null || game.price.final <= 0) return 'Free'
    const price = (game.price.final / 100).toFixed(2)
    return getCurrencyPrice(price)
}

const getSale = (game: any) => {
    if (game.price == null || game.price.final === game.price.initial) return ''
    const salePercentage = Math.round((1 - game.price.final / game.price.initial) * 100)
    return `(${salePercentage}% off)`
}

const goToPage = (page: number) => {
    if (page >= 1 && page <= pagination.total_pages) {
        pagination.current_page = page
        fetchGames()
    }
}

const addTag = (tag: string) => {
    tag = tag.trim()
    if (tag && !filters.tags.includes(tag)) {
        filters.tags.push(tag)
        tagInput.value = ''
        updateFilters()
    }
}

const decodeHtml = (html: string) => {
    const txt = document.createElement('textarea')
    txt.innerHTML = html
    return txt.value
}

// Lifecycle
onMounted(async () => {
    await loadCountries()
    setDefaultCountryFromLocale()
    await fetchGames()
})
</script>

<template>
<div class="controls">
    <filters
        :countries="countries"
        :filters="filters"
        @update-results="updateFilters"
        @add-tag="addTag">
    </filters>
    <scoring
        :scoring="scoring"
        :currency="getCurrency()"
        @update-results="updateFilters">
    </scoring>
</div>

<!-- Loading indicator -->
<div v-if="loading" class="rounded-box response-info">
    Loading games...
</div>

<!-- Error message -->
<div v-if="error" class="rounded-box response-info error">
    {{ error }}
</div>

<!-- Pagination controls -->
<div v-if="!loading && !error && games.length > 0" class="rounded-box pagination">
    <div class="pagination-buttons">
        <button 
            class="pagination-button" 
            :disabled="pagination.current_page <= 1"
            @click="goToPage(pagination.current_page - 1)">
            Previous
        </button>
        <button 
            class="pagination-button" 
            :disabled="pagination.current_page >= pagination.total_pages"
            @click="goToPage(pagination.current_page + 1)">
            Next
        </button>
    </div>
    <div class="pagination-info">
        Page {{ pagination.current_page }} of {{ pagination.total_pages }} 
        ({{ pagination.total_games }} games total)
    </div>
</div>

<!-- Games list -->
<div class="rounded-box game" v-for="(g, index) in games" :key="`game-${g.steam_id || index}`">
    <img :src="g.header_image" :alt="'Header for ' + g.title">
    <h2>{{ g.title }}</h2>
    <div class="game-info">
        <p>
            <strong>Score: </strong>{{ g.score.toFixed(3) }}<br>
            <strong>Price: </strong>{{ getPrice(g) }} <span class="sale">{{ getSale(g) }}</span><br>
            <strong>Steam Rating: </strong>{{ g.steam_rating > 0 ? (g.steam_rating * 100).toFixed(1) + '%' : 'N/A' }}
            ({{ g.number_of_reviews }} reviews)<br>
            <strong>Release Date: </strong>{{ g.is_released ? formatDate(g.release_date) : 'Coming soon' }}<br>
        </p>
        <p>
            <strong>Couch Players: </strong>{{ g.couch_players }}<br>
            <strong>LAN Players: </strong>{{ g.lan_players }}<br>
            <strong>Online Players: </strong>{{ g.online_players }}<br>
        </p>
    </div>
    <p>{{ decodeHtml(g.short_description) }}</p>
    <div class="links">
        <a :href="g.steam_url" target="_blank">Steam Page</a>
        <a :href="g.cooptimus_url" target="_blank">Co-Optimus Page</a>
    </div>
    <div class="tags">
        <span class="tag" v-for="(tag, tagIndex) in g.tags" :key="`${g.steam_id}-tag-${tagIndex}`" @click="addTag(tag)">
            {{ tag }}
        </span>
    </div>
</div>
</template>

<style>
	body {
		font-family: Arial, sans-serif;
		margin: 1rem auto;
		background-color: #f4f4f4;
		max-width: 50rem;
		padding: 0 1rem;
	}

	h1 {
		text-align: center;
		color: #2c3e50;
		margin-bottom: 2rem;
		font-size: 2.8rem;
		font-weight: 600;
		position: relative;
		padding-bottom: 0.75rem;
	}
	h1::after {
		content: '';
		position: absolute;
		bottom: 0;
		left: 50%;
		transform: translateX(-50%);
		width: 8rem;
		height: 0.2rem;
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
	}

	input, button {
		cursor: pointer;
	}
	input:disabled, button:disabled {
		cursor: default;
	}
	button {
		padding: 0.5rem 1rem;
		border: 1px solid #ddd;
		border-radius: 4px;
		background-color: #fff;
		text-decoration: none;
		color: #333;
	}
	button:hover:not(:disabled) {
		background-color: #f5f5f5;
	}
	button:disabled {
		background-color: #f9f9f9;
		color: #999;
	}
	.rounded-box {
		background-color: #fff;
		border: 1px solid #ddd;
		box-shadow: 0 2px 4px rgba(0,0,0,0.1);
		margin-bottom: 0.7rem;
		border-radius: 5px;
		padding: 0.8rem
	}
	.game img {
		width: 31rem;
		height: auto;
		border-radius: 4px;
	}
	.game h2 {
		margin-top: 0.6rem;
		margin-bottom: 0.5rem;
	}
	.game-info {
		display: flex;
		flex-direction: row;
		gap: 2.6rem;
	}
	.game-info p {
		margin: 0;
	}
	.game-info span {
		color: rgb(150, 16, 16);
	}
	.links {
		margin-bottom: 1rem;
	}
	.links a {
		margin-right: 0.6rem;
	}
	.tags {
		margin-top: 0.8rem;
	}
	.tag {
		display: inline-block;
		background-color: #e0e0e0;
		color: #333;
		padding: 4px 8px;
		margin: 2px 2px 2px 2px;
		border-radius: 12px;
		font-size: 0.85em;
		cursor: pointer;
		transition: background-color 0.2s;
	}
	.tag:hover {
		background-color: #c0c0c0;
	}
	.controls {
		gap: 2.6rem;
	}
	.controls h3 {
		margin-top: 0;
	}
	.filter-row {
		margin-bottom: 0.5rem;
	}
	.filter-row:last-child {
		margin-bottom: 0;
	}
	.filter-row h4 {
		margin: 0 0 0.3rem 0;
		font-size: 0.9rem;
		font-weight: bold;
	}
	.filter-inputs {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}
	.filter-input {
		padding: 0.25rem 0.6rem;
		border: 1px solid #ddd;
		border-radius: 4px;
		background-color: #fff;
	}
	.filter-inputs input {
		width: 8rem;
	}
	.filter-inputs select {
		width: 12rem;
	}
	.filter-inputs input[type="range"] {
		width: 13rem;
	}
	.filter-inputs label {
		min-width: 9rem;
		font-size: 0.9rem;
	}
	.response-info {
		text-align: center;
		padding: 1.3rem;
	}
	.error {
		background-color: #fee;
		border: 1px solid #fcc;
		border-radius: 8px;
		padding: 1rem;
		color: #c33;
	}
	.pagination {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 1.3rem;
	}
	.pagination-buttons {
		display: flex;
		gap: 0.6rem;
	}
	.pagination-info {
		font-size: 0.9rem;
		color: #666;
	}
</style>