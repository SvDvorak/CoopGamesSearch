<script setup lang="ts">
import { ref } from 'vue'
import { ScoringData } from './Types.ts'

interface Props {
    scoring: ScoringData,
    currency: string
}

const props = defineProps<Props>()
const emit = defineEmits(['update-results'])

const updateResults = () => {
    emit('update-results')
}
</script>

<template>
    <div class="rounded-box controls scoring">
        <h3>Scoring</h3>
        <!-- Scoring weights row -->
        <div class="filter-row">
            <h4>Weights</h4>
            <div class="filter-inputs"
                title="Weight for game rating. Higher means better rating is more important.">
                <label>Rating Weight: {{ scoring.rating.toFixed(2) }}</label>
                <input class="filter-input" type="range" v-model.number="scoring.rating" @input="updateResults" min="0" max="1" step="0.01">
            </div>
            <div class="filter-inputs"
                title="Weight for price. Higher means cheaper games are prioritized.">
                <label>Price Weight: {{ scoring.price.toFixed(2) }}</label>
                <input class="filter-input" type="range" v-model.number="scoring.price" @input="updateResults" min="0" max="1" step="0.01">
            </div>
            <div class="filter-inputs"
                title="Weight for sale percentage. Higher means more discount is prioritized.">
                <label>Sale Weight: {{ scoring.sale.toFixed(2) }}</label>
                <input class="filter-input" type="range" v-model.number="scoring.sale" @input="updateResults" min="0" max="1" step="0.01">
            </div>
            <div class="filter-inputs"
                title="Weight for review count. Higher means more reviews are prioritized. Lower means fewer reviews are prioritized.">
                <label>Number of Reviews Weight: {{ scoring.number_of_reviews.toFixed(2) }}</label>
                <input class="filter-input" type="range" v-model.number="scoring.number_of_reviews" @input="updateResults" min="-1" max="1" step="0.01">
            </div>
        </div>

        <!-- Expensive game threshold row -->
        <div class="filter-row">
            <h4>Expensive Game Threshold</h4>
            <div class="filter-inputs">
                <input class="filter-input" type="number" v-model.number="scoring.high_price"
                @input="updateResults" min="0" step="0.01"
                placeholder="Price in €"
                title="Whatever you find to be a bit expensive for a game to play with friends.">
                <span :key="currency">{{ currency }}</span>
            </div>
        </div>
    </div>
</template>

<style scoped>
.filter-inputs input[type="range"] {
    width: 13rem;
}
</style>