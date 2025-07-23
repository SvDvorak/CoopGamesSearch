<script setup lang="ts">

import { ref, onMounted } from 'vue'

const isDarkMode = ref(false)

const toggleTheme = () => {
    isDarkMode.value = !isDarkMode.value
    const theme = isDarkMode.value ? 'dark' : 'light'

    document.documentElement.setAttribute('data-theme', theme)

    localStorage.setItem('theme-preference', theme)
}

const loadThemePreference = () => {
    const saved = localStorage.getItem('theme-preference')
    isDarkMode.value = saved ? saved === "dark" : window.matchMedia("(prefers-color-scheme: dark)").matches
    document.documentElement.setAttribute('data-theme', isDarkMode.value ? "dark" : "light")
}

onMounted(async () => {
    loadThemePreference()
})
</script>

<template>
    <a class="theme-toggle" @click="toggleTheme"
        :title="isDarkMode ? 'Switch to light mode' : 'Switch to dark mode'">
        <img v-if="isDarkMode" src="../Resources/LightMode.svg" alt="Light mode" />
        <img v-else src="../Resources/DarkMode.svg" alt="Dark mode" />
    </a>
</template>

<style>
.theme-toggle {
  cursor: pointer;
  transition: background-color 0.2s ease;
}
.theme-toggle img {
	width: 3em;
    margin-bottom: -0.25em;
}
</style>