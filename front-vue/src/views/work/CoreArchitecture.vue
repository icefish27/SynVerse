<template>
  <div class="core-arch-page">
    <h2>核心架构</h2>
    <p class="desc">填写核心设定，然后按卷生成大纲（每卷~200章），支持 AI 生成和手动修改。</p>

    <!-- 核心设定 -->
    <div class="seed-section">
      <h3>核心设定</h3>
      <el-form label-position="top" style="max-width: 800px;">
        <el-form-item label="核心种子">
          <el-input v-model="seed" type="textarea" :rows="3"
            placeholder="描述你的核心创意、核心矛盾、故事主线。例如：穿越成杂灵根废物，唯一的金手指是做梦就能变强..." />
        </el-form-item>
        <el-form-item label="角色设定">
          <el-input v-model="charSetting" type="textarea" :rows="4"
            placeholder="描述主角、配角、反派的姓名、性格、动机..." />
        </el-form-item>
        <el-form-item label="世界观">
          <el-input v-model="worldSetting" type="textarea" :rows="4"
            placeholder="描述世界规则、背景设定、修炼体系/魔法体系等..." />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="saving" @click="saveSeed">保存设定</el-button>
        </el-form-item>
      </el-form>
    </div>

    <!-- 卷管理 -->
    <div class="volumes-section">
      <div class="volumes-header">
        <h3>大纲分卷</h3>
        <el-button type="primary" @click="showAddVolume = true">
          <el-icon><Plus /></el-icon> 新增卷
        </el-button>
      </div>

      <div v-if="!volumes.length" class="empty-hint">
        <el-empty description="点击「新增卷」创建第一卷，或使用 AI 生成" :image-size="80">
          <el-button type="primary" @click="startGenerate(1)">AI 生成第一卷</el-button>
        </el-empty>
      </div>

      <!-- 卷卡片列表 -->
      <div v-for="vol in volumes" :key="vol.volume_number" class="volume-card">
        <div class="volume-header" @click="toggleVolume(vol.volume_number)">
          <div class="volume-title">
            <el-icon :size="20"><Folder /></el-icon>
            <span class="vol-num">第{{ vol.volume_number }}卷</span>
            <el-input
              v-if="editingVolNum === vol.volume_number"
              v-model="vol.title"
              size="small"
              class="vol-title-input"
              @click.stop
              @blur="saveVolumeTitle(vol)"
              @keyup.enter="saveVolumeTitle(vol)"
            />
            <span v-else class="vol-title-text" @dblclick.stop="editingVolNum = vol.volume_number">{{ vol.title || '未命名' }}</span>
            <span class="vol-ch-count">{{ vol.chapters?.length || 0 }} 章</span>
          </div>
          <div class="volume-actions" @click.stop>
            <el-button size="small" type="primary" :loading="generatingVol === vol.volume_number" @click="startGenerate(vol.volume_number)">AI 生成</el-button>
            <el-button size="small" @click="openEditVolume(vol)">编辑</el-button>
            <el-popconfirm title="确定删除此卷？" @confirm="handleDeleteVolume(vol.volume_number)">
              <template #reference>
                <el-button size="small" type="danger" text>删除</el-button>
              </template>
            </el-popconfirm>
          </div>
        </div>

        <!-- 展开的章节列表 -->
        <div v-if="expandedVol === vol.volume_number" class="volume-chapters">
          <div v-if="!vol.chapters?.length" class="vol-empty">
            <p>暂无章节，点击「AI 生成」或「编辑」添加章节</p>
          </div>
          <div v-for="ch in vol.chapters" :key="ch.chapter_number" class="chapter-row">
            <span class="ch-num">第{{ ch.chapter_number }}章</span>
            <span class="ch-title">{{ ch.title }}</span>
            <span class="ch-summary">{{ ch.summary }}</span>
          </div>
        </div>

        <!-- 生成进度 -->
        <div v-if="generatingVol === vol.volume_number" class="generating-box">
          <div class="thinking-header">
            <el-icon class="is-loading"><Loading /></el-icon>
            <span>AI 正在生成第{{ vol.volume_number }}卷大纲...</span>
          </div>
          <div v-if="streamReasoning" class="thinking-content">{{ streamReasoning }}</div>
          <div v-if="streamContent" class="stream-preview">
            <pre>{{ streamContent }}</pre>
          </div>
        </div>
      </div>
    </div>

    <!-- 新增卷弹窗 -->
    <el-dialog v-model="showAddVolume" title="新增卷" width="400px">
      <el-form label-position="top">
        <el-form-item label="卷号">
          <el-input-number v-model="newVolumeNum" :min="1" :max="99" />
        </el-form-item>
        <el-form-item label="卷标题">
          <el-input v-model="newVolumeTitle" placeholder="如：崛起、风云、决战" />
        </el-form-item>
        <el-form-item label="章数">
          <el-input-number v-model="newVolumeChapterCount" :min="10" :max="300" :step="10" />
          <span class="form-hint">推荐 200 章/卷</span>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddVolume = false">取消</el-button>
        <el-button type="primary" @click="handleAddVolume">创建空白卷</el-button>
        <el-button type="primary" :loading="generating" @click="handleAddAndGenerate">创建并 AI 生成</el-button>
      </template>
    </el-dialog>

    <!-- 编辑卷弹窗 -->
    <el-dialog v-model="showEditVolume" :title="`编辑第${editingVolume?.volume_number}卷`" width="700px" top="5vh">
      <div v-if="editingVolume" class="edit-volume">
        <el-form label-position="top" :inline="true">
          <el-form-item label="卷标题">
            <el-input v-model="editingVolume.title" />
          </el-form-item>
        </el-form>
        <h4>章节列表</h4>
        <div class="edit-chapters">
          <div v-for="(ch, idx) in editingChapters" :key="idx" class="edit-ch-row">
            <span class="ech-num">{{ ch.chapter_number }}</span>
            <el-input v-model="ch.title" placeholder="章名" size="small" class="ech-title" />
            <el-input v-model="ch.summary" placeholder="剧情概要" size="small" class="ech-summary" />
            <el-button size="small" type="danger" text @click="editingChapters.splice(idx, 1)">删</el-button>
          </div>
          <el-button size="small" @click="addChapterRow">+ 添加章节</el-button>
        </div>
      </div>
      <template #footer>
        <el-button @click="showEditVolume = false">取消</el-button>
        <el-button type="primary" :loading="savingVolume" @click="saveEditVolume">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from "vue";
