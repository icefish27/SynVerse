const routes = [
  {
    path: "",
    name: "AppDefault", // 给默认子路由命名,防止冲突
    redirect: "/home",
  },
  {
    path: "/home",
    name: "home",
    component: () => import("@/views/home/index.vue"),
  },
//   {
//     path: "/:pathMatch(.*)*",
//     hidden: true,
//     name: "ERROR404",
//     component: () => import("@/views/404.vue"),
//   },
]

export default routes