<template>
  <div class="ai-chat-page">
    <!-- 左侧会话列表 -->
    <div class="session-panel">
      <div class="session-header">
        <el-button type="primary" size="small" @click="handleNewSession" :loading="creatingSession">
          <el-icon><Plus /></el-icon> 新对话
        </el-button>
      </div>
      <div class="session-list">
        <div
          v-for="s in writingStore.sessions"
          :key="s.id"
          class="session-item"
          :class="{ active: writingStore.currentSession?.id === s.id }"
          @click="switchSession(s)"
        >
          <span class="session-title">{{ s.title || '新对话' }}</span>
          <span class="session-time">{{ formatTime(s.updated_at) }}</span>
        </div>
        <div v-if="writingStore.sessions.length === 0" class="session-empty">
          暂无对话
        </div>
      </div>
    </div>

    <!-- 对话区域 -->
    <div class="chat-area">
      <!-- 空状态 -->
      <div v-if="!writingStore.currentSession" class="chat-empty">
        <el-empty description="选择或创建一个对话开始写作">
          <el-button type="primary" @click="handleNewSession">新对话</el-button>
        </el-empty>
      </div>

      <!-- 消息列表 -->
      <div v-else class="chat-messages" ref="msgContainer">
        <div v-for="(msg, i) in writingStore.messages" :key="i" class="msg-wrapper">
          <!-- 用户消息 -->
          <div v-if="msg.role === 'user'" class="msg-user">
            <div class="msg-bubble user-bubble">{{ msg.content }}</div>
          </div>

          <!-- AI 消息 -->
          <div v-else class="msg-ai">
            <!-- 思考面板 -->
            <div v-if="msg.reasoning_content" class="thinking-panel">
              <div class="thinking-header" @click="msg._showThinking = !msg._showThinking">
                <el-icon><Cpu /></el-icon>
                <span>思考过程</span>
                <el-icon class="toggle-icon" :class="{ rotated: msg._showThinking }"><ArrowDown /></el-icon>
              </div>
              <div v-show="msg._showThinking" class="thinking-content">{{ msg.reasoning_content }}</div>
            </div>
            <!-- 正文 -->
            <div class="msg-bubble ai-bubble" v-html="renderMarkdown(msg.content)" />
          </div>
        </div>

        <!-- 流式生成中 -->
        <div v-if="writingStore.streaming" class="msg-wrapper">
          <div class="msg-ai">
            <div v-if="writingStore.streamingReasoning" class="thinking-panel">
              <div class="thinking-header" @click="showStreamThinking = !showStreamThinking">
                <el-icon><Cpu /></el-icon>
                <span>思考中...</span>
                <el-icon class="toggle-icon" :class="{ rotated: showStreamThinking }"><ArrowDown /></el-icon>
              </div>
              <div v-show="showStreamThinking" class="thinking-content">{{ writingStore.streamingReasoning }}</div>
            </div>
            <div v-if="writingStore.streamingContent" class="msg-bubble ai-bubble" v-html="renderMarkdown(writingStore.streamingContent)" />
            <div v-if="!writingStore.streamingContent" class="msg-bubble ai-bubble typing">
              <span class="dot">.</span><span class="dot">.</span><span class="dot">.</span>
            </div>
          </div>
        </div>

        <!-- 引用来源 -->
        <div v-if="!writingStore.streaming && writingStore.lastRefs.length > 0" class="refs-panel">
          <div class="refs-header" @click="showRefs = !showRefs">
            <el-icon><Collection /></el-icon>
            <span>参考来源 ({{ writingStore.lastRefs.length }})</span>
            <el-icon class="toggle-icon" :class="{ rotated: showRefs }"><ArrowDown /></el-icon>
          </div>
          <div v-show="showRefs" class="refs-list">
            <div v-for="(r, i) in writingStore.lastRefs" :key="i" class="ref-item">
              <div class="ref-meta">
                <el-tag size="small">{{ r.scene_type || '未知' }}</el-tag>
                <span>{{ r.source_name }}</span>
                <span class="ref-score">{{ (r.score * 100).toFixed(0) }}%</span>
              </div>
              <p>{{ r.content?.slice(0, 200) }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- 输入区 -->
      <div v-if="writingStore.currentSession" class="chat-input-area">
        <el-input
          v-model="inputText"
          type="textarea"
          :rows="2"
          placeholder="输入写作指令，如：写第3章，主角在药铺被掌柜克扣工钱..."
          @keydown.enter.exact="handleSend"
          :disabled="writingStore.streaming"
        />
        <el-button
          type="primary"
          :icon="Promotion"
          :loading="writingStore.streaming"
          @click="handleSend"
          :disabled="!inputText.trim()"
        >
          发送
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted, watch } from "vue";
import { useRoute } from "vue-router";
import { Plus, Cpu, ArrowDown, Promotion, Collection } from "@element-plus/icons-vue";
import { useWritingStore } from "@/store/useWritingStore";
import { useChapterStore } from "@/store/useChapterStore";
import dayjs from "dayjs";

const route = useRoute();
const writingStore = useWritingStore();
const chapterStore = useChapterStore();

const inputText = ref("");
const showStreamThinking = ref(true);
const showRefs = ref(true);
const creatingSession = ref(false);
const msgContainer = ref(null);

