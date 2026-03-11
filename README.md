# 🌌 NASA APOD Archive

[English Version](./README_EN.md) | 简体中文

基于 NASA **天文每日一图 (APOD)** 的现代化、高性能归档浏览器。使用 Vue 3 和 Vite 构建，并针对流畅浏览和本地数据缓存进行了深度优化。

### ✨ 项目特性

- **每日更新**：自动抓取并记录最新的天文奇观。
- **现代化 UI**：极富设计感的界面，包含星空背景、毛玻璃特效以及动效反馈。
- **性能优化**：
  - 基于本地 JSON 数据库，实现瞬间加载体验。
  - 针对 Cloudflare Pages 优化的强力缓存策略。
  - 优雅的加载过渡动画，彻底消除布局抖动 (CLS)。
- **响应式布局**：完美适配手机、平板及电脑屏幕。
- **动态 SEO**：支持动态生成的标题与 Meta 标签，分享至社交媒体时体验更佳。
- **自动同步**：内置 Python 自动化脚本，确保数据实时同步。

### 🚀 技术栈

- **前端架构**：Vue 3, Vite, Vue Router, Unhead (SEO 管理)
- **样式处理**：原生 CSS (采用现代 CSS 变量与网格布局)
- **部署环境**：适配 Cloudflare Pages (已预设 `_redirects` 和 `_headers`)
- **自动化工具**：Python 脚本负责对接 NASA API 进行数据编排

### 🛠️ 本地开发

```bash
# 安装依赖
pnpm install

# 启动开发服务器
pnpm dev

# 构建生产版本
pnpm build
```
