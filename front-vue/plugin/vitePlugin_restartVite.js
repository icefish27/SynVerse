/**
 * @name ConfigRestartPlugin
 * @description 监听配置文件修改自动重启Vite
 * @param {object} options - 插件配置选项
 * @param {string[]} [options.watchFiles] - 监听的文件路径模式
 * @param {boolean} [options.verbose=true] - 是否在重启时显示日志
 * @param {number} [options.delay=100] - 重启延迟时间(毫秒)
 * @returns {Plugin} ViteRestart插件实例
 */
import ViteRestart from "vite-plugin-restart";

export const ConfigRestartPlugin = ({
  // [jt]s 是一种文件匹配模式，表示同时匹配 .js 和 .ts 文件。 常用于 Vite、Webpack的配置
  watchFiles = [
    "*.config.[jt]s", // 根目录下的配置文件
    "**/config/*.[jt]s", // 任意位置config目录下的文件
    "vite.config.[jt]s", // Vite配置文件
    "tsconfig.json", // TypeScript配置(如果使用)
    ".env*", // 环境变量文件
    "package.json", // 包依赖变化时重启
  ],
  verbose = true,
  delay = 100,
} = {}) => {
  return ViteRestart({
    restart: watchFiles,
    verbose,
    delay,
  });
};
