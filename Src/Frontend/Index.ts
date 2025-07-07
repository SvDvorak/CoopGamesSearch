import Vue from "vue";
import './style.css';
import RootComponent from "./Root.vue";

export const bus = new Vue();

new Vue({
    el: "#app",
    template: `
    <root-component />
    `,
    components: {
        RootComponent,
    }
});