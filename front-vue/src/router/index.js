import { createRouter, createWebHashHistory } from "vue-router";
import { ElNotification } from "element-plus";
import NProgress from "nprogress";
import "nprogress/nprogress.css";
import systemRoutes from "./modules/systemPath.js";

const routes = [...systemRoutes];
const BASE_TITLE = import.meta.env.VITE_APP_TITLE || "SynVerse";

const router = createRouter({
  history: createWebHashHistory(),
  routes,
  scrollBehavior() {
    return { top: 0 };
  },
});

router.beforeEach(async (to, from, next) => {
  NProgress.start();
  document.title = to.meta.title ? `${to.meta.title} - ${BASE_TITLE}` : BASE_TITLE;
  next();
});

router.afterEach(() => {
  NProgress.done();
});

router.onError((error) => {
  NProgress.done();
  ElNotification.error({ title: "路由错误", message: error.message || "路由加载失败" });
  console.error("路由错误:", error);
});

export default router;
