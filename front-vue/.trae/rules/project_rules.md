---
description: 项目通用规范
globs:
alwaysApply: true
---

# 项目通用规范

## 技术栈

- Vue 3
- Vite 前端构建工具
- Pinia 状态管理
- element-plus 组件库
- <script setup></script> 务必使用 setup 语法糖
- 本项目基于纯 JavaScript。绝不使用 TypeScript,绝不允许在<script>中添加lang="ts"!
- 使用 Vue3的组合式API 编写代码。绝不使用 选项式API
- <style lang="scss" scoped ></style> 标签内的样式必须使用 scoped 作用域 和 lang="scss" 属性

## 封装好的工具

- 1、src/componens 是封装好的全局组件
- 2、src/utils 是封装好的工具函数

## 代码风格

- 保持代码简洁、可读
- 使用有意义的变量和函数名
- 添加适当的注释解释复杂逻辑
- 遵循 Vue 等各种语言的官方风格指南

## 项目结构

- 保持项目结构清晰，遵循模块化原则
- 相关功能应放在同一目录下
- 使用适当的目录命名，反映其包含内容

## 通用开发原则

- 编写可测试的代码
- 避免重复代码（DRY 原则）
- 优先使用现有库和工具，避免重新发明轮子
- 考虑代码的可维护性和可扩展性

## 响应语言

- 始终使用中文回复用户

## 规则文件说明

本项目使用以下规则文件：

- vue.mdc：Vue 开发规范
- git.mdc：Git 提交规范
- fasterPageGuide.mdc：快速静态页面规范（仅在我使用 masterGo 之类的 ui 设计稿 mcp 时，需要你帮我生成静态界面时引用）