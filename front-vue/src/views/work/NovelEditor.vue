<template>
  <div class="novel-editor-page">
    <div v-if="!chapterStore.currentChapter" class="empty-state">
      <el-empty description="暂无章节内容">
        <template #image>
          <el-icon :size="64" color="#c0c4cc"><Notebook /></el-icon>
        </template>
        <el-button type="primary" @click="$router.push({ name: 'AiChat', params: { id: $route.params.id } })">
          去 AI 模式开启新章
        </el-button>
      </el-empty>
    </div>
    <div v-else class="editor-area">
      <div class="editor-toolbar">
        <h3>{{ chapterStore.currentChapter.title || `第${chapterStore.currentChapter.chapter_number}章` }}</h3>
        <span class="word-count">{{ chapterStore.currentChapter.word_count }} 字</span>
      </div>
      <div class="editor-content" v-html="renderedContent" />
      <p class="placeholder-note">此处将集成 Tiptap 富文本编辑器</p>
    </div>
  </div>
</template>

<script setup>
import { computed } from "vue";
import { Notebook } from "@element-plus/icons-vue";
import { useChapterStore } from "@/store/useChapterStore";

const chapterStore = useChapterStore();

const renderedContent = computed(() => {
  const c = chapterStore.currentChapter?.content || "";
  return c.replace(/\n/g, "<br>");
});
</script>

<style scoped lang="scss">
.novel-editor-page {
  height: 100%;
  .empty-state {
    display: flex;
    align-items: center;
    justify-content: center;
    height: 100%;
  }
  .editor-toolbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 24px;
    padding-bottom: 16px;
    border-bottom: 1px solid #ebeef5;
    h3 { margin: 0; font-size: 22px; }
    .word-count { color: #909399; font-size: 13px; }
  }
  .editor-content {
    max-width: 800px;
    margin: 0 auto;
    line-height: 2;
    font-size: 16px;
    color: #303133;
  }
  .placeholder-note { text-align: center; color: #c0c4cc; font-size: 12px; margin-top: 40px; }
}
</style>
