import { defineStore } from "pinia";
import { ref } from "vue";
import { request } from "@/utils/request";

export const useKnowledgeStore = defineStore("knowledge", () => {
  const documents = ref([]);
  const searchResults = ref([]);
  const loading = ref(false);

  // 当前查看进度的文档
  const activeDocId = ref(null);

  // 轮询定时器
  let _pollTimer = null;

  async function fetchDocuments() {
    loading.value = true;
    try {
      documents.value = await request({ url: "/api/knowledge/documents", method: "get" }) || [];
    } finally {
      loading.value = false;
    }
  }

  async function uploadDocument(file) {
    const form = new FormData();
    form.append("file", file);
    const data = await request({
      url: "/api/knowledge/upload",
      method: "post",
      data: form,
      headers: { "Content-Type": "multipart/form-data" },
    });
    documents.value.unshift(data);
    return data;
  }

  async function startProcessing(docId) {
    const data = await request({
      url: `/api/knowledge/documents/${docId}/process`,
      method: "post",
    });
    return data;
  }

  async function fetchProgress(docId) {
    const data = await request({
      url: `/api/knowledge/documents/${docId}/progress`,
      method: "get",
    });
    // 更新本地文档列表中的进度
    const idx = documents.value.findIndex((d) => d.id === docId);
    if (idx > -1) {
      documents.value[idx] = { ...documents.value[idx], ...data };
    }
    return data;
  }

  async function fetchContent(docId) {
    const baseUrl = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
    const resp = await fetch(`${baseUrl}/api/knowledge/documents/${docId}/content`);
    if (!resp.ok) {
      const err = new Error(`请求失败 (${resp.status})`);
      err.response = resp;
      throw err;
    }
    return await resp.text();
  }

  function startPolling(docId, onDone) {
    stopPolling();
    activeDocId.value = docId;
    _pollTimer = setInterval(async () => {
      try {
        const progress = await fetchProgress(docId);
        if (progress.status === "ready" || progress.status === "error") {
          stopPolling();
          if (onDone) onDone(progress);
        }
      } catch { stopPolling(); }
    }, 1500);
  }

  function stopPolling() {
    if (_pollTimer) {
      clearInterval(_pollTimer);
      _pollTimer = null;
    }
    activeDocId.value = null;
  }

  async function deleteDocument(id) {
    await request({ url: `/api/knowledge/documents/${id}`, method: "delete" });
    documents.value = documents.value.filter((d) => d.id !== id);
  }

  async function search(query, sceneType = "", topK = 5) {
    searchResults.value = await request({
      url: "/api/knowledge/search",
      method: "get",
      params: { q: query, scene_type: sceneType, top_k: topK },
    }) || [];
    return searchResults.value;
  }

  const examples = ref([]);

  async function fetchExamples(sceneType = "") {
    const params = sceneType ? { scene_type: sceneType } : {};
    examples.value = await request({ url: "/api/style-examples", method: "get", params }) || [];
    return examples.value;
  }

  async function createExample(data) {
    const ex = await request({ url: "/api/style-examples", method: "post", data });
    examples.value.unshift(ex);
    return ex;
  }

  async function deleteExample(id) {
    await request({ url: `/api/style-examples/${id}`, method: "delete" });
    examples.value = examples.value.filter((e) => e.id !== id);
  }

  return {
    documents, searchResults, examples, loading, activeDocId,
    fetchDocuments, uploadDocument, startProcessing, fetchProgress,
    fetchContent, startPolling, stopPolling, deleteDocument, search,
    fetchExamples, createExample, deleteExample,
  };
}, {
  persist: {
    enabled: true,
    strategies: [{
      key: "pinia_knowledgestore",
      storage: localStorage,
      paths: ["documents", "searchResults", "examples"],
    }],
  },
});
