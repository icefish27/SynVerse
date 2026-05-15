<template>
  <div class="style-rag-page">
    <h2>仿写知识库引擎</h2>
    <p class="desc">上传优秀小说 txt 文件 → 自动切片 → 向量化入库 → AI 写作时检索范例</p>

    <!-- 上传区 -->
    <div class="upload-section">
      <el-upload
        ref="uploadRef"
        :auto-upload="false"
        :limit="10"
        accept=".txt"
        :on-change="handleFileChange"
        :file-list="fileList"
        drag
      >
        <el-icon :size="40"><UploadFilled /></el-icon>
        <div class="upload-text">将 txt 小说文件拖到此处，或点击选择</div>
        <template #tip>
          <div class="upload-tip">支持 txt 文件，自动过滤章节标题和噪声行，切片 200-500 字/段</div>
        </template>
      </el-upload>
      <el-button type="primary" :loading="uploading" @click="handleUpload" :disabled="fileList.length === 0" style="margin-top:12px">
        上传并入库
      </el-button>
    </div>

    <!-- 检索区 -->
    <div class="search-section">
      <h3>检索相似段落</h3>
      <div class="search-row">
        <el-input v-model="searchQuery" placeholder="输入场景描述，检索相似范例..." clearable @keyup.enter="handleSearch" />
        <el-select v-model="searchScene" placeholder="场景类型" clearable style="width:140px">
          <el-option label="日常" value="日常" />
          <el-option label="打斗" value="打斗" />
          <el-option label="打脸" value="打脸" />
          <el-option label="修炼" value="修炼" />
          <el-option label="感情" value="感情" />
          <el-option label="阴谋" value="阴谋" />
        </el-select>
        <el-button type="primary" @click="handleSearch" :loading="searching">检索</el-button>
      </div>
      <div v-if="knowledgeStore.searchResults.length > 0" class="search-results">
        <div v-for="(r, i) in knowledgeStore.searchResults" :key="i" class="result-item">
          <div class="result-header">
            <el-tag size="small">{{ r.scene_type || '未分类' }}</el-tag>
            <span class="result-source">{{ r.source_name }}</span>
            <span class="result-score">相似度: {{ (r.similarity * 100).toFixed(1) }}%</span>
          </div>
          <p class="result-content">{{ r.content }}</p>
        </div>
      </div>
    </div>

    <!-- 文档列表 -->
    <div class="doc-section">
      <div class="doc-header">
        <h3>已入库文档</h3>
        <el-button size="small" @click="knowledgeStore.fetchDocuments()" :loading="knowledgeStore.loading">刷新</el-button>
      </div>
      <el-table :data="knowledgeStore.documents" v-if="knowledgeStore.documents.length > 0" size="small">
        <el-table-column prop="filename" label="文件名" />
        <el-table-column prop="chunk_count" label="切片数" width="80" />
        <el-table-column prop="total_chars" label="总字数" width="100" />
        <el-table-column prop="status" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.status === 'ready' ? 'success' : 'warning'" size="small">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="80">
          <template #default="{ row }">
            <el-button size="small" type="danger" text @click="handleDelete(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div v-else-if="!knowledgeStore.loading" class="doc-empty">
        <el-empty description="暂无文档，上传 txt 文件开始构建知识库" :image-size="80" />
      </div>
    </div>

    <!-- 精选范例管理 -->
    <div class="examples-section">
      <div class="doc-header">
        <h3>精选范例</h3>
        <el-select v-model="exampleSceneFilter" placeholder="场景筛选" clearable size="small" style="width:120px" @change="loadExamples">
          <el-option label="日常" value="日常" /><el-option label="打斗" value="打斗" />
          <el-option label="打脸" value="打脸" /><el-option label="修炼" value="修炼" />
          <el-option label="感情" value="感情" /><el-option label="阴谋" value="阴谋" />
        </el-select>
        <el-button size="small" type="primary" @click="showAddExample = true">添加范例</el-button>
      </div>
      <div v-if="knowledgeStore.examples.length === 0" class="doc-empty">
        <p style="color:#c0c4cc;font-size:13px">暂无精选范例，点击「添加范例」手动添加高质量片段</p>
      </div>
      <div v-for="ex in knowledgeStore.examples" :key="ex.id" class="example-card">
        <div class="example-meta">
          <el-tag size="small">{{ ex.scene_type }}</el-tag>
          <el-rate v-model="ex.quality_rating" size="small" disabled show-score text-color="#ff9900" />
          <el-button size="small" type="danger" text @click="handleDeleteExample(ex.id)">删除</el-button>
        </div>
        <p class="example-content">{{ ex.content }}</p>
      </div>
    </div>

    <!-- 添加范例弹窗 -->
    <el-dialog v-model="showAddExample" title="添加精选范例" width="500px">
      <el-form label-position="top">
        <el-form-item label="场景类型" required>
          <el-select v-model="newExample.scene_type" style="width:100%">
            <el-option label="日常" value="日常" /><el-option label="打斗" value="打斗" />
            <el-option label="打脸" value="打脸" /><el-option label="修炼" value="修炼" />
            <el-option label="感情" value="感情" /><el-option label="阴谋" value="阴谋" />
          </el-select>
        </el-form-item>
        <el-form-item label="范例内容" required>
          <el-input v-model="newExample.content" type="textarea" :rows="4" placeholder="粘贴优秀小说片段..." />
        </el-form-item>
        <el-form-item label="质量评分">
          <el-rate v-model="newExample.quality_rating" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddExample = false">取消</el-button>
        <el-button type="primary" :loading="addingExample" @click="handleAddExample">添加</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { UploadFilled } from "@element-plus/icons-vue";
