<template>
  <div class="dashboard">
    <header class="dashboard-header">
      <div class="header-left">
        <h1>我的小说</h1>
        <span class="novel-count">共 {{ novelStore.novelCount }} 部作品</span>
      </div>
      <div class="header-right">
        <el-button type="primary" @click="showCreate = true">
          <el-icon><Plus /></el-icon> 创建小说
        </el-button>
      </div>
    </header>

    <div class="toolbar">
      <el-input
        v-model="searchQuery"
        placeholder="搜索小说标题..."
        :prefix-icon="Search"
        clearable
        class="search-input"
        @input="onSearch"
      />
      <el-select
        v-model="sortBy"
        placeholder="排序"
        class="tool-select"
        @change="onSort"
      >
        <el-option label="更新时间" value="updated_at" />
        <el-option label="创建时间" value="created_at" />
      </el-select>
      <el-select
        v-model="filterTag"
        placeholder="筛选"
        class="tool-select"
        clearable
        @change="onFilter"
      >
        <el-option label="爽文" value="爽文" />
        <el-option label="种田文" value="种田文" />
        <el-option label="系统流" value="系统流" />
        <el-option label="玄幻" value="玄幻" />
        <el-option label="都市" value="都市" />
        <el-option label="仙侠" value="仙侠" />
        <el-option label="穿越" value="穿越" />
        <el-option label="重生" value="重生" />
        <el-option label="科幻" value="科幻" />
        <el-option label="言情" value="言情" />
        <el-option label="历史" value="历史" />
        <el-option label="军事" value="军事" />
        <el-option label="游戏" value="游戏" />
        <el-option label="竞技" value="竞技" />
        <el-option label="悬疑" value="悬疑" />
        <el-option label="推理" value="推理" />
        <el-option label="恐怖" value="恐怖" />
        <el-option label="灵异" value="灵异" />
        <el-option label="轻小说" value="轻小说" />
        <el-option label="同人" value="同人" />
      </el-select>
    </div>

    <!-- 空状态 -->
    <div
      v-if="!novelStore.loading && novelStore.novels.length === 0"
      class="empty-state"
    >
      <el-empty description="还没有作品，创建你的第一部小说吧">
        <el-button type="primary" @click="showCreate = true"
          >创建小说</el-button
        >
      </el-empty>
    </div>

    <!-- 加载 -->
    <div v-if="novelStore.loading" class="loading-state">
      <el-skeleton :rows="3" animated />
    </div>

    <!-- 卡片列表 -->
    <div
      v-if="!novelStore.loading && novelStore.novels.length > 0"
      class="novel-grid"
    >
      <div
        v-for="novel in novelStore.novels"
        :key="novel.id"
        class="novel-card"
        @click="openNovel(novel)"
      >
        <div class="card-cover">
          <img v-if="novel.cover_url" :src="fixCoverUrl(novel.cover_url)" alt="" />
          <div v-else class="cover-placeholder">
            <el-icon :size="48"><Notebook /></el-icon>
          </div>
          <div class="cover-overlay">
            <p>{{ novel.description || "暂无简介" }}</p>
          </div>
        </div>
        <div class="card-info">
          <h3>{{ novel.title }}</h3>
          <div class="card-tags">
            <el-tag
              v-for="tag in novel.type_tags || []"
              :key="tag"
              size="small"
              >{{ tag }}</el-tag
            >
          </div>
          <div class="card-meta">
            <span
              >{{ novel.total_chapters }} 章 · {{ novel.total_words }} 字</span
            >
            <span class="meta-time">{{ formatTime(novel.updated_at) }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 创建弹窗 -->
    <el-dialog
      v-model="showCreate"
      title="创建小说"
      width="500px"
      :close-on-click-modal="false"
    >
      <el-form :model="createForm" label-position="top">
        <el-form-item label="书名" required>
          <el-input
            v-model="createForm.title"
            placeholder="7-10字最佳，含热词≥2个"
          />
        </el-form-item>
        <el-form-item label="简介">
          <el-input
            v-model="createForm.description"
            type="textarea"
            :rows="3"
            placeholder="直接亮卖点，别写慢热/前期铺垫"
          />
        </el-form-item>
        <el-form-item label="类型标签">
          <el-checkbox-group v-model="createForm.type_tags">
            <el-checkbox value="爽文">爽文</el-checkbox>
            <el-checkbox value="种田文">种田文</el-checkbox>
            <el-checkbox value="系统流">系统流</el-checkbox>
            <el-checkbox value="玄幻">玄幻</el-checkbox>
            <el-checkbox value="都市">都市</el-checkbox>
            <el-checkbox value="仙侠">仙侠</el-checkbox>
            <el-checkbox value="穿越">穿越</el-checkbox>
            <el-checkbox value="重生">重生</el-checkbox>
            <el-checkbox value="科幻">科幻</el-checkbox>
            <el-checkbox value="言情">言情</el-checkbox>
            <el-checkbox value="历史">历史</el-checkbox>
            <el-checkbox value="军事">军事</el-checkbox>
            <el-checkbox value="游戏">游戏</el-checkbox>
            <el-checkbox value="竞技">竞技</el-checkbox>
            <el-checkbox value="悬疑">悬疑</el-checkbox>
            <el-checkbox value="推理">推理</el-checkbox>
            <el-checkbox value="恐怖">恐怖</el-checkbox>
            <el-checkbox value="灵异">灵异</el-checkbox>
            <el-checkbox value="轻小说">轻小说</el-checkbox>
            <el-checkbox value="同人">同人</el-checkbox>
          </el-checkbox-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreate = false">取消</el-button>
        <el-button type="primary" :loading="creating" @click="onCreate"
          >创建</el-button
        >
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import { Plus, Search, Notebook } from "@element-plus/icons-vue";
import { useNovelStore } from "@/store/useNovelStore";
import dayjs from "dayjs";
import relativeTime from "dayjs/plugin/relativeTime";
import "dayjs/locale/zh-cn";
dayjs.extend(relativeTime);
dayjs.locale("zh-cn");

const router = useRouter();
const novelStore = useNovelStore();

const searchQuery = ref("");
const sortBy = ref("updated_at");
const filterTag = ref(null);
const showCreate = ref(false);
const creating = ref(false);

const createForm = ref({
  title: "",
  description: "",
  type_tags: [],
});

onMounted(() => {
  novelStore.fetchNovels();
});

function onSearch() {
  novelStore.fetchNovels({
    search: searchQuery.value,
    sort: sortBy.value,
    tag: filterTag.value,
  });
}
function onSort() {
  novelStore.fetchNovels({
    search: searchQuery.value,
    sort: sortBy.value,
    tag: filterTag.value,
  });
}
function onFilter() {
  novelStore.fetchNovels({
    search: searchQuery.value,
    sort: sortBy.value,
    tag: filterTag.value,
  });
}

async function onCreate() {
  if (!createForm.value.title) return;
  creating.value = true;
  try {
    const novel = await novelStore.createNovel(createForm.value);
    showCreate.value = false;
    createForm.value = { title: "", description: "", type_tags: [] };
    openNovel(novel);
  } finally {
    creating.value = false;
  }
}

function openNovel(novel) {
  novelStore.setCurrentNovel(novel);
  router.push({ name: "AiChat", params: { id: novel.id } });
}

const apiBase = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
function fixCoverUrl(url) {
  if (!url) return "";
  return url.startsWith("http") ? url : apiBase + url;
}

function formatTime(t) {
  if (!t) return "";
  return dayjs(t).fromNow();
}
</script>

<style scoped lang="scss">
.dashboard {
  max-width: 1200px;
  margin: 0 auto;
  padding: 40px 24px;
}
.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  h1 {
    font-size: 28px;
    font-weight: 700;
    margin: 0;
  }
  .novel-count {
    color: #909399;
    font-size: 14px;
    margin-left: 12px;
  }
}
.toolbar {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
  .search-input {
    width: 280px;
  }
  .tool-select {
    width: 140px;
  }
}
.empty-state,
.loading-state {
  display: flex;
  justify-content: center;
  padding: 80px 0;
}
.novel-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 20px;
}
.novel-card {
  background: #fff;
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
  transition:
    box-shadow 0.2s,
    transform 0.2s;
  &:hover {
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.12);
    transform: translateY(-2px);
  }
  .card-cover {
    position: relative;
    height: 200px;
    background: #f5f7fa;
    overflow: hidden;
    img {
      width: 100%;
      height: 100%;
      object-fit: cover;
    }
    .cover-placeholder {
      display: flex;
      align-items: center;
      justify-content: center;
      height: 100%;
      color: #c0c4cc;
    }
    .cover-overlay {
      position: absolute;
      inset: 0;
      background: rgba(0, 0, 0, 0.6);
      color: #fff;
      display: flex;
      align-items: center;
      padding: 16px;
      opacity: 0;
      transition: opacity 0.2s;
      p {
        font-size: 13px;
        line-height: 1.6;
      }
    }
    &:hover .cover-overlay {
      opacity: 1;
    }
  }
  .card-info {
    padding: 12px 16px 16px;
    h3 {
      font-size: 16px;
      font-weight: 600;
      margin: 0 0 8px;
    }
    .card-tags {
      display: flex;
      gap: 4px;
      flex-wrap: wrap;
      margin-bottom: 8px;
    }
    .card-meta {
      font-size: 12px;
      color: #909399;
      display: flex;
      justify-content: space-between;
    }
  }
}
</style>
