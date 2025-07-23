<script setup lang="ts">

import { ref, reactive, onMounted, computed } from 'vue'
import SidePanel from './SidePanel.vue'
import Filters from './Filters.vue'
import Scoring from './Scoring.vue'
import Pagination from './Pagination.vue'
import Game from './Game.vue'
import { CountryData, FiltersData, ScoringData, GameData } from './Types.ts'

const games = ref<GameData[]>([])
const loading = ref<boolean>(false)
const error = ref<string | null>(null)
const debounceTimer = ref<number | null>(null)
const debounceTime = 300
const tagInput = ref<string>('')
const countries = ref<CountryData[]>([])
const hiddenGames = ref<Set<string>>(new Set())
const totalGames = ref<number>(0)

const visibleGames = computed(() => {
    return games.value.filter(game => !hiddenGames.value.has(game.steam_id))
})

const visibleGamesCount = computed(() => (totalGames.value - games.value.length) + visibleGames.value.length)
const hiddenGamesCount = computed(() => games.value.length - visibleGames.value.length )

const filters = reactive<FiltersData>({
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

const scoring = reactive<ScoringData>({
    rating: 0.7,
    price: 0.3,
    sale: 0.0,
    number_of_reviews: 0.0,
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
    return filters.min_supported_players &&
        filters.max_supported_players &&
        filters.min_reviews &&
        scoring.high_price
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
        games.value = games.value.concat(data.games)
        totalGames.value = data.total_games
    } catch (err: any) {
        console.error('Error fetching games:', err)
        error.value = err.message || 'Failed to load games. Please try again.'
        games.value = [] // Clear games on error
    } finally {
        loading.value = false
    }
}

const getSearchParameters = () => {
    const search_params: any = { ...filters }

    search_params.rating_weight = scoring.rating
    search_params.price_weight = scoring.price
    search_params.sale_weight = scoring.sale
    search_params.number_of_reviews_weight = scoring.number_of_reviews
    search_params.high_price = scoring.high_price

    search_params.next_index = games.value.length
    if (search_params.tags && search_params.tags.length > 0) {
        search_params.tags = search_params.tags.join('|')
    }
    return search_params
}

const loadMoreGames = () => {
    fetchGames()
}

const updateFilters = () => {
    if (debounceTimer.value) {
        clearTimeout(debounceTimer.value)
    }
    
    debounceTimer.value = setTimeout(() => {
        // Clear out games before we fetch
        games.value = []
        fetchGames()
    }, debounceTime)
}

const getCurrency = () => {
    if (countries.value.length === 0)
        return ''

    const country = countries.value.find(c => c.code === filters.country_code)
    return country ? country.currency : ''
}

const getCurrencyPrice = (price: string) => {
    const currency = getCurrency()
    if (currency === "EUR")
        return price + getCurrencySymbol()
    else if (currency === "USD")
        return getCurrencySymbol() + price
    return `${price} ${currency}`
}

const getCurrencySymbol = () => {
    const currency = getCurrency()
    if (currency === "EUR")
        return '€'
    else if (currency === "USD")
        return '$'
    return currency
}

const addTag = (tag: string) => {
    tag = tag.trim()
    if (tag && !filters.tags.includes(tag)) {
        filters.tags.push(tag)
        tagInput.value = ''
        updateFilters()
    }
}

const loadHiddenGames = () => {
    const saved = localStorage.getItem('hidden-games')
    if (!saved)
        return;

    const hiddenArray = JSON.parse(saved)
    hiddenGames.value = new Set(hiddenArray)
}

const hideGame = (steamId: string) => {
    hiddenGames.value.add(steamId)
    localStorage.setItem('hidden-games', JSON.stringify([...hiddenGames.value]))
}

const clearHidden = () => {
    hiddenGames.value.clear()
    localStorage.setItem('hidden-games', JSON.stringify([]))
}

const hasRetrievedGames = () => {
    return !loading.value && !error.value && games.value.length > 0
}

const canRetrieveMoreGames = () => {
    return hasRetrievedGames() && totalGames.value != games.value.length
}

onMounted(async () => {
    loadHiddenGames()
    await loadCountries()
    setDefaultCountryFromLocale()
    await fetchGames()
})
</script>

<template>
    <SidePanel />

    <div class="controls">
        <filters :countries="countries" :filters="filters" @update-results="updateFilters" @add-tag="addTag">
        </filters>
        <scoring :scoring="scoring" :currency="getCurrencySymbol()" @update-results="updateFilters">
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

    <Pagination v-if="hasRetrievedGames()" :total_games="visibleGamesCount" :hidden_games="hiddenGamesCount" @clear-hidden="clearHidden">
    </Pagination>

    <game v-for="(game, index) in visibleGames" :key="`game-${game.steam_id || index}`" :game="game"
        :getCurrencyPrice="getCurrencyPrice" @add-tag="addTag" @hide-game="hideGame">
    </game>

    <div class="rounded-box load-more" v-if="canRetrieveMoreGames()">
        <button @click="loadMoreGames">
            Load more
        </button>
    </div>
</template>

<style>
body {
    font-family: Arial, sans-serif;
    margin: 1rem auto;
    background-color: var(--bg-color);
    max-width: 50rem;
    padding: 0 1rem;
    color: var(--text-color);
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
    border: 1px solid var(--border-color);
    border-radius: 4px;
    background-color: var(--card-color);
    text-decoration: none;
    color: var(--text-color);
}
button:hover:not(:disabled) {
    background-color: var(--button-hover);
}
button:disabled {
    background-color: var(--disabled-bg-color);
    color: var(--disabled-text-color);
    background-color: var(--disabled-border-color);
}
.rounded-box {
    background-color: var(--card-bg);
    border: 1px solid var(--border-color);
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    margin-bottom: 0.7rem;
    border-radius: 5px;
    padding: 0.8rem
}
.tags {
    margin-top: 0.8rem;
}
.tag {
    display: inline-block;
    background-color: var(--button-bg);
    color: var(--text-color);
    padding: 4px 8px;
    margin: 2px 2px 2px 2px;
    border-radius: 12px;
    font-size: 0.85em;
    cursor: pointer;
    transition: background-color 0.2s;
}
.tag:hover {
    background-color: var(--button-hover);
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
    border: 1px solid var(--border-color);
    border-radius: 4px;
    background-color: var(--button-bg);
    color: var(--text-color);
}
.filter-input:hover, .pagination-button:hover {
    background-color: var(--button-hover);
}
.filter-inputs input {
    width: 8rem;
}
.filter-inputs select {
    width: 12rem;
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
.load-more {
    display: flex;
    justify-content: center;
}
</style>