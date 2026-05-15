/**
 * @name ConfigProgressPlugin
 * @description 构建过程显示进度条，提升开发体验
 * @param {object} options - 进度条配置选项
 * @param {string} [options.format='构建中 |:bar| :percent | 耗时: :elapsed 秒'] - 进度条显示格式
 * @param {number} [options.barsize=65] - 进度条宽度
 * @param {boolean} [options.verbose=true] - 是否显示详细信息
 * @param {string} [options.color='green'] - 进度条颜色，可选值: red, green, yellow, blue, magenta, cyan, white
 * @returns {Plugin} 进度条插件实例
 */
import progress from "vite-plugin-progress";

export const ConfigProgressPlugin = ({
  format = "📦 构建中 |:bar| :percent | 耗时: :elapsed 秒 🚀",
  barsize = 65,
  verbose = true,
  color = "green",
} = {}) => {
  return progress({
    format,
    barsize,
    verbose,
    color,
  });
};
