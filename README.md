# LocalToolbox

本地优先的 Flask 工具箱，包含常用文件与时间工具，适合个人与小团队快速部署。

## 功能概览

- HTML 转图片（JPEG/PNG，基于 Playwright + Chromium）
- 文件夹树查看器
- 照片添加拍摄时间戳
- 世界时钟 / 世界地图时钟

## 技术栈

- Python + Flask
- Playwright（Chromium）+ Pillow
- Bootstrap + 原生 JavaScript
- Docker / Docker Compose

## 环境要求

- Python `>=3.10`
- Node.js（用于统一命令入口）
- `playwright==1.49.0`
- Chromium 浏览器二进制（HTML 转图需要）

默认监听端口：`5000`（可通过 `FLASK_PORT` 覆盖）

## 快速开始（本地开发）

```bash
pip install -r requirements.txt
npm run dev
```

浏览器访问：`http://127.0.0.1:5000`

如果提示 Chromium 缺失：

```bash
npm run repair:playwright
```

## 命令说明

- `npm run dev`：启动前自检 + 启动服务
- `npm run preflight`：运行完整环境检查（含端口）
- `npm run preflight:skip-port`：跳过端口检查（容器内常用）
- `npm run test`：Python + JS 测试全跑
- `npm run test:py`：仅 Python 测试
- `npm run test:js`：仅 JS 测试

## Docker 部署

```bash
docker compose up -d --build
docker compose ps
```

镜像基于 [Playwright 官方 Python 镜像](https://playwright.dev/python/docs/docker)，内置 Chromium 运行环境。

## 发布流程（推荐）

1. 本地开发并运行：`npm run dev`
2. 提交前运行：`npm run test`
3. 推送代码到远程仓库
4. 服务器拉取并重启：
   - `git fetch origin`
   - `git reset --hard origin/main`
   - `docker compose up -d --build`

## 推送卫生规范

- 已忽略：`.cursor/`、`node_modules/`、日志、临时文件、`uidemo.html`
- 推送前建议执行：
  - `git status --short`
  - `npm run test`
- 建议启用本仓库提供的 pre-commit 守卫（见 `scripts/install-git-hooks.*`）

## 目录说明

- `tools/`：后端工具实现
- `core/`：调度、响应、运行时检查等核心能力
- `templates/`：页面模板
- `static/`：前端脚本与静态资源
- `scripts/`：预检与开发辅助脚本
- `tests/`：契约与回归测试

## 说明

- `uploads/`：运行时生成目录（已忽略，仅保留占位）
- `logs/`：日志目录（已忽略）
