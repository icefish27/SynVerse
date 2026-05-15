<template>
  <div class="basic-info-page">
    <div v-if="novelStore.currentNovel" class="info-form">
      <h2>基本信息</h2>
      <el-form :model="form" label-position="top" style="max-width: 600px;">
        <el-form-item label="书名">
          <el-input v-model="form.title" />
        </el-form-item>
        <el-form-item label="简介">
          <el-input v-model="form.description" type="textarea" :rows="4" />
        </el-form-item>
        <el-form-item label="类型标签">
          <el-checkbox-group v-model="form.type_tags">
            <el-checkbox label="爽文" />
            <el-checkbox label="种田文" />
            <el-checkbox label="系统流" />
            <el-checkbox label="玄幻" />
            <el-checkbox label="都市" />
            <el-checkbox label="仙侠" />
            <el-checkbox label="穿越" />
          </el-checkbox-group>
        </el-form-item>
        <el-form-item label="目标章节数">
          <el-input-number v-model="form.target_chapters" :min="1" :max="9999" />
        </el-form-item>
        <el-form-item label="目标每章字数">
          <el-input-number v-model="form.target_words" :min="500" :step="500" :max="20000" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="saving" @click="save">保存</el-button>
        </el-form-item>
      </el-form>
    </div>
    <div v-else class="empty-state">
      <el-empty description="请先选择一部小说" />
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, watch, onMounted } from "vue";
import { useNovelStore } from "@/store/useNovelStore";
import { ElMessage } from "element-plus";

const novelStore = useNovelStore();
const saving = ref(false);

const form = reactive({
  title: "",
  description: "",
  type_tags: [],
  target_chapters: 500,
  target_words: 2000,
});

onMounted(() => {
  if (novelStore.currentNovel) {
    Object.assign(form, {
      title: novelStore.currentNovel.title,
      description: novelStore.currentNovel.description || "",
      type_tags: novelStore.currentNovel.type_tags || [],
      target_chapters: novelStore.currentNovel.target_chapters,
      target_words: novelStore.currentNovel.target_words,
    });
  }
});

watch(() => novelStore.currentNovel, (n) => {
  if (n) Object.assign(form, { title: n.title, description: n.description || "", type_tags: n.type_tags || [], target_chapters: n.target_chapters, target_words: n.target_words });
});

async function save() {
  saving.value = true;
  try {
    await novelStore.updateNovel(novelStore.currentNovel.id, { ...form });
    ElMessage.success("保存成功");
  } finally {
    saving.value = false;
  }
}
</script>

<style scoped lang="scss">
.basic-info-page {
  max-width: 800px;
  h2 { font-size: 20px; margin-bottom: 24px; }
  .empty-state { display: flex; align-items: center; justify-content: center; height: 400px; }
}
</style>
