<template>
  <div>
    <HelloWorld />
    <br />
    <div class="mb-4">
      <el-button>Default</el-button>
      <el-button type="primary">Primary</el-button>
      <el-button type="success">Success</el-button>
      <el-button type="info">Info</el-button>
      <el-button type="warning">Warning</el-button>
      <el-button type="danger">Danger</el-button>
    </div>
  </div>
</template>

<script setup>
import HelloWorld from "@/components/template.vue"; // 测试组件
import { useUserStore } from "@/store/useUserStore"; // 测试pinia状态库
const userStore = useUserStore();
userStore.setUserInfo({
  avatar: "https://wpimg.wallstcn.com/f778738c-e4f8-4870-b634-56703b4acafe.gif",
  createtime: 1693040000000,
  id: 1,
  mobile: "13800000000",
  nickname: "张三",
  score: 0,
  token: "123",
  user_id: 1,
  username: "zhangsan",
});

// 测试 axios封装
import { indexTest } from "@/api/commonApi";
import { onMounted } from "vue";
onMounted(async () => {
  const indexTest_res = await indexTest({
    username: "zhangsan",
    password: "123456",
  });
});
</script>

<style scoped></style>
