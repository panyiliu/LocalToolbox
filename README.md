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
docker compose up -d
docker compose ps
```

镜像基于 [Playwright 官方 Python 镜像](https://playwright.dev/python/docs/docker)，内置 Chromium 运行环境。

### 使用 GHCR + Watchtower 自动更新

本项目默认镜像：`ghcr.io/panyiliu/localtoolbox:latest`

服务器首次部署：

```bash
docker login ghcr.io -u panyiliu
docker compose pull
docker compose up -d
```

本仓库的 `docker-compose.yml` 已为 `localtoolbox` 配置 Watchtower label：

- `com.centurylinklabs.watchtower.enable=true`

确保你的 Watchtower 启动参数包含 `--label-enable`，即可实现“只更新带 label 的容器”。后续只要 `main` 有新 push，GitHub Actions 会发布新镜像到 GHCR，Watchtower 会自动拉取并重启容器。

## 发布流程（推荐）

1. 本地开发并运行：`npm run dev`
2. 提交前运行：`npm run test`
3. 推送代码到远程仓库
4. 服务器拉取并重启：
   - `git fetch origin`
   - `git reset --hard origin/main`
   - `docker compose pull`
   - `docker compose up -d`

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

## 架构维护指南（长期）

### 核心分层约定

- `app.py`：只负责路由入口与请求分发，不承载业务细节。
- `core/`：沉淀跨工具共用能力（调度、响应、运行时检查、渲染引擎边界）。
- `tools/`：每个工具的业务胶水层，输入校验 + 调用核心能力 + 返回响应。
- `templates/` 与 `static/js/*-page.js`：页面结构与页面交互拆分，避免模板内大段脚本。

### 新增一个工具的标准流程

1. 在 `core/tool_registry.py` 注册工具元信息（`id`、`template`、`module`）。
2. 新建 `templates/<tool_id>.html` 页面模板。
3. 新建 `tools/<tool_id>.py` 后端处理逻辑（暴露 `process(request, upload_folder)`）。
4. 若有复杂交互，新建 `static/js/<tool_id>-page.js`，模板只保留最小初始化脚本。
5. 补充测试：
   - `tests/test_api_contract.py` 覆盖路由契约；
   - 新增工具的成功/失败边界测试。

### 代码变更边界

- 只在必要层改动：页面问题先看 `templates/static`，业务问题先看 `tools/core`。
- 禁止把环境探测、文件清理、下载响应等横切逻辑复制到每个工具里，优先复用 `core/`。
- 新增依赖前先确认是否可由现有模块复用，避免“每个工具一套实现”。

### 发布与回归基线

- 本地提交前固定执行：
  - `npm run preflight`
  - `npm run test`
- 推送 `main` 后由 GitHub Actions 发布 `ghcr.io/panyiliu/localtoolbox:latest`。
- 生产更新通过 Watchtower（`--label-enable` + `com.centurylinklabs.watchtower.enable=true`）。
- 页面右下角版本角标用于确认容器是否已经更新到新镜像。

## 说明

- `uploads/`：运行时生成目录（已忽略，仅保留占位）
- `logs/`：日志目录（已忽略）
