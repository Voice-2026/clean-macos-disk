# AI 工具数据分级

## 扫描原则

- 只统计已知路径的大小、修改时间和文件类型；不要读取会话、提示词、附件、数据库内容或命令行参数。
- 不以“超过 N 天”为删除依据。时间只能帮助人工判断，不能证明资料已废弃。
- 不把运行时间长、父进程退出或名字包含 MCP 当作僵尸进程的充分证据；先核对当前应用、端口、工作目录和任务。
- 缓存清理前退出对应应用，防止文件被立即重建或状态损坏。

## 风险分级

### REBUILDABLE

仅包括明确命名的 `Cache`、`Code Cache`、`GPUCache`、渲染缓存等可重建目录。仍需展示精确路径、大小并取得确认后才能删除。

### REVIEW

包括 debug 日志、日志数据库、Service Worker CacheStorage 和离线资源。它们可能用于问题排查、离线能力或恢复，不得自动删除。

### PROTECTED

包括：

- Codex/Claude 会话、归档会话、history、file-history、tasks、todos、plans 和 session-env；
- worktree、项目映射、插件、Skill、Hook、扩展和工作区状态；
- `auth.json`、配置、Cookies、Local Storage、IndexedDB、SQLite 状态库；
- Claude VM bundles、模型、附件、生成资源和 OpenCode application state。

只报告这些路径的总体容量。除非用户针对精确路径单独批准，否则不要读取下级内容，也不要删除。

## 外部工具

- `zclean`：适合审计 AI 遗留进程和项目缓存；只使用已安装版本的 audit/report 能力。安装、`npx` 下载、Hook、scheduler 和真实清理都需要单独确认。
- Claude Code Session Manager：适合按 Claude 会话预览孤立资料；优先使用 dry-run。删除会话仍需展示逐会话计划并再次确认。
- `dev-clean`：不要直接运行真实清理。它会按天数删除 Codex/Claude 会话，并整体删除 Codex worktrees，不符合本 Skill 的保护规则。
- context-cleaner：用于压缩 Claude transcript 的 token 体积，不等于磁盘清理；它保留原文件，安装 SessionStart Hook 也需要单独确认。
