---
name: clean-macos-disk
description: "安全扫描、分析并分级清理 macOS 磁盘空间。Use when the user asks to clean disk space, inspect large or hidden home directories, identify leftovers from uninstalled apps, remove caches or logs, audit stale Codex/Claude/Cursor/Windsurf/Kiro/Trae/OpenCode data or processes, prune Docker resources, review Homebrew apps, or clean old target/node_modules/build artifacts. Default to read-only evidence, verify whether an app or CLI is still used, require explicit confirmation before every destructive scope, and protect sessions, worktrees, credentials, Forge, app data, VMs, SDKs, and Docker volumes."
---

# 安全清理 Mac 磁盘

把 Mole 作为可选的补充扫描器，不把它当作无条件的一键删除器。默认使用受限根目录的只读脚本，先取得当前证据，再按风险分级，并只删除用户明确批准的路径。

## 开始前

1. 对新任务先说明：需求理解、准备怎么做、预计影响哪些路径或系统。
2. 在安装工具、退出应用或删除内容前等待明确确认。只读扫描不代表删除授权。
3. 阅读 [references/safety-boundaries.md](references/safety-boundaries.md)，并把其中的硬保护规则应用到本次任务。
4. 检查 `command -v mo`。若 Mole 未安装，说明影响并等待确认后使用 `brew install mole`；不要运行远程 `curl | bash` 安装脚本。

## 只读扫描

使用 `scripts/safe_scan.sh`，按需选择模式：

```bash
scripts/safe_scan.sh overview
scripts/safe_scan.sh projects
scripts/safe_scan.sh installers
scripts/safe_scan.sh docker
scripts/safe_scan.sh brew
scripts/safe_scan.sh ai
scripts/safe_scan.sh dotfiles
```

- `projects` 只扫描 `~/Documents/Projects`、`~/workers` 和 `~/bees`，并跳过 `.private`、`.git` 与 worktree 根目录。
- `projects` 默认只显示 10 MiB 以上的目录；需要细查时可用 `MIN_SIZE_MB=1 scripts/safe_scan.sh projects`。
- 不要在非交互环境调用 `mo installer --dry-run`；使用脚本的 `installers` 模式列出安装包。
- Mole 会遍历整个 Home/Documents，包括受保护的 Forge 和 worktree。只有用户明确同意扩大扫描范围时，才可运行 `ALLOW_MOLE_HOME_SCAN=1 scripts/safe_scan.sh mole`。它不会删除文件，但会更新 Mole 预览清单。
- 不要使用 `sudo` 扩大 Mole 预览范围，除非用户单独要求并确认。

### AI 工具专项扫描

当用户提到 Codex、Claude Code、Claude Desktop、Cursor、Windsurf、Kiro、Trae、OpenCode、MCP 或 AI 工具残留时：

1. 阅读 [references/ai-tool-data.md](references/ai-tool-data.md)。
2. 运行 `scripts/safe_scan.sh ai`；它只统计已知路径的大小和修改时间，并列出相关进程的 PID、父 PID、运行时长和可执行文件，不读取会话内容。
3. 把结果按脚本输出分为 `REBUILDABLE`、`REVIEW`、`PROTECTED`。进程列表只是线索，不能据此认定为僵尸进程。
4. 默认只把 `REBUILDABLE` 中的精确缓存路径列为候选；日志仍需确认。`PROTECTED` 只报告容量，不得读取内容或纳入批量删除。

不要按天数自动删除 `~/.codex/sessions`、`~/.codex/archived_sessions`、`~/.claude/projects` 或任何 AI worktree。不要使用第三方脚本的自动计划任务。外部工具只能作为可选审计器，安装、`npx` 下载、Hook 和调度器都需要单独确认。

### Home 隐藏目录扫描

当用户要求清理 `~/.*`、dotfiles 或已卸载 App 的残留时：

1. 阅读 [references/dotfiles-audit.md](references/dotfiles-audit.md)。
2. 运行 `scripts/safe_scan.sh dotfiles`。需要降低缓存子目录显示阈值时，使用 `DOTFILES_CACHE_MIN_MB=1 scripts/safe_scan.sh dotfiles`。
3. 依据 App、CLI、Homebrew、进程、LaunchAgent 和有限配置引用区分 `ACTIVE`、`NO_OWNER_EVIDENCE`、`UNKNOWN` 与 `PROTECTED`。
4. 把 `NO_OWNER_EVIDENCE` 当作调查线索，不当作删除授权。对候选目录核验其直接子项类型、官方卸载范围和恢复成本后，再展示精确删除清单。

禁止删除整个 `~/.cache`、`~/.config`、`~/.local`、`~/.npm`、`~/.cargo`、`~/.gradle`、`~/.m2` 或任何未知隐藏目录。优先使用包管理器自己的 prune/clean 命令，或只删除已确认的精确缓存子路径。

## 分类候选

把结果分为三组：

1. **安全可重建**：明确的缓存、日志，以及经核验的旧构建产物。
2. **需要确认**：下载文件、浏览器 Service Worker、`node_modules`、`.venv`、应用缓存、Homebrew 工具和 Docker 闲置资源。
3. **硬保护**：工作树、源码、归档、会话、数据库、应用状态、SDK、VM 和任何隐私目录。

报告每个候选的绝对路径、当前大小、为何可重建、清理后的恢复成本。对项目产物同时核验：

- 不位于任何 worktree 路径；
- Git 最近提交时间与目录修改时间都足够旧；
- 不是当前仓库、当前任务或运行中进程所需；
- 用户批准的是明确路径，而不是模糊的“全部旧项目”。

实测 `mo purge` 会把近期 worktree `.venv` 和活跃项目 `node_modules` 也列为候选。禁止运行真实 `mo purge`，必须逐路径定向处理。

## 执行门禁

删除前再次输出准确清单、预计释放空间和影响，并等待明确确认。确认只覆盖已经展示的范围，不自动扩展到新发现项。

- 应用缓存：先确认应用未运行；只清理批准的缓存路径。
- 项目产物：只删除批准的 `target`、`node_modules`、`dist`、`build`、`.next` 或 `.venv` 路径。
- Docker：默认保留运行容器和所有 volumes；只在确认后清理停止容器、未使用镜像、网络与构建缓存。Volumes 必须单独列出名称、链接数和大小后再次确认。
- Homebrew：先列出顶层 formula/cask、依赖关系和体积。卸载明确批准的包后，再运行 `brew autoremove --dry-run`；不要自动执行 `brew autoremove`。
- Mole：只有用户明确批准完整 dry-run 清单时才可运行真实 `mo clean`。通常优先定向删除。

禁止使用 `--force`、`--risky`、宽泛的根目录通配删除或绕过 macOS 权限保护。

## 完成复查

1. 用 `df -h /System/Volumes/Data` 记录前后可用空间和使用率。
2. 复查批准路径是否清空，报告权限受限或未删除项。
3. 若处理 Docker，确认运行容器仍正常并重新运行 `docker system df -v`。
4. 区分目录统计释放量与 APFS 显示的可用空间变化，不把系统延迟回收误算为单个操作的效果。
5. 下一轮继续清理前重新扫描并重新确认，不沿用旧授权扩大删除范围。
