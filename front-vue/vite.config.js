import { loadEnv } from "vite";
import { fileURLToPath, URL } from "node:url";
import vue from "@vitejs/plugin-vue";
import { createVitePlugins } from "./plugin/index.js";

// 全局标志，vite是否初始化,重启会重新打印环境信息
let initialized = false;

/* ======= 《情景配置》：基于（dev/serve 或 build）命令或者不同的 模式 来决定选项 =======*/
export default ({ command, mode }) => {
  const isBuild = command === "build";
  const env = initEnvironmentInfo(command, mode);

  return {
    base: "./",
    // -------------- 设置别名依赖 --------------
    resolve: {
      alias: {
        "@": fileURLToPath(new URL("./src", import.meta.url)),
      },
    },
    plugins: [...createVitePlugins(env, isBuild)],
    // -------------- 开发服务器的设置 --------------
    server: {
      // HMR(热模块替换)配置
      hmr: {
        overlay: false, // 禁用服务器错误遮罩层，发生错误时不会在浏览器中显示全屏 overlay
      },

      // 服务基础配置
      port: env.VITE_PORT, // 指定开发服务器端口，从环境变量获取
      open: false, // 服务器启动时是否自动打开浏览器
      cors: false, // 是否启用跨域资源共享，设为false时使用默认配置
      host: "0.0.0.0", // 指定服务器监听地址，支持通过IP访问开发服务器

      // 代理配置，仅在启用代理时生效
      proxy: env.VITE_OPEN_PROXY
        ? {
            // 匹配请求路径前缀，如/api
            [env.VITE_API_PREFIX]: {
              target: env.VITE_PROXY_URL, // 代理目标URL，如http://api.example.com
              changeOrigin: true, // 是否修改请求源，解决跨域问题
              rewrite: (path) =>
                // 重写请求路径，移除前缀
                path.replace(new RegExp(`^${env.VITE_API_PREFIX}`), ""),
            },
          }
        : undefined, // 不启用代理时设为undefined
    },
    // -------------- 定义全局常量 --------------
    define: {
      // __VITE_APP_TITLE__，值为环境变量中的应用标题
      // 使用 JSON.stringify 确保字符串被正确转义为合法的 JS 字符串字面量
      __VITE_APP_TITLE__: JSON.stringify(env.VITE_APP_TITLE),
    },
  };
};

/* ======= 旧版写法 ======= */
// export default defineConfig({
//   base: "./",
//     resolve: {
//       alias: {
//         "@": fileURLToPath(new URL("./src", import.meta.url)),
//       },
//     },
//   plugins: [vue()],
// })

/**
 * 初始化并打印环境信息（只执行一次）
 */
function initEnvironmentInfo(command, mode) {
  if (initialized) return;
  initialized = true;

  const root = process.cwd();
  const env = loadEnv(mode, root);

  // console.log("✨".repeat(60));
  console.log("✨".repeat(26) + " 🚀 Vite·启动 🚀 " + "✨".repeat(26));
  console.log("以下为系统信息：");
  console.log("command: ", command); // 比如 dev为serve，build为build
  console.log("isBuild: ", command === "build"); // 比如 dev为false，build为true
  console.log("mode: ", mode); // 比如 dev为development，build为production
  console.log("root: ", root); // 比如 C:\Users\jin\Desktop\demo_clone\cesium_study
  console.log("env: ", env); // 比如一整个env的数据对象化（确实是动态的选择dev还是prod）

  console.log("✨".repeat(60));

  return env;
}
