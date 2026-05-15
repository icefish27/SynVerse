// router/routeGuard.js
export function setupRouterGuard(router) {
  // 权限校验
  router.beforeEach((to, from, next) => {
    const token = localStorage.getItem('token');
    if (to.meta.requiresAuth && !token) {
      next({ name: 'Login' });
    } else {
      next();
    }
  });

  // 路由切换动画
  router.beforeEach((to, from) => {
    document.body.classList.add('page-transition');
    return new Promise(resolve => {
      setTimeout(() => resolve(), 300);
    });
  });

  // 路由切换后操作
  router.afterEach((to) => {
    document.title = to.meta.title || '默认标题';
    document.body.classList.remove('page-transition');
  });
}    