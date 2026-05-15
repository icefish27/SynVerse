import { defineStore } from "pinia";
import { ref, computed } from "vue";
import { cloneDeep } from "@/utils/myLodash";

const initUserInfoState = {
  // 举例用户信息内容，可以适当修改
  avatar: "",
  createtime: 0,
  id: 0,
  mobile: "",
  nickname: "",
  score: 0,
  token: "",
  user_id: 0,
  username: "",
}; //用户信息

// 定义store
export const useUserStore = defineStore(
  "user",
  () => {
    const userInfo = ref(cloneDeep(initUserInfoState)); // 必须深拷贝，不然后期用initState清空会不变

    // ================ 设置用户信息，手动原始==================
    const setUserInfo = (val) => {
      userInfo.value = val;
    };
    // ================ 清除用户信息，清空pinia==================
    const clearUserInfo = () => {
      userInfo.value = cloneDeep(initUserInfoState);
    };

    // ============== 判断用户是否登录 ================
    const isLogin = computed(() => !!userInfo.value.token);

    return {
      userInfo, // 暴露用户信息
      isLogin, // 暴露用户是否登录的计算属性
      setUserInfo, // 设置用户信息
      clearUserInfo, // 清空用户信息
    };
  },
  {
    persist: {
      enabled: true,
      strategies: [
        {
          key: "pinia_userstore", // 本地存储的 key
          storage: localStorage, // 存储位置：localStorage / sessionStorage
        },
      ],
    },
  }
);
