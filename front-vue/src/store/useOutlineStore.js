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

  async function saveVolume(novelId, volume) {
    const volumes = [...(outline.value?.volumes || [])];
    const idx = volumes.findIndex((v) => v.volume_number === volume.volume_number);
    if (idx > -1) volumes[idx] = volume;
    else volumes.push(volume);
    volumes.sort((a, b) => a.volume_number - b.volume_number);
    return await updateOutline(novelId, { volumes });
  }

  async function deleteVolume(novelId, volumeNumber) {
    const volumes = (outline.value?.volumes || []).filter(
      (v) => v.volume_number !== volumeNumber
    );
    return await updateOutline(novelId, { volumes });
  }

  function getVolume(volumeNumber) {
    return (outline.value?.volumes || []).find((v) => v.volume_number === volumeNumber);
  }

  function reset() {
    outline.value = null;
  }

  return {
    outline, loading,
    fetchOutline, updateOutline, saveVolume, deleteVolume, getVolume,
    reset,
  };
});
