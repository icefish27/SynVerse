import { defineStore } from "pinia";
import { ref, computed } from "vue";
import { request } from "@/utils/request";

export const useChapterStore = defineStore("chapter", () => {
  const chapters = ref([]);
  const currentChapter = ref(null);
  const loading = ref(false);

  const chapterCount = computed(() => chapters.value.length);

  async function fetchChapters(novelId) {
    loading.value = true;
    try {
      chapters.value = await request({ url: `/api/novels/${novelId}/chapters`, method: "get" }) || [];
    } finally {
      loading.value = false;
    }
  }

  async function fetchChapter(chapterId) {
    const data = await request({ url: `/api/chapters/${chapterId}`, method: "get" });
    currentChapter.value = data;
    return data;
  }

  async function createChapter(novelId, body) {
    const data = await request({ url: `/api/novels/${novelId}/chapters`, method: "post", data: body });
    chapters.value.push(data);
    return data;
  }

  async function updateChapter(chapterId, body) {
    const data = await request({ url: `/api/chapters/${chapterId}`, method: "put", data: body });
    const idx = chapters.value.findIndex((c) => c.id === chapterId);
    if (idx > -1) chapters.value[idx] = data;
    if (currentChapter.value?.id === chapterId) currentChapter.value = data;
    return data;
  }

  async function deleteChapter(chapterId) {
    await request({ url: `/api/chapters/${chapterId}`, method: "delete" });
    chapters.value = chapters.value.filter((c) => c.id !== chapterId);
    if (currentChapter.value?.id === chapterId) currentChapter.value = null;
  }

  function setCurrentChapter(chapter) {
    currentChapter.value = chapter;
  }

  return {
    chapters, currentChapter, loading, chapterCount,
    fetchChapters, fetchChapter, createChapter, updateChapter, deleteChapter, setCurrentChapter,
  };
});
