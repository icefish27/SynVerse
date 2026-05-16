# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 仓库说明

本仓库 名为 SynVerse(神韵) 最终目的是 研发出一个 AI 写作引擎

不同于通用大模型，它：

- 真正学习 大量优秀小说的文学审美（来自本地资料进行知识库构建），模仿文笔，写出来的东西不再“AI 腔”。
- 精确记住你的故事设定，从角色关系到伏笔埋设全部可靠。
- 完全适配你“大纲→迭代→续写”的工作习惯，不强行改变你的创作流程。
- 能随着你的作品规模和技术进步平滑升级。

## 可用的资源

局域网家庭服务器 uzentu，详细服务器信息见： `/AI参考信息/局域网服务器信息.md`。

uzentu的大致资源如下：

- 1Panel
- Docker
- Docker Compose
- SSH
- PostgreSQL 18.3
- MySQL 8.4.9
- Redis 8.6.3
- Ollama 0.23.3
- Open WebUI
- MinIO
- MongoDB 7.0
- RabbitMQ 4.3.0

### 大模型

目前使用的大模型是 DeepSeek 的模型 DeepSeek v4 pro 和 flash。 用的云端 apikey 密钥信息见： `/AI参考信息/ 大模型密钥.md`。

#### 其他模型

由于局域网服务器 uzentu 性能不强，所以 大模型用的 云端DeepSeek， 其他辅助模型，你看着需要就去 ollama 上弄。
如果有在 ollama 上弄新模型，请你回写到 `/AI参考信息/局域网服务器信息.md`。

## 文件夹描述

### front-vue

《front-vue》： 一个成熟的前端框架，可以当做前端起步框架。
该框架原名叫 pc_evo，所在地址为 https://gitee.com/kang-zhenbin/pc-pure.git
注意，不要去动我这个 pc_evo 的 git 仓库，目前他已经稳定，你只能在需要的时候拉取过来，作为起步框架使用。

### 历史资料和代码

novel： 一个我曾经尝试用 claude code 结合 agent、skills 已经各种规则和流程来进行AI 小说创作的项目。
由于 通用大模型写出来的效果不好，这才启发了我做这个 SynVerse 项目

实验： 测试代码

rag： 测试代码，用各种技术增强 ai 写小说的能力

### AI参考信息

《AI参考信息》： 一个目录，用于归类 AI 参考的信息，防止全部一股脑塞在 CLAUDE.md 中，导致 token 消耗太多。

## 优秀小说原稿收集

《优秀小说原稿收集》： 一个目录，用于收集优秀小说的原稿，用于知识库构建。

## 涉及 修改优化 CLAUDE.md 的关键规则

- **简洁**: token 宝贵，只记重点，用最简 markdown 语法
- **抽离**: 大段细节放 `/AI参考信息/` 目录，此处只留引用
- **自优化**: 发现可优化的结构时，主动精简/重构此文件和 `/AI参考信息/`

## 网络代理

uzentu 在其 7897 端口有 clash verge 的网络代理
本机 mac 电脑 在其 7890 端口 有 clash verge 的网络代理
