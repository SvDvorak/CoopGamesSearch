<script setup lang="ts">

interface Props {
    total_games: number
    hidden_games: number
}

const props = defineProps<Props>()
const emit = defineEmits(['clear-hidden'])

const clearHidden = () => {
    emit('clear-hidden')
}
</script>

<template>
    <div class="rounded-box pagination">
        <div class="pagination-info">
            {{ total_games }} games ({{ hidden_games }} hidden)
        </div>
        <button
            :disabled="hidden_games == 0"
            @click="clearHidden()">
            Clear hidden
        </button>
    </div>
</template>

<style scoped>
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
    color: var(--text-color);
}
.pagination-button {
  background-color: var(--button-bg);
  border: 1px solid var(--border-color);
  color: var(--text-color);
}

.pagination-button:hover {
  background-color: var(--button-hover);
}
</style>