import { useRoute } from "vue-router";
import { Plus, Folder, Loading } from "@element-plus/icons-vue";
import { useOutlineStore } from "@/store/useOutlineStore";
import { ElMessage } from "element-plus";

const route = useRoute();
const outlineStore = useOutlineStore();

const seed = ref("");
const charSetting = ref("");
const worldSetting = ref("");
const saving = ref(false);

const expandedVol = ref(null);
const generatingVol = ref(null);
const generating = ref(false);
const streamReasoning = ref("");
const streamContent = ref("");

const showAddVolume = ref(false);
const newVolumeNum = ref(1);
const newVolumeTitle = ref("");
const newVolumeChapterCount = ref(200);

const showEditVolume = ref(false);
const editingVolume = ref(null);
const editingChapters = ref([]);
const editingVolNum = ref(null);
const savingVolume = ref(false);

const volumes = computed(() => outlineStore.outline?.volumes || []);

let abortController = null;

async function loadOutlineData() {
  const id = route.params.id;
  if (!id) return;
  await outlineStore.fetchOutline(id);
  if (outlineStore.outline) {
    seed.value = outlineStore.outline.core_seed || "";
    charSetting.value = outlineStore.outline.character_setting || "";
    worldSetting.value = outlineStore.outline.world_setting || "";
  }
}

onMounted(() => {
  loadOutlineData();
});

watch(() => route.params.id, (newId, oldId) => {
  if (newId && newId !== oldId) {
    // 切换小说时重置展开状态并重新加载
    expandedVol.value = null;
    generatingVol.value = null;
    loadOutlineData();
  }
});

