// router/index.js
import { createRouter, createWebHistory } from 'vue-router'
import { setupRouterGuard } from './routeGuard'

// 自动导入路由模块（vite提供的批量静态导入（同步加载））
const modules = import.meta.globEager('./modules/*.js');
const routeModules = Object.values(modules).map(m => m.default);

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
    },
    ...routeModules,
    // {
    //   path: '/:pathMatch(.*)*',
    //   name: 'NotFound',
    //   component: () => import('@/views/error/NotFound.vue'),
    // },
  ],
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) {
      return savedPosition;
    } else {
      return { top: 0 };
    }
  },
});

// 注册路由守卫
setupRouterGuard(router);

export default router;