import { defineStore } from "pinia";
import { ref } from "vue";
import { request } from "@/utils/request";

export const useKnowledgeStore = defineStore("knowledge", () => {
  const documents = ref([]);
  const searchResults = ref([]);
  const loading = ref(false);

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
      timeout: 120000,
    });
    documents.value.unshift(data);
    return data;
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
    documents, searchResults, examples, loading,
    fetchDocuments, uploadDocument, deleteDocument, search,
    fetchExamples, createExample, deleteExample,
  };
});
