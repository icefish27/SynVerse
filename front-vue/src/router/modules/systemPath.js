const routes = [
  {
    path: "",
    name: "AppDefault",
    redirect: "/dashboard",
  },
  {
    path: "/dashboard",
    name: "Dashboard",
    component: () => import("@/views/dashboard/index.vue"),
    meta: { title: "我的小说" },
  },
  {
    path: "/novel/:id",
    name: "WorkLayout",
    component: () => import("@/views/work/WorkLayout.vue"),
    redirect: { name: "AiChat" },
    children: [
      {
        path: "ai",
        name: "AiChat",
        component: () => import("@/views/work/AiChat.vue"),
        meta: { title: "AI 模式" },
      },
      {
        path: "novel-mode",
        name: "NovelEditor",
        component: () => import("@/views/work/NovelEditor.vue"),
        meta: { title: "小说模式" },
      },
      {
        path: "basic-info",
        name: "BasicInfo",
        component: () => import("@/views/work/BasicInfo.vue"),
        meta: { title: "基本信息" },
      },
      {
        path: "core-arch",
        name: "CoreArchitecture",
        component: () => import("@/views/work/CoreArchitecture.vue"),
        meta: { title: "核心架构" },
      },
      {
        path: "rhythm",
        name: "RhythmAnalysis",
        component: () => import("@/views/work/RhythmAnalysis.vue"),
        meta: { title: "节奏分析" },
      },
      {
        path: "consistency",
        name: "ConsistencyKG",
        component: () => import("@/views/work/ConsistencyKG.vue"),
        meta: { title: "一致性 RAG 引擎" },
      },
      {
        path: "style-rag",
        name: "StyleRAG",
        component: () => import("@/views/work/StyleRAG.vue"),
        meta: { title: "仿写 RAG 引擎" },
      },
      {
        path: "agents",
        name: "AgentManage",
        component: () => import("@/views/work/AgentManage.vue"),
        meta: { title: "多 Agent 智能体" },
      },
      {
        path: "skills",
        name: "Skills",
        component: () => import("@/views/work/Skills.vue"),
        meta: { title: "Skills" },
      },
      {
        path: "workflow",
        name: "Workflow",
        component: () => import("@/views/work/Workflow.vue"),
        meta: { title: "工作流编排" },
      },
    ],
  },
];

export default routes;
