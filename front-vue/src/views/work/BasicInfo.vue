<template>
  <div class="basic-info-page">
    <div v-if="novelStore.currentNovel" class="info-form">
      <h2>基本信息</h2>

      <!-- 封面上传 -->
      <div class="cover-section">
        <div class="cover-preview" :class="{ uploading }" @click="triggerUpload">
          <img v-if="coverUrl" :src="coverUrl" alt="封面" />
          <div v-else class="cover-placeholder">
            <el-icon :size="48"><Camera /></el-icon>
            <span>点击上传封面</span>
          </div>
          <div class="cover-overlay">
            <el-icon v-if="!uploading" :size="24"><Edit /></el-icon>
            <el-icon v-else class="is-loading" :size="24"><Loading /></el-icon>
          </div>
        </div>
        <input
          ref="fileInput"
          type="file"
          accept="image/*"
          style="display:none"
          @change="handleFileChange"
        />
        <p class="cover-hint">推荐尺寸 600x800，支持 jpg/png</p>
      </div>

      <el-form :model="form" label-position="top" style="max-width: 600px;">
        <el-form-item label="书名">
          <el-input v-model="form.title" />
        </el-form-item>
        <el-form-item label="简介">
          <el-input v-model="form.description" type="textarea" :rows="4" />
        </el-form-item>
        <el-form-item label="类型标签">
          <el-checkbox-group v-model="form.type_tags">
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
import { ref, reactive, watch, onMounted, computed } from "vue";
import { useNovelStore } from "@/store/useNovelStore";
import { ElMessage } from "element-plus";
import { Camera, Edit, Loading } from "@element-plus/icons-vue";
import { request } from "@/utils/request";

const novelStore = useNovelStore();
const saving = ref(false);
const uploading = ref(false);
const fileInput = ref(null);

const form = reactive({
  title: "",
  description: "",
  type_tags: [],
  target_chapters: 500,
  target_words: 2000,
});

const baseUrl = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
const coverUrl = computed(() => {
  const url = novelStore.currentNovel?.cover_url;
  if (!url) return "";
  return url.startsWith("http") ? url : baseUrl + url;
});

onMounted(() => {
  syncForm();
});

watch(() => novelStore.currentNovel, () => {
  syncForm();
});

function syncForm() {
  if (novelStore.currentNovel) {
    Object.assign(form, {
      title: novelStore.currentNovel.title,
      description: novelStore.currentNovel.description || "",
      type_tags: novelStore.currentNovel.type_tags || [],
      target_chapters: novelStore.currentNovel.target_chapters,
      target_words: novelStore.currentNovel.target_words,
    });
  }
}

function triggerUpload() {
  fileInput.value?.click();
}

async function handleFileChange(e) {
  const file = e.target.files?.[0];
  if (!file) return;
  uploading.value = true;
  try {
    const formData = new FormData();
    formData.append("file", file);
    const data = await request({
      url: `/api/novels/${novelStore.currentNovel.id}/cover`,
      method: "post",
      data: formData,
      headers: { "Content-Type": "multipart/form-data" },
      timeout: 30000,
    });
    novelStore.currentNovel.cover_url = data.cover_url;
    ElMessage.success("封面上传成功");
  } catch {
    ElMessage.error("上传失败");
  } finally {
    uploading.value = false;
    if (fileInput.value) fileInput.value.value = "";
  }
}

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

.cover-section {
  margin-bottom: 24px;
  .cover-preview {
    width: 180px;
    height: 240px;
    border-radius: 8px;
    border: 2px dashed #dcdfe6;
    cursor: pointer;
    position: relative;
    overflow: hidden;
    transition: border-color 0.2s;
    &:hover { border-color: #409eff; }
    img { width: 100%; height: 100%; object-fit: cover; }
    .cover-placeholder {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      height: 100%;
      color: #c0c4cc;
      gap: 8px;
      font-size: 13px;
    }
    .cover-overlay {
      position: absolute;
      inset: 0;
      background: rgba(0,0,0,0.5);
      display: flex;
      align-items: center;
      justify-content: center;
      color: #fff;
      opacity: 0;
      transition: opacity 0.2s;
    }
    &:hover .cover-overlay { opacity: 1; }
    &.uploading {
      pointer-events: none;
      opacity: 0.7;
    }
  }
  .cover-hint { font-size: 12px; color: #c0c4cc; margin-top: 6px; }
}
</style>
