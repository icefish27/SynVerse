/**
 * @name createBundleVisualizer
 * @description 创建 Rollup 打包可视化分析插件实例
 * @param {object} options - 可视化配置选项
 * @param {boolean} [options.enabled=false] - 是否启用插件
 * @param {boolean} [options.openAnalyzer=false] - 是否自动打开分析页面
 * @param {string} [options.reportFilename='stats.html'] - 分析报告文件名
 * @returns {object|null} 配置好的插件实例，或 null（未启用时）
 */
import { visualizer } from "rollup-plugin-visualizer";

export function createBundleVisualizer(options = {}) {
  const {
    enabled = false, // 是否启用插件
    openAnalyzer = false, // 是否自动打开分析页面
    reportFilename = "index.html", // 分析报告文件名
  } = options;

  // 仅在启用且为生产环境构建时生成分析报告
  if (!enabled || process.env.NODE_ENV !== "production") {
    return null;
  }

  return visualizer({
    // 输出文件路径（相对于项目根目录）
    filename: `./analyzeVisualization/${reportFilename}`,

    // 生成交互式 HTML 报告（默认值，可省略）
    template: "treemap",

    // 构建完成后自动打开浏览器查看报告
    open: openAnalyzer,

    // 显示 gzip 压缩后的文件大小
    gzipSize: true,

    // 显示 brotli 压缩后的文件大小
    brotliSize: true,

    // 排除 node_modules 中的依赖（可选优化）
    // exclude: [/node_modules/],
  });
}
