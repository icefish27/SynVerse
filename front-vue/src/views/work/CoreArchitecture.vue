<template>
  <div class="core-arch-page">
    <h2>核心架构</h2>
    <p class="desc">填写核心种子、角色设定和世界观，然后点击「生成大纲」让 AI 为你规划整本小说的章级大纲。</p>

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
        <el-button type="primary" :loading="generating" @click="generateOutline">生成大纲</el-button>
        <el-button :loading="saving" @click="saveOutline">保存草稿</el-button>
      </el-form-item>
    </el-form>

    <!-- 生成中的思考过程 -->
    <div v-if="generating" class="generating-box">
      <div class="thinking-header">
        <el-icon><Cpu /></el-icon>
        <span>AI 思考中...</span>
      </div>
      <div v-if="streamReasoning" class="thinking-content">{{ streamReasoning }}</div>
    </div>

    <!-- 大纲结果 -->
    <div v-if="outline" class="outline-result">
      <h3>
        小说大纲
        <el-tag size="small" style="margin-left:8px">v{{ outlineStore.outline?.version }}</el-tag>
      </h3>
      <pre>{{ outline }}</pre>
    </div>

    <div v-if="!outline && !hasInput && !generating" class="empty-hint">
      <el-empty description="填写上面的信息，点击「生成大纲」开始" />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import { useRoute } from "vue-router";
import { Cpu } from "@element-plus/icons-vue";
import { useOutlineStore } from "@/store/useOutlineStore";
import { ElMessage } from "element-plus";

const route = useRoute();
const outlineStore = useOutlineStore();

const seed = ref("");
const charSetting = ref("");
const worldSetting = ref("");
const generating = ref(false);
const saving = ref(false);
const streamReasoning = ref("");

const outline = computed(() => outlineStore.outline?.full_outline || "");
const hasInput = computed(() => seed.value || charSetting.value || worldSetting.value);

onMounted(async () => {
  await outlineStore.fetchOutline(route.params.id);
  if (outlineStore.outline) {
    seed.value = outlineStore.outline.core_seed || "";
    charSetting.value = outlineStore.outline.character_setting || "";
    worldSetting.value = outlineStore.outline.world_setting || "";
  }
});

async function saveOutline() {
  saving.value = true;
  try {
    await outlineStore.updateOutline(route.params.id, {
      core_seed: seed.value, character_setting: charSetting.value, world_setting: worldSetting.value,
    });
    ElMessage.success("草稿已保存");
  } finally { saving.value = false; }
}

async function generateOutline() {
  if (!seed.value.trim()) { ElMessage.warning("请先填写核心种子"); return; }
  generating.value = true;
  streamReasoning.value = "";

  try {
    await outlineStore.updateOutline(route.params.id, {
      core_seed: seed.value, character_setting: charSetting.value, world_setting: worldSetting.value,
    });
  } catch (e) { /* save draft before generate */ }

  const baseUrl = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
  try {
    const resp = await fetch(`${baseUrl}/api/novels/${route.params.id}/outline/generate`, {
      method: "POST", headers: { "Content-Type": "application/json" },
    });
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
              // 实时更新大纲显示
              await outlineStore.updateOutline(route.params.id, { full_outline: contentBuf.join("") });
            }
          } catch (e) { /* skip */ }
        }
      }
    }
    ElMessage.success("大纲生成完成");
  } catch (e) {
    ElMessage.error("生成失败: " + (e.message || "未知错误"));
  } finally {
    generating.value = false;
    streamReasoning.value = "";
    await outlineStore.fetchOutline(route.params.id);
  }
}
</script>

<style scoped lang="scss">
.core-arch-page { max-width: 800px; }
h2 { font-size: 20px; margin-bottom: 8px; }
.desc { color: #909399; font-size: 13px; margin-bottom: 24px; }
.generating-box {
  margin-bottom: 24px;
  .thinking-header { display: flex; align-items: center; gap: 6px; font-size: 13px; color: #409eff; margin-bottom: 8px; }
  .thinking-content { background: #f5f7fa; border-radius: 8px; padding: 12px 16px; font-size: 12px; color: #909399; line-height: 1.6; white-space: pre-wrap; max-height: 200px; overflow-y: auto; }
}
.outline-result {
  margin-top: 32px;
  h3 { font-size: 16px; margin-bottom: 12px; }
  pre { white-space: pre-wrap; background: #f5f7fa; padding: 16px; border-radius: 8px; font-size: 14px; line-height: 1.8; }
}
.empty-hint { margin-top: 40px; }
</style>
