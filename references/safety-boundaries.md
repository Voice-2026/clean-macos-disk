# 安全边界

## 硬保护路径

除非用户针对精确路径单独确认，否则不要读取内容、搜索或删除：

- 任意 `.private/`；
- `~/Documents/Forge/`，包括 `personal/`、`sources/` 和知识索引；
- `~/Documents/Archives/`；
- `~/Documents/Worktrees/`、`~/Worktrees/`、`~/.config/superpowers/worktrees/`；
- `~/.codex/sessions/`、`~/.codex/archived_sessions/`、`~/.codex/memories/`、`~/.codex/plugins/`；
- `~/.codex/worktrees/`、`~/.codex/skills/`、`~/.codex/auth.json`、`~/.codex/config.toml` 和 Codex SQLite 状态库；
- `~/.claude/projects/`、`~/.claude/file-history/`、`~/.claude/tasks/`、`~/.claude/todos/`、`~/.claude/plans/`、`~/.claude/session-env/`、`~/.claude/teams/`、`~/.claude/hooks/`、`~/.claude/skills/`、Claude 设置与历史文件；
- `~/.cursor/`、`~/.windsurf/`、`~/.kiro/`、`~/.trae/`、`~/.local/share/opencode/` 中的会话、扩展、工作树、配置和应用状态；
- `~/Library/Application Support/` 中的会话、账号、数据库、Local Storage、IndexedDB 和用户配置；
- Docker volumes、`Docker.raw` 和运行中容器使用的数据；
- Claude/Tart 等 VM 镜像；
- Android/Xcode SDK、模拟器、NDK、`~/.m2/repository`、`~/.gradle` 及其他工具链；
- 用户的文档、下载、照片、音乐、视频、备份和归档文件。

对 Forge 只允许基于目录大小做最外层容量判断；不要为了磁盘清理遍历或展示其内容。

## 默认安全候选

仍需展示清单并确认后才能删除：

- 明确命名的应用缓存、更新缓存和日志；
- npm、pnpm、uv、Cargo、Go、Homebrew 等可重新下载的缓存；
- 已证明不活跃且不在 worktree 中的 `target`、`node_modules`、`dist`、`build`、`.next`；
- Docker 停止容器、未使用镜像、构建缓存和未使用网络，但不包含 volumes；
- 已安装且无依赖方的 Homebrew formula/cask。

## 必须人工判断

- 浏览器 Service Worker 与离线站点数据；
- `.venv`、模型缓存、Maven/Gradle 仓库；
- 下载目录中的 `.dmg`、`.pkg`、`.zip`、`.apk`；
- 应用的 `Application Support`、离线媒体和消息资源；
- Git worktree、未提交仓库、近期项目和当前运行任务；
- Codex 历史、附件、生成图片和插件；
- Claude/Cursor/Windsurf/Kiro/Trae/OpenCode 的会话、工作区状态、file-history、Hook、Skill、插件、扩展和账号数据；
- AI 工具相关运行进程；仅凭进程名、父 PID 或运行时长不能认定为废弃进程；
- Docker 未挂载 volume，即使 `LINKS=0` 也可能保存数据库。

## 禁止的宽泛操作

- `sudo rm -rf` 或对 `$HOME`、`Documents`、`Library` 使用通配删除；
- 未审查路径就运行真实 `mo purge`；
- 未批准完整预览就运行真实 `mo clean`；
- `docker system prune --volumes` 或 `docker volume prune`；
- 卸载 formula 后立即无审查执行 `brew autoremove`；
- 绕过 SIP、TCC、文件所有权或权限保护来删除失败项。
- 按保留天数批量删除 Codex/Claude 会话，或整体删除任何 AI 工具 worktree；
- 未审查源码就运行 `curl | bash`、第三方清理脚本、自动清理 Hook 或 launchd/cron 调度器。
- 因为 App bundle 不存在、目录修改时间较旧或扫描不到所有者，就直接删除整个隐藏目录；
- 整体删除 `~/.cache`、`~/.config`、`~/.local`、`~/.npm`、`~/.cargo`、`~/.gradle` 或 `~/.m2`。
