# LocalToolbox

本地 Flask 工具箱：HTML 转图、文件夹树、照片时间戳、世界时钟、世界地图时钟等。

## 环境契约

- Python `>=3.10`
- `playwright==1.49.0`
- Chromium 浏览器二进制（供 HTML 转图使用）
- 默认端口：`5000`（可通过 `FLASK_PORT` 覆盖）

## 本地运行（推荐）

```bash
pip install -r requirements.txt
npm run dev
```

浏览器访问 `http://127.0.0.1:5000`（端口见 `config.py`）。

如果提示 Playwright/Chromium 缺失，可一键修复：

```bash
npm run repair:playwright
```

## 启动前自检

```bash
# 完整自检（含端口占用）
npm run preflight

# 跳过端口检查（常用于容器内）
npm run preflight:skip-port
```

自检规则：
- 阻断项：Python 版本/依赖、目录可写性、Playwright Chromium 可用性、端口可用性
- 告警项：`FLASK_DEBUG` 处于开启状态

生产 / Docker 建议设置环境变量：`FLASK_DEBUG=false`。

## Docker（推荐部署方式）

```bash
# 构建
docker build -t <你的DockerHub用户名>/localtoolbox:latest .

# 登录并推送（Docker Hub 示例）
docker login
docker push <你的DockerHub用户名>/localtoolbox:latest
```

或使用 Compose 本地运行：

```bash
docker compose up --build
```

访问 `http://127.0.0.1:5000`。

镜像基于 [Playwright 官方 Python 镜像](https://playwright.dev/python/docs/docker)，体积较大，用于支持 **HTML 转图片**（Chromium）。

## 不再用 GitHub 托管代码时

- **清空/删除远程仓库**：在 GitHub 打开仓库 → **Settings** → 最底部 **Delete this repository**（需仓库名确认）。
- **仅本地不再关联远程**：`git remote remove origin`（不会删除 GitHub 上的内容）。
- 部署改为：在能联网的机器上 `docker build` + `docker push`，服务器上 `docker pull` + `docker run`（无需把代码放在 GitHub）。

## 说明

- `uploads/`：工具生成的上传目录（已加入 `.gitignore`，仅保留占位文件）
- `logs/`：运行日志（不提交）
