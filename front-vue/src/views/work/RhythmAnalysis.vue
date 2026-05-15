<template>
  <div class="rhythm-page">
    <h2>节奏分析</h2>
    <p class="desc">AI 多维度分析章节节奏、爽点密度、情绪曲线</p>

    <div class="rhythm-actions">
      <el-select v-model="chapterId" placeholder="选择章节" style="width: 340px" @change="loadAnalysis">
        <el-option v-for="c in chapterStore.chapters" :key="c.id" :label="`第${c.chapter_number}章 ${c.title || ''}`" :value="c.id" />
      </el-select>
      <el-button type="primary" :loading="analyzing" @click="handleAnalyze" :disabled="!chapterId">分析</el-button>
    </div>

    <!-- 加载中 -->
    <div v-if="analyzing" class="loading-box">
      <el-icon class="is-loading"><Loading /></el-icon>
      <span>AI 分析中...</span>
    </div>

    <!-- 图表 -->
    <div v-if="scores && Object.keys(scores).length > 0" class="rhythm-result">
      <div class="chart-box">
        <div ref="radarRef" style="width:100%;height:420px"></div>
      </div>
      <div v-if="suggestions" class="suggestions">
        <h3>改进建议</h3>
        <pre>{{ suggestions }}</pre>
      </div>
    </div>

    <!-- 错误状态 -->
    <div v-if="error" class="error-box">
      <el-result icon="warning" title="分析失败" :sub-title="error" />
    </div>

    <!-- 空状态 -->
    <div v-if="!scores || Object.keys(scores).length === 0" class="rhythm-empty" :class="{ hidden: analyzing }">
      <el-empty description="选择章节，点击「分析」开始 AI 多维度节奏评估">
        <template #image><el-icon :size="64" color="#c0c4cc"><TrendCharts /></el-icon></template>
      </el-empty>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted } from "vue";
import { useRoute } from "vue-router";
import { Loading, TrendCharts } from "@element-plus/icons-vue";
import { useChapterStore } from "@/store/useChapterStore";
import { request } from "@/utils/request";
import { ElMessage } from "element-plus";
import * as echarts from "echarts";

const route = useRoute();
const chapterStore = useChapterStore();
const chapterId = ref("");
const analyzing = ref(false);
const scores = ref(null);
const suggestions = ref("");
const error = ref("");
const radarRef = ref(null);

onMounted(() => chapterStore.fetchChapters(route.params.id));

async function handleAnalyze() {
  if (!chapterId.value) return;
  analyzing.value = true; error.value = "";
  try {
    const data = await request({ url: `/api/chapters/${chapterId.value}/rhythm`, method: "post", timeout: 60000 });
    scores.value = data.scores || {};
    suggestions.value = data.suggestions || "";
    await nextTick(); renderRadar();
    ElMessage.success("分析完成");
  } catch (e) {
    error.value = e?.message || "分析失败，请重试";
  } finally { analyzing.value = false; }
}

async function loadAnalysis() {
  if (!chapterId.value) return;
  try {
    const data = await request({ url: `/api/chapters/${chapterId.value}/rhythm`, method: "get" });
    if (data?.scores && Object.keys(data.scores).length > 0) {
      scores.value = data.scores;
      suggestions.value = data.suggestions || "";
      await nextTick(); renderRadar();
    } else { scores.value = null; suggestions.value = ""; }
  } catch (e) { scores.value = null; }
}

function renderRadar() {
  if (!radarRef.value || !scores.value) return;
  const chart = echarts.init(radarRef.value);
  const dims = Object.keys(scores.value);
  const vals = Object.values(scores.value);
  const maxVal = Math.max(...vals, 60);

  chart.setOption({
    tooltip: {},
    legend: { data: ["节奏评分"], bottom: 0 },
    radar: {
      indicator: dims.map(d => ({ name: d, max: 100 })),
      center: ["50%", "45%"], radius: "65%",
      axisName: { fontSize: 12 }
    },
    series: [{
      type: "radar",
      data: [{ value: vals, name: "节奏评分", areaStyle: { color: "rgba(64,158,255,0.2)" } }],
      symbol: "circle", symbolSize: 6,
      lineStyle: { color: "#409eff", width: 2 }
    }]
  });
}
</script>

<style scoped lang="scss">
.rhythm-page { max-width: 900px; }
h2 { font-size: 20px; margin-bottom: 8px; }
.desc { color: #909399; font-size: 13px; margin-bottom: 24px; }
.rhythm-actions { display: flex; gap: 12px; margin-bottom: 24px; }
.loading-box { display: flex; align-items: center; gap: 8px; justify-content: center; padding: 40px; color: #409eff; font-size: 14px; }
.rhythm-result { margin-top: 8px; }
.chart-box { background: #fff; border: 1px solid #ebeef5; border-radius: 8px; padding: 16px; margin-bottom: 24px; }
.suggestions {
  h3 { font-size: 16px; margin-bottom: 8px; }
  pre { white-space: pre-wrap; background: #f5f7fa; padding: 16px; border-radius: 8px; font-size: 14px; line-height: 1.8; }
}
.error-box { padding: 40px 0; }
.rhythm-empty { padding: 60px 0; &.hidden { display: none; } }
</style>
