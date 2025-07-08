<script setup lang="ts">
import { ref } from 'vue'

interface Props {
    scoring: any,
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
            <div class="filter-inputs">
                <label>Rating Weight: {{ scoring.rating.toFixed(2) }}</label>
                <input class="filter-input" type="range" v-model.number="scoring.rating" @input="updateResults" min="0" max="1" step="0.01">
            </div>
            <div class="filter-inputs">
                <label>Price Weight: {{ scoring.price.toFixed(2) }}</label>
                <input class="filter-input" type="range" v-model.number="scoring.price" @input="updateResults" min="0" max="1" step="0.01">
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