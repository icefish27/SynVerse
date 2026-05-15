# 一、快速重开新项目

## 法一、作为新起步框架 【纯净重开】

```bash
rm -rf .git                    # 完全删除.git目录及其所有历史记录，该操作不可逆，删除后无法恢复
git init --initial-branch=master # 重新初始化一个新的 Git 仓库，并设置主分支名为 master
git add .                      # 将当前目录下所有修改、新增和删除的文件添加到 Git 本地暂存区
git commit -m "全新仓库"        # 将暂存区的文件提交到本地仓库，并附上提交信息 "全新仓库"

git remote add origin 《填入新的处理好的地址.git》  # 将本地仓库与指定的远程仓库地址建立关联，需替换为实际的远程仓库地址
git remote -v                  # 查看当前本地仓库关联的远程仓库信息，确认关联是否正确
git push --set-upstream origin --all # 提交到远程仓库
```

## 法二、保留旧记录的情况下 【完整迁移】

```bash
# 1、运行命令设置全局配置：（可以直接走这个覆盖）
git config --global user.name "{你的用户名}"
git config --global user.email "{你的邮箱}"


# 2、运行命令查看全局配置：
git config --global --list

# 3、重置远程仓库连接地址：
git remote set-url origin 《填入新的处理好的地址.git》

# 4、查看远程仓库连接地址：
git remote -v

# 5、推送代码到远程仓库：
git add .
git commit -m "update"
git push -u origin "master"
```

# 二、快速静态页命令语句

```
在你为我工作之前，我需要确保你是否能正确阅读到ui设计稿，如果可以，告诉我你看到了什么：《填写设计稿url地址》
```

```
请你基于 mastergo mcp能力，为我实现 《填写xx页》，ui设计稿地址：《填写设计稿url地址》
```

# 三、终端走代理的方法

> 当你 npm 下载拉取不动，尝试修改镜像源、切换 pnpm 都失败时。或者你想执行 wget 或者 curl 来下载“foreign”的代码库。可以使用如下命令：

注：本方法只作用于当前终端中，不会影响整个全局环境

```BASH
export http_proxy=http://127.0.0.1:7890
```

如果是 https 那么就经过如下命令：

```BASH
export https_proxy=http://127.0.0.1:7890
```

# 四、AI 代码工具配置

## doc 文档集

> 通过 URL，添加这些常用知识文档集作为对话上下文，提升 AI 的回答质量。

| 文档名称         | 链接                                 |
| ---------------- | ------------------------------------ |
| JS,CSS,HTML 文档 | https://developer.mozilla.org/zh-CN/ |
| Vue.js           | https://vuejs.org/                   |
| Pinia            | https://pinia.vuejs.org/zh/          |
| vue-router       | https://router.vuejs.org/zh/         |
| Vite 构建工具    | https://cn.vitejs.dev/               |
| WotDesignUni     | https://wot-design-uni.pages.dev/    |
| InspiraUi        | https://inspira-ui.com/              |
| ElementPlus      | https://element-plus.org/zh-CN/      |
| Z-Paging         | https://z-paging.zxlee.cn/           |
| VueUse           | https://vueuse.org/                  |

## rules 规则库

> 通过规则定义，让 AI 回答遵循你的规范

已经内置集成好了, 存放在 `.trae/rules/*`

## AI 开发约定

项目根目录新增了 `AGENTS.md`。

- 当你使用 AI 编码工具时，先让它阅读 `AGENTS.md`
- 里面约定了 Vue 写法、响应式断点、页面结构、工具函数和网络层边界
- 当前项目已经不再推荐引入 `lodash`，优先使用 `src/utils/myLodash.js`

# 五、VsCode 编辑器配置 （Trae/Cursor 皆基于 vscode 魔改，故同理）

## 1、快捷键`ctrl+d` 快速向下复制

- 1、顶部导航栏菜单 选择 文件 ，选择 首选项， 选择 键盘快捷键
- 2、搜索 `copy line down`, 解绑相关的快捷键（根本用不到）
- 3、设置快捷键为 `ctrl+d`

## 2、JSON 文件不允许注释报错

- 1、顶部导航栏菜单 选择 文件 ，选择 首选项， 选择 设置
- 2、搜索 `Files: Associations`
- 3、配置键值对，内容为：`"*.json": "jsonc"`

## 3、结合`Prettier`与 vscode，实现保存自动格式

// TODO 暂时先这样处理代码规范，后续会增加 `eslint` 与 `prettier` 的 `vite`插件配置

- 1、安装`prettier插件`（应用商店中直接下载即可）
- 2、`Trae` 点击右上角的个人图标，点击 `IDE设置`，点击 `Editor设置`
- 3、搜索 format 关键词
- 4、 `Default Formatter项` 设置为 prettier
- 5、 `format on save项`，将其勾选上
