/**
 * @name ConfigImageminPlugin
 * @description 图片压缩插件配置（基于 sharp + svgo）- 优化生产环境包体积
 * @param {object} options - 插件配置选项
 * @param {boolean} [options.disable=false] - 是否禁用插件（开发环境建议禁用）
 * @param {number} [options.jpgQuality=60] - JPG图片压缩质量（0-100）
 * @param {number | [number, number]} [options.pngQuality=85] - PNG图片压缩质量
 * @param {boolean} [options.keepViewBox=true] - 是否保留SVG的viewBox属性
 * @returns {import("vite").PluginOption} 图片压缩插件实例
 */
import { ViteImageOptimizer } from "vite-plugin-image-optimizer";

export function ConfigImageminPlugin({
  disable = false,
  jpgQuality = 60,
  pngQuality = 85,
  keepViewBox = true,
} = {}) {
  if (disable) return null;

  const jpg = clampQuality(jpgQuality, 60);
  const png = normalizePngQuality(pngQuality, 85);

  return ViteImageOptimizer({
    // 输出压缩统计日志
    logStats: true,
    includePublic: true,
    cache: true,

    // 有损压缩配置（可按项目视觉要求调整）
    jpg: { quality: jpg },
    jpeg: { quality: jpg },
    png: { quality: png },
    webp: { quality: 85 },
    avif: { quality: 80 },

    // SVG优化：默认保留 viewBox 防止图标尺寸异常
    svg: {
      multipass: true,
      plugins: [
        { name: "preset-default" },
        { name: "removeViewBox", active: !keepViewBox },
      ],
    },
  });
}

function clampQuality(value, fallback) {
  if (!Number.isFinite(value)) return fallback;
  return Math.max(1, Math.min(100, Math.round(value)));
}

function normalizePngQuality(value, fallback) {
  if (Array.isArray(value)) {
    const [min, max] = value.map((item) => Number(item));
    const avg = Number.isFinite(min) && Number.isFinite(max) ? (min + max) / 2 : fallback;
    return clampQuality(avg, fallback);
  }

  return clampQuality(Number(value), fallback);
}