onUnmounted(() => {
  if (abortController) {
    abortController.abort();
    abortController = null;
  }
});

async function saveSeed() {
  saving.value = true;
  try {
    await outlineStore.updateOutline(route.params.id, {
      core_seed: seed.value,
      character_setting: charSetting.value,
      world_setting: worldSetting.value,
    });
    ElMessage.success("核心设定已保存");
  } finally {
    saving.value = false;
  }
}

function toggleVolume(volNum) {
  expandedVol.value = expandedVol.value === volNum ? null : volNum;
}

async function saveVolumeTitle(vol) {
  editingVolNum.value = null;
  await outlineStore.saveVolume(route.params.id, vol);
}

async function handleAddVolume() {
  const vol = {
    volume_number: newVolumeNum.value,
    title: newVolumeTitle.value || `第${newVolumeNum.value}卷`,
    chapters: [],
  };
  await outlineStore.saveVolume(route.params.id, vol);
  showAddVolume.value = false;
  ElMessage.success("空白卷已创建");
}

async function handleAddAndGenerate() {
  const vol = {
    volume_number: newVolumeNum.value,
    title: newVolumeTitle.value || `第${newVolumeNum.value}卷`,
    chapters: [],
  };
  await outlineStore.saveVolume(route.params.id, vol);
  showAddVolume.value = false;
  await generateVolume(newVolumeNum.value, newVolumeChapterCount.value);
}

async function handleDeleteVolume(volNum) {
  await outlineStore.deleteVolume(route.params.id, volNum);
  ElMessage.success("已删除");
}

function startGenerate(volNum) {
  generateVolume(volNum, 200);
}

async function generateVolume(volNum, chapterCount) {
  // 防止并发生成
  if (generating.value) return;

  if (!seed.value.trim()) {
    ElMessage.warning("请先保存核心设定");
    return;
  }
  await saveSeed();

  // 中止上一次未完成的请求
  if (abortController) {
    abortController.abort();
  }
  abortController = new AbortController();

  const baseUrl = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
  generating.value = true;
  generatingVol.value = volNum;
  streamReasoning.value = "";
  streamContent.value = "";

  try {
    const url = `${baseUrl}/api/novels/${route.params.id}/outline/generate?volume_number=${volNum}&chapter_count=${chapterCount}`;
    const resp = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      signal: abortController.signal,
    });
    if (!resp.ok) {
      throw new Error(`服务器返回 ${resp.status}`);
    }
    const reader = resp.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let buffer = "", eventType = "", contentBuf = [];

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() || "";

      for (const line of lines) {
        if (line.startsWith("event: ")) { eventType = line.slice(7).trim(); }
        else if (line.startsWith("data: ")) {
          try {
            const data = JSON.parse(line.slice(6));
            if (eventType === "reasoning" && data.content) {
              streamReasoning.value += data.content;
            } else if (eventType === "content" && data.content) {
              contentBuf.push(data.content);
              streamContent.value = contentBuf.join("");
            } else if (eventType === "done") {
              // 刷新大纲数据
            }
          } catch (e) { /* skip */ }
        }
      }
    }

    await outlineStore.fetchOutline(route.params.id);
    expandedVol.value = volNum;
    ElMessage.success(`第${volNum}卷大纲生成完成`);
  } catch (e) {
    if (e.name === "AbortError") {
      // 用户主动取消或切换生成，不提示错误
      return;
    }
    ElMessage.error("生成失败: " + (e.message || "未知错误"));
  } finally {
    generating.value = false;
    generatingVol.value = null;
    streamReasoning.value = "";
    streamContent.value = "";
    abortController = null;
  }
}

function openEditVolume(vol) {
  editingVolume.value = { ...vol };
  editingChapters.value = (vol.chapters || []).map((ch) => ({ ...ch }));
  showEditVolume.value = true;
}

