<template>
  <div class="kg-page">
    <h2>一致性知识图谱引擎</h2>
    <p class="desc">自动提取角色/地点/物品/事件，构建关系图谱，写作时实时检索设定，杜绝前后矛盾</p>

    <div class="kg-actions">
      <el-button type="primary" :loading="extracting" @click="handleExtract">从章节提取实体</el-button>
      <el-input v-model="searchText" placeholder="搜索实体..." class="kg-search" clearable @keyup.enter="handleSearch">
        <template #prefix><el-icon><Search /></el-icon></template>
      </el-input>
      <el-button @click="loadGraph">刷新图谱</el-button>
    </div>

    <!-- ECharts 图可视化 -->
    <div v-if="graphData.nodes.length > 0" class="graph-container">
      <div ref="graphRef" style="width:100%;height:500px"></div>
    </div>

    <!-- 实体列表 -->
    <div v-if="graphData.nodes.length > 0" class="entity-cards">
      <div v-for="e in graphData.nodes.slice(0, 20)" :key="e.id" class="entity-card">
        <div class="entity-label">
          <el-tag :type="tagType(e.type)" size="small">{{ e.type }}</el-tag>
          <strong>{{ e.name }}</strong>
        </div>
        <p v-if="e.description" class="entity-desc">{{ e.description }}</p>
      </div>
    </div>

    <div v-if="graphData.nodes.length === 0 && !extracting" class="kg-empty">
      <el-empty description="暂无知识图谱数据，点击「从章节提取实体」开始构建">
        <template #image><el-icon :size="64" color="#c0c4cc"><Connection /></el-icon></template>
      </el-empty>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, nextTick } from "vue";
import { useRoute } from "vue-router";
import { Search, Connection } from "@element-plus/icons-vue";
import { request } from "@/utils/request";
import { ElMessage } from "element-plus";

const route = useRoute();
const extracting = ref(false);
const searchText = ref("");
const graphRef = ref(null);
const graphData = reactive({ nodes: [], edges: [] });

onMounted(() => loadGraph());

async function handleExtract() {
  extracting.value = true;
  try {
    const data = await request({ url: `/api/novels/${route.params.id}/kg/extract`, method: "post", timeout: 60000 });
    if (data.nodes) {
      ElMessage.success(`提取到 ${data.nodes.length} 个实体, ${data.edges?.length || 0} 条关系`);
      await loadGraph();
    }
  } catch (e) {
    ElMessage.warning("提取失败，请确保有章节内容");
  } finally { extracting.value = false; }
}

async function handleSearch() {
  if (!searchText.value.trim()) { await loadGraph(); return; }
  try {
    const data = await request({ url: `/api/novels/${route.params.id}/kg/search`, method: "get", params: { q: searchText.value } });
    graphData.nodes = data.nodes || [];
    graphData.edges = data.edges || [];
    await nextTick(); renderGraph();
  } catch (e) { /* no results */ }
}

async function loadGraph() {
  try {
    const data = await request({ url: `/api/novels/${route.params.id}/kg/graph`, method: "get" });
    graphData.nodes = data.nodes || [];
    graphData.edges = data.edges || [];
    await nextTick(); renderGraph();
  } catch (e) { /* Neo4j not available */ }
}

function renderGraph() {
  if (!graphRef.value || !window.echarts) return;
  const chart = window.echarts.init(graphRef.value);
  const categories = [
    { name: "角色" }, { name: "地点" }, { name: "物品" }, { name: "事件" }, { name: "势力" }
  ];
  const nodes = graphData.nodes.map(n => ({
    ...n, symbolSize: 28, category: n.category ?? 0,
    label: { show: true, fontSize: 11 }
  }));
  const edges = graphData.edges.map(e => ({
    source: e.source, target: e.target, label: { show: true, formatter: e.label || e.relation }
  }));
  chart.setOption({
    tooltip: { formatter: (p) => p.dataType === "node" ? `<b>${p.name}</b><br/>${p.data.description || ""}` : `${p.data.source} → ${p.data.target}` },
    legend: [{ data: categories.map(c => c.name), bottom: 0 }],
    series: [{ type: "graph", layout: "force", force: { repulsion: 300, edgeLength: 150 }, roam: true, draggable: true,
      categories, data: nodes, edges, lineStyle: { curveness: 0.2 }
    }]
  });
}

function tagType(type) {
  const map = { Character: "", Location: "success", Item: "warning", Event: "danger", Faction: "info" };
  return map[type] || "";
}
</script>

<style scoped lang="scss">
.kg-page { max-width: 1100px; }
h2 { font-size: 20px; margin-bottom: 8px; }
.desc { color: #909399; font-size: 13px; margin-bottom: 24px; }
.kg-actions { display: flex; gap: 12px; margin-bottom: 24px; .kg-search { width: 280px; } }
.graph-container { background: #fff; border: 1px solid #ebeef5; border-radius: 8px; margin-bottom: 24px; padding: 12px; }
.entity-cards { display: flex; flex-wrap: wrap; gap: 12px; }
.entity-card {
  padding: 12px 16px; background: #fff; border: 1px solid #ebeef5; border-radius: 8px; min-width: 220px;
  .entity-label { display: flex; align-items: center; gap: 8px; }
  .entity-desc { font-size: 13px; color: #909399; margin: 8px 0 0; }
}
.kg-empty { padding: 60px 0; }
</style>
