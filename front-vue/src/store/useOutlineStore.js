import { defineStore } from "pinia";
import { ref } from "vue";
import { request } from "@/utils/request";

export const useOutlineStore = defineStore("outline", () => {
  const outline = ref(null);
  const loading = ref(false);

  async function fetchOutline(novelId) {
    loading.value = true;
    try {
      outline.value = await request({ url: `/api/novels/${novelId}/outline`, method: "get" });
    } finally {
      loading.value = false;
    }
  }

  async function updateOutline(novelId, body) {
    const data = await request({ url: `/api/novels/${novelId}/outline`, method: "put", data: body });
    outline.value = data;
    return data;
  }

  function reset() {
    outline.value = null;
  }

  return { outline, loading, fetchOutline, updateOutline, reset };
});
