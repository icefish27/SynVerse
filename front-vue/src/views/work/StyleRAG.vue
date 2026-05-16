<template>
  <div class="style-rag-page">
    <h2>仿写知识库引擎</h2>
    <p class="desc">上传优秀小说 txt 文件 → 后台自动切片+向量化 → AI 写作时检索范例</p>

    <!-- 上传区 -->
    <div class="upload-section">
      <el-upload
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
          <div class="upload-tip">先上传到服务器，再点击「处理」进行切片和向量化。支持 MD5 去重。</div>
        </template>
      </el-upload>
      <el-button type="primary" :loading="uploading" @click="handleUploadAndProcess" :disabled="fileList.length === 0" style="margin-top:12px">
        {{ uploading ? "上传中..." : "上传并入库" }}
      </el-button>
    </div>

    <!-- 文档列表 + 进度 -->
    <div class="doc-section">
      <div class="doc-header">
        <h3>已入库文档</h3>
        <el-button size="small" @click="knowledgeStore.fetchDocuments()" :loading="knowledgeStore.loading">刷新</el-button>
      </div>

      <div v-if="documents.length === 0 && !knowledgeStore.loading" class="doc-empty">
        <el-empty description="暂无文档，上传 txt 文件开始构建知识库" :image-size="80" />
      </div>

      <div v-for="doc in documents" :key="doc.id" class="doc-card" :class="{ expanded: expandedDoc === doc.id }">
        <div class="doc-card-header" @click="toggleDoc(doc.id)">
          <div class="doc-info">
            <span class="doc-name">{{ doc.filename }}</span>
            <el-tag :type="statusTag(doc.status)" size="small">{{ statusLabel(doc.status) }}</el-tag>
            <span class="doc-meta">{{ doc.chunk_count }} 切片 · {{ doc.total_chars }} 字</span>
          </div>
          <div class="doc-actions" @click.stop>
            <el-button
              v-if="doc.status === 'uploaded'"
              size="small" type="primary"
              @click="handleProcess(doc.id)"
            >处理</el-button>
            <el-button size="small" @click="handleViewContent(doc.id)">查看原文</el-button>
            <el-popconfirm title="确定删除？" @confirm="handleDelete(doc.id)">
              <template #reference>
                <el-button size="small" type="danger" text>删除</el-button>
              </template>
            </el-popconfirm>
          </div>
        </div>

        <!-- 进度面板 -->
        <div v-if="expandedDoc === doc.id && (doc.status === 'processing' || doc.status === 'ready' || doc.status === 'error')" class="progress-panel">
          <div class="progress-header">
            <el-icon :size="14" :class="{ 'is-loading': doc.status === 'processing' }"><Loading /></el-icon>
            <span>{{ doc.status === 'processing' ? '处理中' : doc.status === 'error' ? '处理失败' : '处理完成' }}</span>
            <span v-if="doc.status === 'processing'" class="progress-pct">{{ doc.processing_progress }}%</span>
            <span v-if="doc.status === 'processing' && etaText(doc)" class="progress-eta">{{ etaText(doc) }}</span>
            <el-tag v-if="doc.status === 'ready'" type="success" size="small">完成</el-tag>
            <el-tag v-if="doc.status === 'error'" type="danger" size="small">失败</el-tag>
          </div>
          <div class="progress-bar-wrap">
            <div class="progress-bar" :style="{ width: doc.processing_progress + '%' }" :class="{ done: doc.status === 'ready', error: doc.status === 'error' }"></div>
          </div>
          <div class="progress-log">
            <div v-for="(log, i) in (doc.processing_log || [])" :key="i" class="log-line" :class="log.stage">
              <span class="log-icon">{{ logIcon(log.stage) }}</span>
              <span class="log-msg">{{ log.message }}</span>
              <span v-if="log.detail" class="log-detail">{{ log.detail }}</span>
            </div>
            <div v-if="(doc.processing_log || []).length === 0 && doc.status === 'processing'" class="log-line">
              <span class="log-icon">⏳</span>
              <span class="log-msg">等待服务器处理...</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 查看原文弹窗 -->
    <el-dialog v-model="showContent" title="文件内容预览" width="800px" top="5vh">
      <div class="content-preview"><pre>{{ fileContent }}</pre></div>
    </el-dialog>

    <div style="height: 40px"></div>

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
import { ref, onMounted, onUnmounted, computed } from "vue";
import { UploadFilled, Loading } from "@element-plus/icons-vue";
import { useKnowledgeStore } from "@/store/useKnowledgeStore";
import { ElMessage, ElNotification } from "element-plus";

