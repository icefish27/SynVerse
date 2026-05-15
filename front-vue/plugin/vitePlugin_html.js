/**
 * @name HtmlPlugin
 * @description 处理HTML文件的Vite插件配置
 * @param {object} viteEnv - Vite环境变量对象
 * @param {string} viteEnv.VITE_APP_TITLE - 应用标题
 * @param {string} [viteEnv.VITE_APP_DESCRIPTION] - 应用描述
 * @param {string} [viteEnv.VITE_APP_KEYWORDS] - 应用关键词
 * @param {boolean} [isBuild=false] - 是否为生产环境构建
 * @returns {Plugin} HTML处理插件实例
 */
import { createHtmlPlugin } from "vite-plugin-html";

export const HtmlPlugin = (viteEnv, isBuild = false) => {
  const {
    VITE_APP_TITLE,
    VITE_APP_DESCRIPTION = "Web application powered by Vite",
    VITE_APP_KEYWORDS = "vite,webapp,frontend",
  } = viteEnv;

  return createHtmlPlugin({
    // 是否压缩HTML（生产环境默认开启）
    minify: isBuild,

    // 注入数据到HTML模板
    inject: {
      data: {
        // 页面标题
        title: VITE_APP_TITLE,

        // 元数据注入
        meta: {
          description: VITE_APP_DESCRIPTION,
          keywords: VITE_APP_KEYWORDS,
        },

        // 环境标识（用于条件渲染）
        env: isBuild ? "production" : "development",

        // 其他环境变量
        envVars: {
          baseUrl: viteEnv.VITE_BASE_URL || "/",
          apiPrefix: viteEnv.VITE_API_PREFIX || "/api",
        },
      },
    },

    // ============== 页面转换钩子 ==============
    // transformHtml: (html) => {
    //     // ------------- 开发环境添加调试标记 ------------- 按需启用
    //     if (!isBuild) {
    //         return html.replace(
    //             "</body>",
    //             `
    //     <script>
    //       console.log('[Vite] 开发环境: ${new Date().toLocaleString()}');
    //     </script>
    //   </body>
    // `);
    //     }

    //     // ============= 生产环境注入CDN资源（示例）================= 按需启用
    //     if (isBuild && viteEnv.VITE_USE_CDN === "true") {
    //         return html.replace(
    //             "</head>",
    //             `
    //         <script src="https://cdn.example.com/lib.min.js"></script>
    //       </head>
    //     `);
    //     }

    //     return html;
    // },
  });
};
