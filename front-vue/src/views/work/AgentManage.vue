<template>
  <div class="page-placeholder">
    <el-empty description="多 Agent 智能体">
      <template #image><el-icon :size="64" color="#c0c4cc"><UserFilled /></el-icon></template>
    </el-empty>
    <p class="note">写作智能体 + 读者智能体 + 用户自定义智能体</p>
  </div>
</template>
<script setup>
import { UserFilled } from "@element-plus/icons-vue";
</script>
<style scoped lang="scss">
.page-placeholder { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; .note { color: #909399; font-size: 13px; } }
</style>
