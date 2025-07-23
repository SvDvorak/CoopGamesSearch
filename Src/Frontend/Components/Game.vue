<script setup lang="ts">
import { GameData } from './Types.ts'
import { decodeHTML } from './DecodeHTML.ts'

interface Props {
    game: GameData
    getCurrencyPrice: (price: string) => string
}

const props = defineProps<Props>()
const emit = defineEmits(['add-tag', 'hide-game'])

const addTag = (tag: string) => {
    emit('add-tag', tag)
}

const hideGame = () => {
    emit('hide-game', props.game.steam_id)
}

const getPrice = (game: any) => {
    if (game.price == null || game.price.final <= 0) return 'Free'
    const price = (game.price.final / 100).toFixed(2)
    return props.getCurrencyPrice(price)
}

const getSale = (game: any) => {
    if (game.price == null || game.price.final === game.price.initial) return ''
    const salePercentage = Math.round((1 - game.price.final / game.price.initial) * 100)
    return `(${salePercentage}% off)`
}

const formatDate = (dateStr: string) => {
    const options: Intl.DateTimeFormatOptions = { year: 'numeric', month: 'short', day: '2-digit' }
    return new Date(dateStr).toLocaleDateString(undefined, options)
}
</script>

<template>
    <div class="rounded-box game">
        <a class="hide-button" @click="hideGame" title="Hide this game">
            <!-- Super ugly to have to inline the SVG like this but I have to so that I can change color in CSS-->
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 -960 960 960" fill="currentColor"><path d="M650-445 549-546q2-11-7.5-22t-23.5-9l-93-93q14-5 28-7.5t27-2.5q75 0 127.5 52.5T660-500q0 11-2.5 27t-7.5 28Zm154 154-78-78q31-27 56-58t48-73q-52-100-143.5-160T480-720q-29 0-51.5 3t-42.5 8l-88-88q41-17 88-25.5t94-8.5q157 0 283.5 88.5T951-500q-23 61-62.5 115.5T804-291ZM780-44 630-193q-33 12-70.5 18t-79.5 6q-158 0-284.5-89.5T9-500q20-51 53-100t72-89L28-795l67-67 751 752-66 66ZM213-613q-27 28-45.5 53T131-500q50 101 142 160.5T480-280q11 0 25.5-1t34.5-4l-36-38q-6 2-12 2.5t-12 .5q-75 0-127.5-52.5T300-500v-11.5q0-6.5 1-12.5l-88-89Zm343 74Zm-180 90Z"/>
            </svg>
        </a>
        <img :src="game.header_image" :alt="'Header for ' + game.title">
        <h2>{{ game.title }}</h2>
        <div class="game-info">
            <p>
                <strong>Score: </strong>{{ game.score.toFixed(3) }}<br>
                <strong>Price: </strong>{{ getPrice(game) }} <span class="sale">{{ getSale(game) }}</span><br>
                <strong>Steam Rating: </strong>{{ game.steam_rating > 0 ? (game.steam_rating * 100).toFixed(1) + '%' : 'N/A' }}
                ({{ game.number_of_reviews }} reviews)<br>
                <strong>Release Date: </strong>{{ game.is_released ? formatDate(game.release_date) : 'Coming soon' }}<br>
            </p>
            <p>
                <strong>Couch Players: </strong>{{ game.couch_players }}<br>
                <strong>LAN Players: </strong>{{ game.lan_players }}<br>
                <strong>Online Players: </strong>{{ game.online_players }}<br>
            </p>
        </div>
        <p>{{ decodeHTML(game.short_description) }}</p>
        <div class="links">
            <a :href="game.steam_url" target="_blank">Steam Page</a>
            <a :href="game.cooptimus_url" target="_blank">Co-Optimus Page</a>
        </div>
        <div class="tags">
            <span class="tag" v-for="(tag, tagIndex) in game.tags" :key="`${game.steam_id}-tag-${tagIndex}`" @click="addTag(tag)">
                {{ tag }}
            </span>
        </div>
    </div>
</template>

<style scoped>
.game {
    position: relative;
}
.game img {
    width: 31rem;
    height: auto;
    border-radius: 4px;
}
.hide-button {
    position: absolute;
    top: 1em;
    right: 1em;
    width: 28px;
    height: 28px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    transition: background-color 0.2s ease;
}
.hide-button svg {
    color: var(--hide-color);
}
.hide-button svg:hover {
    filter: brightness(150%);
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
    color: var(--accent-color);
}
.links a:hover {
    opacity: 0.8;
}
</style>