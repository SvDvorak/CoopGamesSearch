<script setup lang="ts">
import { ref, computed } from 'vue'
import ThemeToggle from './ThemeToggle.vue'

const showInfo = ref(false)

const emailLink = computed(() => {
	const username = "andreas"
	const hostname = "anwilc.com"
	return `mailto:${username}@${hostname}`
})

const onClickAway = () => {
	showInfo.value = false
}
</script>

<template>
	<div class="sidebar" v-click-away="onClickAway">
		<div class="shortcuts">
			<a @click="showInfo = !showInfo"><img src="../Resources/InfoIcon.svg" /></a>
			<ThemeToggle />
			<a :href="emailLink"><img src="../Resources/MailIcon.svg" /></a>
			<a href="https://github.com/SvDvorak/CoopGamesSearch" target="_blank"><img
					src="../Resources/GithubIcon.svg" /></a>
		</div>
		<div class="info" v-show="showInfo">
			<h3>Coop Games Search</h3>
			<p>This is a tool I made to find games on sale to play with a number of friends of mine. Here you can find
				cheap and good games that support a specified number of players according to your friend group.</p>
			<p>All data is a combination of the data from Co-Optimus, Steam and Steamspy.</p>
			<h3>Known Issues</h3>
			<ul>
				<li>Data is limited to the games available on Co-Optimus; though some games on Co-Optimus might still be
					missing here.</li>
				<li>Prices update every 12 hours so recently started/ended sale prices will not show immediately.</li>
			</ul>
			<p></p>
		</div>
	</div>
</template>

<style scoped>
.sidebar {
	display: flex;
	flex-direction: row;
	position: fixed;
	top: 3.5em;
	right: 0;
	padding: 0.3em;
	padding-right: 0;
	max-width: 90vw;
	z-index: 1000;
}

.sidebar div {
	background: var(--card-bg);
}

.shortcuts {
	display: flex;
	flex-direction: column;
	border: 0.1em solid var(--border-color);
	border-right-width: 0;
	border-radius: 1em 0 0 1em;
}

.shortcuts a {
	cursor: pointer;
}

.shortcuts img {
	width: 2.5em;
	margin: 0.2em;
}

.info {
	border: 0.1em solid var(--border-color);
	border-left: 0px;
	border-left: 0px;
	padding: 0.7em;
	width: 24em;
	max-height: 80vh;
	overflow-y: scroll;
}

.info p {
	white-space: pre-wrap;
	margin: 0px;
}

.info h3 {
	margin-bottom: 0px;
}

.info ul {
	padding-left: 1em;
	margin-top: 0.5em;
}
</style>