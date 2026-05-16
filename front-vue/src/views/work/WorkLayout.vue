<template>
  <div class="work-layout">
    <!-- 左侧边栏 -->
    <aside class="left-sidebar">
      <div class="sidebar-header">
        <h2>{{ novelStore.currentNovel?.title || '加载中...' }}</h2>
        <el-button size="small" type="primary" @click="handleNewChapter">开启新章</el-button>
      </div>
      <div class="sidebar-search">
        <el-input v-model="chapterSearch" placeholder="搜索章节..." size="small" clearable />
      </div>
      <div class="chapter-list">
        <div v-if="chapterStore.loading" class="sidebar-loading">
          <el-skeleton :rows="5" animated />
        </div>
        <div v-else-if="chapterStore.chapters.length === 0" class="sidebar-empty">
          <p>暂无章节</p>
          <el-button size="small" type="primary" @click="handleNewChapter">开启新章</el-button>
        </div>
        <div
          v-for="chapter in filteredChapters"
          :key="chapter.id"
          class="chapter-item"
          :class="{ active: chapterStore.currentChapter?.id === chapter.id }"
          @click="selectChapter(chapter)"
        >
          <span class="chapter-num">{{ chapter.chapter_number }}</span>
          <span class="chapter-title">{{ chapter.title || `第${chapter.chapter_number}章` }}</span>
          <span class="chapter-words">{{ chapter.word_count }}字</span>
        </div>
      </div>
      <div class="sidebar-footer">
        共 {{ chapterStore.chapterCount }} 章
      </div>
    </aside>

    <!-- 右侧主区域 -->
    <div class="main-area">
      <!-- 顶部导航 -->
      <nav class="top-nav">
        <el-button
          v-for="tab in tabs"
          :key="tab.name"
          :type="activeTab === tab.name ? 'primary' : 'default'"
          size="small"
          @click="switchTab(tab.name)"
        >
          {{ tab.label }}
        </el-button>
      </nav>

      <!-- 中央内容区 -->
      <main class="content-area">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useNovelStore } from "@/store/useNovelStore";
import { useChapterStore } from "@/store/useChapterStore";

const route = useRoute();
const router = useRouter();
const novelStore = useNovelStore();
const chapterStore = useChapterStore();

const chapterSearch = ref("");

const tabs = [
  { name: "AiChat", label: "AI 模式" },
  { name: "NovelEditor", label: "小说模式" },
  { name: "BasicInfo", label: "基本信息" },
  { name: "CoreArchitecture", label: "核心架构" },
  { name: "StyleRAG", label: "仿写RAG引擎" },
];

const activeTab = computed(() => route.name);

const filteredChapters = computed(() => {
  if (!chapterSearch.value) return chapterStore.chapters;
  const q = chapterSearch.value.toLowerCase();
  return chapterStore.chapters.filter(
    (c) => c.title?.toLowerCase().includes(q) || String(c.chapter_number).includes(q)
  );
});

onMounted(async () => {
  const novelId = route.params.id;
  if (novelId) {
    await novelStore.fetchNovel(novelId);
    await chapterStore.fetchChapters(novelId);
  }
});

watch(() => route.params.id, async (id) => {
  if (id) {
    await novelStore.fetchNovel(id);
    await chapterStore.fetchChapters(id);
  }
});

function switchTab(name) {
  router.push({ name, params: { id: route.params.id } });
}

function selectChapter(chapter) {
  chapterStore.setCurrentChapter(chapter);
  router.push({ name: "NovelEditor", params: { id: route.params.id } });
}

function handleNewChapter() {
  router.push({ name: "AiChat", params: { id: route.params.id } });
}
</script>

<style scoped lang="scss">
.work-layout {
  display: flex;
  height: 100vh;
  background: #f0f2f5;
}
.left-sidebar {
  width: 260px;
  background: #fff;
  border-right: 1px solid #ebeef5;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  .sidebar-header {
    padding: 16px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    h2 { font-size: 16px; font-weight: 600; margin: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  }
  .sidebar-search { padding: 0 16px 12px; }
  .chapter-list {
    flex: 1;
    overflow-y: auto;
    padding: 0 8px;
  }
  .chapter-item {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 12px;
    border-radius: 6px;
    cursor: pointer;
    font-size: 13px;
    transition: background 0.15s;
    &:hover { background: #f5f7fa; }
    &.active { background: #ecf5ff; color: #409eff; }
    .chapter-num { color: #909399; font-size: 12px; min-width: 24px; }
    .chapter-title { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
    .chapter-words { color: #c0c4cc; font-size: 11px; }
  }
  .sidebar-footer {
    padding: 12px 16px;
    font-size: 12px;
    color: #909399;
    border-top: 1px solid #ebeef5;
    text-align: center;
  }
  .sidebar-empty, .sidebar-loading { padding: 24px 16px; text-align: center; color: #909399; }
}
.main-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}
.top-nav {
  display: flex;
  gap: 6px;
  padding: 12px 16px;
  background: #fff;
  border-bottom: 1px solid #ebeef5;
  overflow-x: auto;
  flex-shrink: 0;
}
.content-area {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}
</style>