const knowledgeStore = useKnowledgeStore();
const fileList = ref([]);
const uploading = ref(false);
const expandedDoc = ref(null);

const documents = computed(() => knowledgeStore.documents);
const showContent = ref(false);
const fileContent = ref("");

const searchQuery = ref("");
const searchScene = ref("");
const searching = ref(false);
const showAddExample = ref(false);
const addingExample = ref(false);
const exampleSceneFilter = ref("");
const newExample = ref({ scene_type: "日常", content: "", quality_rating: 3 });

onMounted(async () => {
  await knowledgeStore.fetchDocuments();
  loadExamples();
  // 恢复轮询：如果有正在处理的文档，重新开始轮询
  resumeProcessingDocs();
});

onUnmounted(() => {
  knowledgeStore.stopPolling();
});

function resumeProcessingDocs() {
  const processing = documents.value.find(d => d.status === "processing");
  if (processing) {
    expandedDoc.value = processing.id;
    knowledgeStore.startPolling(processing.id, (progress) => {
      if (progress.status === "ready") {
        ElNotification({
          title: "RAG 入库完成",
          message: `${progress.filename} — ${progress.chunk_count} 切片 · ${progress.total_chars} 字`,
          type: "success",
          duration: 6000,
        });
      }
    });
  }
}

function statusTag(status) {
  const map = { uploaded: "info", processing: "warning", ready: "success", error: "danger" };
  return map[status] || "info";
}

function statusLabel(status) {
  const map = { uploaded: "待处理", processing: "处理中", ready: "已完成", error: "失败" };
  return map[status] || status;
}

const etaMap = {};

function etaText(doc) {
  if (!doc.processing_progress || doc.processing_progress <= 10 || doc.processing_progress >= 99) return "";
  const now = Date.now();
  if (!etaMap[doc.id]) {
    etaMap[doc.id] = { startTime: now, startProgress: doc.processing_progress };
    return "";
  }
  const entry = etaMap[doc.id];
  if (doc.processing_progress <= entry.startProgress) {
    entry.startTime = now;
    entry.startProgress = doc.processing_progress;
    return "";
  }
  const elapsed = (now - entry.startTime) / 1000;
  const progressDelta = doc.processing_progress - entry.startProgress;
  const totalEstimated = (elapsed / progressDelta) * (100 - doc.processing_progress);
  if (totalEstimated < 60) return `预计还需 ${Math.round(totalEstimated)} 秒`;
  if (totalEstimated < 3600) return `预计还需 ${Math.round(totalEstimated / 60)} 分钟`;
  return `预计还需 ${Math.round(totalEstimated / 3600)} 小时`;
}

function logIcon(stage) {
  const map = {
    reading: "📄", chunking: "✂️", embedding: "🧠",
    classifying: "🏷️", saving: "📥", done: "✅", error: "❌",
  };
  return map[stage] || "⏳";
}

function toggleDoc(docId) {
  expandedDoc.value = expandedDoc.value === docId ? null : docId;
}

function handleFileChange(file) {
  fileList.value.push(file);
}

async function handleUploadAndProcess() {
  uploading.value = true;
  for (const f of fileList.value) {
    let doc;
    try {
      doc = await knowledgeStore.uploadDocument(f.raw);
    } catch (e) {
      if (e?.response?.status === 409 || e?.code === "duplicate") {
        ElMessage.warning(e?.detail || `${f.name} 已存在`);
        continue;
      }
      ElMessage.error(`${f.name} 上传失败`);
      continue;
    }

    // 上传成功后自动开始处理
    ElMessage.success(`${f.name} 上传完成，开始入库...`);
    expandedDoc.value = doc.id;
    await knowledgeStore.startProcessing(doc.id);
    knowledgeStore.startPolling(doc.id, (progress) => {
      if (progress.status === "ready") {
        ElNotification({
          title: "RAG 入库完成",
          message: `${progress.filename} — ${progress.chunk_count} 切片 · ${progress.total_chars} 字`,
          type: "success",
          duration: 6000,
        });
      }
    });

    // 更新本地文档状态
    const localDoc = documents.value.find(d => d.id === doc.id);
    if (localDoc) {
      localDoc.status = "processing";
      localDoc.processing_progress = 0;
      localDoc.processing_log = [{ stage: "start", message: "上传完成，开始处理...", detail: "", progress: 0 }];
    }
  }
  fileList.value = [];
  uploading.value = false;
  knowledgeStore.fetchDocuments();
}

