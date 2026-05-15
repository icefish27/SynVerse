/**
 * @name ConfigCompressPlugin
 * @description 静态资源压缩插件配置 - 支持多种压缩算法并可根据环境调整
 * @param {object} options - 压缩配置选项
 * @param {boolean} [options.isBuild=false] - 是否为生产环境构建
 * @param {boolean} [options.deleteOrigin=false] - 是否删除原始文件
 * @param {string} [options.algorithm='gzip'] - 压缩算法，可选 'gzip' | 'brotliCompress' | 'deflate' | 'deflateRaw'
 * @param {number} [options.threshold=10240] - 触发压缩的文件大小阈值(字节)
 * @returns {Plugin} 压缩插件实例
 */
import viteCompression from "vite-plugin-compression";

export const ConfigCompressPlugin = ({
  isBuild = false,
  deleteOrigin = false,
  algorithm = "gzip",
  threshold = 10240,
} = {}) => {
  // 开发环境不启用压缩
  if (!isBuild) return () => {};

  // 根据算法设置文件扩展名
  const extMap = {
    gzip: ".gz",
    brotliCompress: ".br",
    deflate: ".zz",
    deflateRaw: ".zz",
  };
  const ext = extMap[algorithm] || ".gz";

  // 根据算法设置压缩级别
  const levelMap = {
    gzip: 9, // gzip最高压缩级别
    brotliCompress: 11, // brotli最高压缩级别
    deflate: 9, // deflate最高压缩级别
    deflateRaw: 9, // deflateRaw最高压缩级别
  };
  const level = levelMap[algorithm] || 9;

  return viteCompression({
    verbose: true, // 输出压缩日志
    disable: false, // 不禁用压缩
    deleteOriginFile: deleteOrigin, // 是否删除原始文件
    threshold, // 触发压缩的文件大小阈值
    algorithm, // 压缩算法
    ext, // 压缩文件扩展名
    compressionOptions: { level }, // 设置压缩级别
  });
};