import { useKnowledgeStore } from "@/store/useKnowledgeStore";
import { ElMessage } from "element-plus";

const knowledgeStore = useKnowledgeStore();
const fileList = ref([]);
const uploading = ref(false);
const searchQuery = ref("");
const searchScene = ref("");
const searching = ref(false);
const showAddExample = ref(false);
const addingExample = ref(false);
const exampleSceneFilter = ref("");
const newExample = ref({ scene_type: "日常", content: "", quality_rating: 3 });

onMounted(() => { knowledgeStore.fetchDocuments(); loadExamples(); });

function handleFileChange(file) { fileList.value.push(file); }

async function loadExamples() {
  await knowledgeStore.fetchExamples(exampleSceneFilter.value);
}

async function handleAddExample() {
  if (!newExample.value.content.trim()) return;
  addingExample.value = true;
  try {
    await knowledgeStore.createExample({ ...newExample.value });
    showAddExample.value = false;
    newExample.value = { scene_type: "日常", content: "", quality_rating: 3 };
    ElMessage.success("范例已添加");
  } finally { addingExample.value = false; }
}

async function handleDeleteExample(id) {
  await knowledgeStore.deleteExample(id);
  ElMessage.success("已删除");
}

async function handleUpload() {
  uploading.value = true;
  try {
    for (const f of fileList.value) {
      await knowledgeStore.uploadDocument(f.raw);
      ElMessage.success(`${f.name} 入库完成`);
    }
    fileList.value = [];
  } catch (e) {
    ElMessage.error("上传失败");
  } finally {
    uploading.value = false;
  }
}

async function handleSearch() {
  if (!searchQuery.value.trim()) return;
  searching.value = true;
  try {
    await knowledgeStore.search(searchQuery.value, searchScene.value);
  } finally {
    searching.value = false;
  }
}

async function handleDelete(id) {
  await knowledgeStore.deleteDocument(id);
  ElMessage.success("已删除");
}
</script>

<style scoped lang="scss">
.style-rag-page { max-width: 900px; }
h2 { font-size: 20px; margin-bottom: 8px; }
.desc { color: #909399; font-size: 13px; margin-bottom: 24px; }
.upload-section { margin-bottom: 32px; }
.upload-text { margin-top: 8px; color: #909399; font-size: 13px; }
.upload-tip { color: #c0c4cc; font-size: 12px; margin-top: 8px; }
.search-section {
  margin-bottom: 32px;
  h3 { font-size: 16px; margin-bottom: 12px; }
  .search-row { display: flex; gap: 12px; }
}
.search-results { margin-top: 16px; }
.result-item {
  padding: 12px;
  background: #fff;
  border-radius: 8px;
  margin-bottom: 8px;
  border: 1px solid #ebeef5;
  .result-header { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
  .result-source { font-size: 12px; color: #909399; }
  .result-score { font-size: 12px; color: #67c23a; margin-left: auto; }
  .result-content { font-size: 13px; line-height: 1.8; color: #303133; margin: 0; }
}
.doc-section {
  .doc-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; h3 { font-size: 16px; } }
}
.doc-empty { padding: 40px 0; }
.examples-section {
  margin-top: 32px;
  .doc-header { display: flex; justify-content: flex-start; align-items: center; gap: 12px; margin-bottom: 12px; h3 { font-size: 16px; margin: 0; } }
  .example-card {
    padding: 12px;
    background: #fff;
    border: 1px solid #ebeef5;
    border-radius: 8px;
    margin-bottom: 8px;
    .example-meta { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
    .example-content { font-size: 13px; line-height: 1.8; color: #303133; margin: 0; white-space: pre-wrap; }
  }
}
</style>
