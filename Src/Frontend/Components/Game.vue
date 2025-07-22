<script setup lang="ts">
import { GameData } from './Types.ts'
import { decodeHTML } from './DecodeHTML.ts'

interface Props {
    game: GameData
    getCurrencyPrice: (price: string) => string
}

const props = defineProps<Props>()
const emit = defineEmits(['add-tag'])

const addTag = (tag: string) => {
    emit('add-tag', tag)
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
</style>