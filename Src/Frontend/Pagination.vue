<script setup lang="ts">
import PagenationData from './Types.ts'

interface Props {
    pagination: PagenationData
}

const props = defineProps<Props>()
const emit = defineEmits(['go-to-page'])

const goToPage = (page: number) => {
    emit('go-to-page', page)
}
</script>

<template>
    <div class="rounded-box pagination">
        <div class="pagination-buttons">
            <button 
                :disabled="pagination.current_page <= 1"
                @click="goToPage(pagination.current_page - 1)">
                Previous
            </button>
            <button 
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
    color: #666;
}
</style>