function addChapterRow() {
  const lastNum = editingChapters.value.length > 0
    ? editingChapters.value[editingChapters.value.length - 1].chapter_number
    : (editingVolume.value?.volume_number || 1) * 200 - 200;
  editingChapters.value.push({
    chapter_number: lastNum + 1,
    title: "",
    summary: "",
  });
}

async function saveEditVolume() {
  savingVolume.value = true;
  try {
    const updated = {
      ...editingVolume.value,
      chapters: editingChapters.value.filter((ch) => ch.summary || ch.title),
    };
    await outlineStore.saveVolume(route.params.id, updated);
    showEditVolume.value = false;
    ElMessage.success("卷已保存");
  } finally {
    savingVolume.value = false;
  }
}
</script>

<style scoped lang="scss">
.core-arch-page { max-width: 900px; }
h2 { font-size: 20px; margin-bottom: 8px; }
.desc { color: #909399; font-size: 13px; margin-bottom: 24px; }

.seed-section {
  margin-bottom: 32px;
  h3 { font-size: 16px; margin-bottom: 12px; }
}

.volumes-section {
  .volumes-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
    h3 { font-size: 16px; margin: 0; }
  }
}

.empty-hint { margin: 32px 0; }

.volume-card {
  background: #fff;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  margin-bottom: 12px;
  overflow: hidden;

  .volume-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 14px 16px;
    cursor: pointer;
    transition: background 0.15s;
    &:hover { background: #fafafa; }
  }
  .volume-title {
    display: flex;
    align-items: center;
    gap: 8px;
    flex: 1;
    min-width: 0;
    .vol-num { font-weight: 600; font-size: 15px; color: #303133; }
    .vol-title-text { color: #303133; }
    .vol-title-input { width: 180px; }
    .vol-ch-count { color: #909399; font-size: 12px; margin-left: auto; }
  }
  .volume-actions { display: flex; gap: 6px; margin-left: 16px; flex-shrink: 0; }

  .volume-chapters {
    border-top: 1px solid #ebeef5;
    padding: 8px 16px 16px;
    .vol-empty { text-align: center; color: #c0c4cc; font-size: 13px; padding: 20px 0; }
  }

  .chapter-row {
    display: flex;
    gap: 12px;
    padding: 6px 0;
    font-size: 13px;
    border-bottom: 1px solid #f5f7fa;
    &:last-child { border-bottom: none; }
    .ch-num { color: #909399; flex-shrink: 0; min-width: 60px; }
    .ch-title { color: #303133; font-weight: 500; flex-shrink: 0; min-width: 80px; max-width: 160px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
    .ch-summary { color: #606266; flex: 1; }
  }
}

.generating-box {
  border-top: 1px solid #ebeef5;
  padding: 12px 16px;
  .thinking-header {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 13px;
    color: #409eff;
    margin-bottom: 8px;
  }
  .thinking-content {
    background: #f5f7fa;
    border-radius: 6px;
    padding: 10px 14px;
    font-size: 12px;
    color: #909399;
    line-height: 1.6;
    white-space: pre-wrap;
    max-height: 150px;
    overflow-y: auto;
    margin-bottom: 8px;
  }
  .stream-preview {
    pre {
      white-space: pre-wrap;
      font-size: 12px;
      line-height: 1.6;
      color: #606266;
      max-height: 200px;
      overflow-y: auto;
      background: #f5f7fa;
      border-radius: 6px;
      padding: 10px 14px;
      margin: 0;
    }
  }
}

.form-hint { color: #909399; font-size: 12px; margin-left: 8px; }

.edit-volume {
  h4 { font-size: 14px; margin: 16px 0 8px; }
  .edit-chapters {
    max-height: 60vh;
    overflow-y: auto;
    .edit-ch-row {
      display: flex;
      gap: 8px;
      align-items: center;
      margin-bottom: 8px;
      .ech-num { color: #909399; font-size: 12px; min-width: 50px; }
      .ech-title { width: 120px; flex-shrink: 0; }
      .ech-summary { flex: 1; }
    }
  }
}
</style>
