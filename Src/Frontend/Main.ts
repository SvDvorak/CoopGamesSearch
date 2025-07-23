//import './assets/main.css'

import { createApp } from 'vue'
import App from './Components/Root.vue'
import VueClickAway from "vue3-click-away";
import './theme.css'

const app = createApp(App)
app.use(VueClickAway)
app.mount('#app')
