<script setup lang="ts">
import { ref } from 'vue'
import { CountryData, FiltersData } from './Types.ts'

interface Props {
    countries: CountryData[]
    filters: FiltersData
}

const props = defineProps<Props>()
const emit = defineEmits(['update-filters', 'add-tag'])

const tagInput = ref('')

const addTagFromInput = () => {
    emit('add-tag', tagInput.value)
    tagInput.value = ''
}

const removeTag = (index: number) => {
    props.filters.tags.splice(index, 1)
    updateFilters()
}

const updateFilters = () => {
    emit('update-results')
}
</script>

<template>
    <div class="rounded-box filters">
        <h3>Filters</h3>
        
        <!-- Country row -->
        <div class="filter-row">
            <h4>Country (for pricing)</h4>
            <div class="filter-inputs">
                <select class="filter-input" v-model="filters.country_code" @change="updateFilters">
                    <option v-for="country in countries" :key="country.code" :value="country.code">
                        {{ country.name }}
                    </option>
                </select>
            </div>
        </div>

        <!-- Player count row -->
        <div class="filter-row">
            <h4>Players</h4>
            <div class="filter-inputs">
                <input class="filter-input" type="number" v-model.number="filters.min_supported_players" @input="updateFilters" min="1" max="100">
                <span class="filter-to-label">to</span>
                <input class="filter-input" type="number" v-model.number="filters.max_supported_players" @input="updateFilters" min="1" max="100">
                <select class="filter-input" v-model="filters.player_type" @change="updateFilters">
                    <option value="couch">Couch</option>
                    <option value="lan">LAN</option>
                    <option value="online">Online</option>
                </select>
            </div>
        </div>

        <!-- Date range row -->
        <div class="filter-row">
            <h4>Release Date</h4>
            <div class="filter-inputs">
                <input class="filter-input" type="date" v-model="filters.release_date_from" @change="updateFilters">
                <span>to</span>
                <input class="filter-input" type="date" v-model="filters.release_date_to" @change="updateFilters">
            </div>
        </div>

        <!-- Minimum reviews row -->
        <div class="filter-row">
            <h4>Minimum Reviews</h4>
            <div class="filter-inputs">
                <input class="filter-input" type="number" v-model.number="filters.min_reviews" @input="updateFilters" min="0">
            </div>
        </div>

        <!-- Checkboxes -->
        <div class="filter-row checkbox-group">
            <label>
                <input type="checkbox" v-model="filters.free_games" @change="updateFilters">
                Include Free Games
            </label>
            <label>
                <input type="checkbox" v-model="filters.unreleased_games" @change="updateFilters">
                Include Unreleased Games
            </label>
        </div>

        <!-- Tag search row -->
        <div class="filter-row">
            <h4>Tags</h4>
            <div class="filter-inputs tag-inputs">
                <input class="filter-input" type="text" v-model="tagInput" @keydown.enter="addTagFromInput" placeholder="Add a tag and press Enter">
            </div>
            <div class="tags" v-if="filters.tags.length > 0">
                <span class="tag" v-for="(tag, index) in filters.tags" :key="`filter-tag-${index}`" @click="removeTag(index)">
                    {{ tag }}
                </span>
            </div>
        </div>
    </div>
</template>

<style scoped>
.checkbox-group {
    display: flex;
    flex-direction: column;
    gap: 0.6rem;
}
.checkbox-group label {
    margin-top: 0.2rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}
.tag-inputs input {
    width: 13rem;
}
</style>