async function handleProcess(docId) {
  expandedDoc.value = docId;
  await knowledgeStore.startProcessing(docId);
  knowledgeStore.startPolling(docId, (progress) => {
    if (progress.status === "ready") {
      ElNotification({
        title: "RAG 入库完成",
        message: `${progress.filename} — ${progress.chunk_count} 切片 · ${progress.total_chars} 字`,
        type: "success",
        duration: 6000,
      });
    }
  });
  // 更新本地文档状态
  const doc = documents.value.find(d => d.id === docId);
  if (doc) {
    doc.status = "processing";
    doc.processing_progress = 0;
    doc.processing_log = [];
  }
}

async function handleViewContent(docId) {
  try {
    fileContent.value = await knowledgeStore.fetchContent(docId);
    showContent.value = true;
  } catch {
    ElMessage.error("无法读取文件内容");
  }
}

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

/* 文档卡片 */
.doc-section {
  margin-bottom: 32px;
  .doc-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; h3 { font-size: 16px; margin: 0; } }
}
.doc-empty { padding: 40px 0; }

.doc-card {
  background: #fff;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  margin-bottom: 8px;
  overflow: hidden;
  .doc-card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 16px;
    cursor: pointer;
    transition: background 0.15s;
    &:hover { background: #fafafa; }
    .doc-info {
      display: flex;
      align-items: center;
      gap: 10px;
      flex: 1;
      min-width: 0;
      .doc-name { font-weight: 500; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
      .doc-meta { color: #909399; font-size: 12px; }
    }
    .doc-actions { display: flex; gap: 6px; flex-shrink: 0; margin-left: 12px; }
  }
}

/* 进度面板 */
.progress-panel {
  border-top: 1px solid #ebeef5;
  background: #1a1b2e;
  padding: 16px 20px;
  font-family: "SF Mono", "Menlo", "Monaco", monospace;
  .progress-header {
    display: flex;
    align-items: center;
    gap: 8px;
    color: #a8b2d1;
    font-size: 13px;
    margin-bottom: 10px;
    .progress-pct { color: #64ffda; }
    .progress-eta { color: #8892b0; font-size: 11px; }
    .el-tag { margin-left: auto; }
  }
  .progress-bar-wrap {
    height: 4px;
    background: rgba(255,255,255,0.08);
    border-radius: 2px;
    margin-bottom: 12px;
    overflow: hidden;
    .progress-bar {
      height: 100%;
      background: linear-gradient(90deg, #64ffda, #48c6ef);
      border-radius: 2px;
      transition: width 0.5s;
      &.done { background: #64ffda; }
      &.error { background: #ff6b6b; }
    }
  }
  .progress-log {
    max-height: 180px;
    overflow-y: auto;
    font-size: 12px;
    line-height: 1.8;
    &::-webkit-scrollbar { width: 4px; }
    &::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 2px; }
    .log-line {
      display: flex;
      gap: 8px;
      color: #8892b0;
      .log-icon { flex-shrink: 0; }
      .log-msg { color: #ccd6f6; }
      .log-detail { color: #5a6a8a; margin-left: auto; font-size: 11px; }
      &.done { color: #64ffda; .log-msg { color: #64ffda; } }
      &.error { color: #ff6b6b; .log-msg { color: #ff6b6b; } }
    }
  }
}

/* 内容预览 */
.content-preview {
  max-height: 70vh;
  overflow: auto;
  pre { white-space: pre-wrap; font-size: 13px; line-height: 1.8; margin: 0; }
}

.search-section {
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
.examples-section {
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
