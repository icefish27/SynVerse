import { createApp } from "vue";
import App from "./App.vue";

// 全局样式组件
import "@/assets/css/globalStyle.css";

// element-plus相关
import ElementPlus from "element-plus";
import * as ElementPlusIconsVue from "@element-plus/icons-vue";
import "element-plus/dist/index.css";

// pinia相关
import { createPinia } from "pinia";
import piniaPersist from "pinia-plugin-persist";
const pinia = createPinia();
pinia.use(piniaPersist);

// vue-router相关
import router from "@/router/index.js"

const app = createApp(App);
app.use(ElementPlus);
app.use(pinia);
app.use(router)

app.mount("#app");
