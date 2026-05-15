/**
 * @name createVitePlugins
 * @description 基于环境动态创建Vite插件数组
 * @param {object} viteEnv - Vite环境变量对象
 * @param {boolean} viteEnv.VITE_DEV_OPEN_HTTPS - 是否在开发环境启用HTTPS
 * @param {boolean} viteEnv.VITE_USE_COMPRESS - 是否启用资源压缩
 * @param {boolean} viteEnv.VITE_USE_IMAGEMIN - 是否启用图片压缩
 * @param {boolean} isBuild - 是否为生产环境构建
 * @returns {import('vite').Plugin[]} Vite插件数组
 */

// 基础导入
import vue from "@vitejs/plugin-vue"; // 导入Vue官方插件，提供Vue 3单文件组件(SFC)支持,处理.vue文件的编译和转换
// import { fileURLToPath } from "url"; // Node.js内置模块，用于将URL对象转换为文件路径字符串
// import { resolve } from "path"; // Node.js内置模块，用于解析文件路径

// 自定义插件导入
// 通用
import { AutoRegistryComponents } from "./vitePlugin_autoRegistryComponents.js"; // 自动扫描并注册组件，无需手动import
import { ConfigRestartPlugin } from "./vitePlugin_restartVite.js"; // 监听配置文件改动重启Vite服务
import { HtmlPlugin } from "./vitePlugin_html.js"; // 处理HTML文件的Vite插件配置
// 生产环境使用
import { ConfigProgressPlugin } from "./vitePlugin_progress.js"; // 构建进度条插件
import { createBundleVisualizer } from "./vitePlugin_inspectVisualizer.js"; // Rollup 打包可视化分析插件
import { ConfigCompressPlugin } from "./vitePlugin_compress.js"; // 配置资源压缩插件，优化生产环境包体积
import { ConfigImageminPlugin } from "./vitePlugin_imageMin.js"; // 图片压缩插件

// TODO 若有需要 可以封装 vite-plugin-mkcert 实现HTTPS简化配置
// - 动态导入开发环境依赖 诸如 vite-plugin-mkcert、 unocss、 vite-plugin-mock
// - 动态导入生产环境依赖 诸如 unocss

export function createVitePlugins(viteEnv, isBuild) {
  const {
    VITE_USE_IMAGEMIN, // 是否启用图片压缩
    VITE_USE_COMPRESS, // 是否启用资源压缩
    VITE_DEV_OPEN_HTTPS, // 是否在开发环境启用HTTPS
  } = viteEnv;

  // ========== 基础插件列表 ==========
  const vitePlugins = [
    // Vue核心插件
    vue({
      reactivityTransform: true, // 启用响应式语法糖
    }),

    // 自动注册组件
    AutoRegistryComponents(),

    // 监听配置文件改动重启
    ConfigRestartPlugin(),

    // 构建进度条
    ConfigProgressPlugin(),

    // HTML处理
    HtmlPlugin(viteEnv, isBuild),
  ];

  // ========== 开发环境插件 ==========
  // if (!isBuild) {
  //     // HTTPS支持
  //     if (VITE_DEV_OPEN_HTTPS) {
  //         // 启用封装的 vite-plugin-mkcert
  //     }
  // }

  // ========== 生产环境插件 ==========
  if (isBuild) {
    // 图片压缩
    if (VITE_USE_IMAGEMIN) {
      vitePlugins.push(ConfigImageminPlugin());
    }

    // 资源压缩
    if (VITE_USE_COMPRESS) {
      vitePlugins.push(
        ConfigCompressPlugin({
          isBuild,
          algorithm: "gzip",
          deleteOrigin: false,
        })
      );
    }

    // 打包分析
    vitePlugins.push(
      createBundleVisualizer({
        enabled: true, // 是否启用插件
        openAnalyzer: false, // 是否自动打开分析页面
      })
    );
  }

  // 过滤掉未成功加载的插件(null)
  return vitePlugins.filter(Boolean);
}