onMounted(async () => {
  await writingStore.fetchSessions(route.params.id);
  if (writingStore.sessions.length > 0) {
    await switchSession(writingStore.sessions[0]);
  }
});

watch(() => route.params.id, async (id) => {
  writingStore.reset();
  if (id) await writingStore.fetchSessions(id);
});

async function handleNewSession() {
  creatingSession.value = true;
  try {
    await writingStore.createSession(route.params.id, `对话 ${writingStore.sessions.length + 1}`);
    inputText.value = "";
  } finally {
    creatingSession.value = false;
  }
}

async function switchSession(session) {
  writingStore.currentSession = session;
  await writingStore.fetchMessages(session.id);
}

async function handleSend() {
  const text = inputText.value.trim();
  if (!text || writingStore.streaming) return;
  inputText.value = "";

  writingStore.addUserMessage(text);
  await scrollToBottom();

  try {
    const gen = writingStore.generateStream(writingStore.currentSession.id, text);
    for await (const chunk of gen) {
      await scrollToBottom();
    }
    if (writingStore.streamingContent) {
      writingStore.addAssistantMessage(writingStore.streamingContent, writingStore.streamingReasoning);
      writingStore.streamingContent = "";
      writingStore.streamingReasoning = "";
    }
    // 刷新章节列表（AI 生成会自动保存为新章节）
    await chapterStore.fetchChapters(route.params.id);
  } catch (e) {
    console.error("生成失败:", e);
  }
}

async function scrollToBottom() {
  await nextTick();
  if (msgContainer.value) {
    msgContainer.value.scrollTop = msgContainer.value.scrollHeight;
  }
}

function renderMarkdown(text) {
  if (!text) return "";
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\n\n/g, "</p><p>")
    .replace(/\n/g, "<br>")
    .replace(/^/, "<p>")
    .replace(/$/, "</p>");
}

function formatTime(t) {
  if (!t) return "";
  return dayjs(t).format("MM-DD HH:mm");
}
</script>

<style scoped lang="scss">
.ai-chat-page {
  display: flex;
  height: 100%;
  margin: -24px;
}
.session-panel {
  width: 220px;
  background: #fff;
  border-right: 1px solid #ebeef5;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  .session-header { padding: 12px; }
  .session-list { flex: 1; overflow-y: auto; }
  .session-item {
    padding: 10px 12px;
    cursor: pointer;
    display: flex;
    flex-direction: column;
    gap: 4px;
    border-bottom: 1px solid #f5f7fa;
    &:hover { background: #f5f7fa; }
    &.active { background: #ecf5ff; }
    .session-title { font-size: 13px; font-weight: 500; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
    .session-time { font-size: 11px; color: #c0c4cc; }
  }
  .session-empty { padding: 24px; text-align: center; color: #c0c4cc; font-size: 13px; }
}
.chat-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  background: #fafafa;
}
.chat-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
}
.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}
.msg-wrapper { margin-bottom: 20px; }
.msg-user {
  display: flex;
  justify-content: flex-end;
}
.msg-bubble {
  max-width: 75%;
  padding: 10px 16px;
  border-radius: 8px;
  font-size: 14px;
  line-height: 1.8;
  p { margin: 0; + p { margin-top: 12px; } }
}
.user-bubble {
  background: #409eff;
  color: #fff;
  border-bottom-right-radius: 2px;
}
.ai-bubble {
  background: #fff;
  border: 1px solid #ebeef5;
  border-bottom-left-radius: 2px;
}
.thinking-panel {
  margin-bottom: 8px;
  max-width: 75%;
  .thinking-header {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 12px;
    color: #909399;
    cursor: pointer;
    padding: 4px 0;
    .toggle-icon { transition: transform 0.2s; &.rotated { transform: rotate(180deg); } }
  }
  .thinking-content {
    background: #f5f7fa;
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 12px;
    color: #909399;
    line-height: 1.6;
    white-space: pre-wrap;
    max-height: 200px;
    overflow-y: auto;
  }
}
.typing {
  .dot { animation: blink 1.4s infinite; &:nth-child(2) { animation-delay: 0.2s; } &:nth-child(3) { animation-delay: 0.4s; } }
}
@keyframes blink { 0%,60%,100% { opacity: 0.2; } 30% { opacity: 1; } }
.refs-panel {
  margin: 0 24px 20px;
  .refs-header {
    display: flex; align-items: center; gap: 6px; font-size: 12px; color: #909399;
    cursor: pointer; padding: 6px 0;
    .toggle-icon { transition: transform 0.2s; &.rotated { transform: rotate(180deg); } }
  }
  .refs-list { margin-top: 8px; }
  .ref-item {
    padding: 8px 12px; background: #f5f7fa; border-radius: 6px; margin-bottom: 6px;
    .ref-meta { display: flex; align-items: center; gap: 8px; font-size: 12px; margin-bottom: 4px; }
    .ref-score { color: #67c23a; }
    p { font-size: 12px; color: #909399; margin: 0; line-height: 1.5; }
  }
}
.chat-input-area {
  display: flex;
  gap: 12px;
  padding: 16px 24px;
  background: #fff;
  border-top: 1px solid #ebeef5;
  align-items: flex-end;
  :deep(.el-textarea__inner) { resize: none; }
}
</style>
