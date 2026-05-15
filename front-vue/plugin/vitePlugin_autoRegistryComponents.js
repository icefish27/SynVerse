/**
 * @name  AutoRegistryComponents
 * @description 组件自动注册插件 - 实现按需加载，无需手动导入组件
 * @returns {object} 配置好的组件自动注册插件实例
 */
import Components from "unplugin-vue-components/vite";
import {
  ElementPlusResolver, // ElementPlus 组件解析器
  VueUseComponentsResolver, // VueUse 组件解析器
} from "unplugin-vue-components/resolvers"; // 此库能实现 vue的按需自动导入

// import IconsResolver from 'unplugin-icons/resolver'; // 图标组件解析器

export const AutoRegistryComponents = () => {
  return Components({
    // 组件目录配置 - 支持多目录扫描
    dirs: [
      "src/components", // 基础组件
      "src/views/**/components", // 页面级组件
    ],

    // 支持的文件扩展名
    extensions: ["vue", "md"],

    // 递归扫描子目录
    deep: true,

    // 生成类型声明文件，支持 TypeScript 类型提示
    // dts: 'types/components.d.ts',

    // 是否将目录名作为组件的命名空间
    // 例如：components/button/MyButton.vue 会注册为 <button-my-button>
    directoryAsNamespace: false,

    // 全局组件命名空间
    globalNamespaces: [],

    // 是否自动注册指令
    directives: true,

    // 要处理的文件匹配规则
    include: [/\.vue$/, /\.vue\?vue/, /\.md$/],

    // 排除的文件匹配规则
    exclude: [
      /[\\/]node_modules[\\/]/, // 排除 node_modules
      /[\\/]\.git[\\/]/, // 排除 .git 目录
      /[\\/]\.nuxt[\\/]/, // 排除 nuxt 目录
      /[\\/]dist[\\/]/, // 排除 dist 目录
    ],

    // 组件解析器配置 - 支持多种组件库
    resolvers: [
      // ElementPlus 组件解析器 - 按需加载 ElementPlus 组件
      ElementPlusResolver({
        importStyle: "sass", // 指定样式导入方式
        directives: true, // 自动导入指令
      }),

      // VueUse 组件解析器 - 按需加载 VueUse 组件
      VueUseComponentsResolver(),

      // 图标组件解析器 - 按需加载图标
      // IconsResolver({
      //   prefix: 'icon',          // 图标前缀，例如 <icon-mdi-home>
      //   enabledCollections: ['mdi', 'fa', 'el'], // 启用的图标集
      // }),
    ],

    // 自定义组件命名规则
    getComponentName: (componentPath) => {
      // 自定义组件名称生成逻辑
      // 例如：将 src/components/button/MyButton.vue 转换为 MyButton
      const name = componentPath
        .split("/")
        .pop()
        .replace(/\.\w+$/, "");
      return name;
    },
  });
};
