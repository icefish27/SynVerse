import { defineStore } from "pinia";
import { ref, computed } from "vue";
import { request } from "@/utils/request";

export const useNovelStore = defineStore("novel", () => {
  const novels = ref([]);
  const currentNovel = ref(null);
  const loading = ref(false);

  const novelCount = computed(() => novels.value.length);

  async function fetchNovels(params = {}) {
    loading.value = true;
    try {
      novels.value = await request({ url: "/api/novels", method: "get", params }) || [];
    } finally {
      loading.value = false;
    }
  }

  async function fetchNovel(id) {
    const data = await request({ url: `/api/novels/${id}`, method: "get" });
    currentNovel.value = data;
    return data;
  }

  async function createNovel(body) {
    const data = await request({ url: "/api/novels", method: "post", data: body });
    novels.value.unshift(data);
    return data;
  }

  async function updateNovel(id, body) {
    const data = await request({ url: `/api/novels/${id}`, method: "put", data: body });
    const idx = novels.value.findIndex((n) => n.id === id);
    if (idx > -1) novels.value[idx] = data;
    if (currentNovel.value?.id === id) currentNovel.value = data;
    return data;
  }

  async function deleteNovel(id) {
    await request({ url: `/api/novels/${id}`, method: "delete" });
    novels.value = novels.value.filter((n) => n.id !== id);
    if (currentNovel.value?.id === id) currentNovel.value = null;
  }

  function setCurrentNovel(novel) {
    currentNovel.value = novel;
  }

  return {
    novels, currentNovel, loading, novelCount,
    fetchNovels, fetchNovel, createNovel, updateNovel, deleteNovel, setCurrentNovel,
  };
});
