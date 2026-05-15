import { createRouter, createWebHashHistory } from "vue-router";
import { ElNotification } from "element-plus";
import NProgress from "nprogress";
import "nprogress/nprogress.css";

import systemRoutes from "./modules/systemPath.js";
import { useUserStore } from "@/store/useUserStore";

// 路由配置
const routes = [...systemRoutes];

// 创建路由实例
const router = createRouter({
  history: createWebHashHistory(),
  routes,
  // 路由跳转后的滚动行为
  scrollBehavior(to, from, savedPosition) {
    // 有保存位置则恢复，否则滚动到顶部
    return savedPosition || { top: 0 };
  },
});

// 应用基础标题
const BASE_TITLE = import.meta.env.VITE_APP_TITLE;

/**
 * 路由前置守卫
 * 1. 启动进度条
 * 2. 设置页面标题
 * 3. 处理路由访问权限
 */
router.beforeEach(async (to, from, next) => {
  // 启动进度条
  NProgress.start();
  
  // 设置页面标题（格式：页面标题 - 应用名）
  document.title = to.meta.title ? `${to.meta.title} - ${BASE_TITLE}` : BASE_TITLE;

  // 白名单路径（无需登录即可访问）
  const whiteList = ["/auth", "/home", "/aboutUs"];
  if (whiteList.includes(to.path)) {
    return next();
  }

  // 获取用户状态
  const userStore = useUserStore();
  
  // 未登录时重定向到登录页
  if (!userStore.isLogin) {
    return next({
      path: "/auth",
      query: { redirect: to.fullPath }, // 记录原始路径用于登录后跳转
    });
  }

  // 权限验证（示例：检查路由meta.roles）
  if (to.meta.roles && !to.meta.roles.includes(userStore.userRole)) {
    return next({ name: "Forbidden" }); // 跳转到403页面
  }

  next();
});

/**
 * 路由后置守卫
 * 1. 结束进度条
 */
router.afterEach(() => {
  NProgress.done();
});

/**
 * 错误处理
 * 1. 结束进度条
 * 2. 显示错误通知
 */
router.onError((error) => {
  NProgress.done();
  ElNotification.error({
    title: "路由错误",
    message: error.message || "路由加载失败",
  });
  console.error("路由错误:", error);
});

/**
 * 路由跳转工具方法
 * @param {String} routeName - 路由名称
 * @param {Object} params - 路径参数
 * @param {Object} query - 查询参数
 * @param {Boolean} replace - 是否使用replace模式
 */
router.navigateTo = function (routeName, params = {}, query = {}, replace = false) {
  const method = replace ? "replace" : "push";
  this[method]({ name: routeName, params, query });
};

export default router;    