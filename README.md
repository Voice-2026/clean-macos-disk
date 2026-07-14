# clean-macos-disk

一个面向 Codex 的 macOS 磁盘清理 Skill。它先进行只读扫描和证据核验，再按风险分级候选项；任何删除操作都要求用户针对明确路径再次确认。

## 主要能力

- 查看磁盘使用情况和常见大目录。
- 扫描 Rust、Node.js、Python 等项目构建产物。
- 检查安装包、Homebrew 软件和 Docker 闲置资源。
- 审计 Codex、Claude、Cursor、Windsurf、Kiro、Trae、OpenCode 等 AI 工具的缓存、会话和运行进程。
- 扫描 `~/` 下的隐藏目录，并通过 App、CLI、Homebrew、进程、LaunchAgent、IDE 插件、Shell 引用和项目标记判断目录是否仍在使用。
- 把结果分为可重建缓存、需要判断的数据和硬保护数据。

## 安全原则

- 默认只读，不提供无条件的一键清理。
- 删除前展示精确路径、大小、用途和恢复成本，并等待明确确认。
- 不因目录较旧、App 不存在或没有找到所有者，就直接判定目录可以删除。
- 默认保护账号、凭证、会话、数据库、工作树、插件、Skill、SDK、VM、模型和 Docker volumes。
- 不读取或扫描 `.private/`。
- 不执行 `sudo rm -rf`、宽泛的 Home 通配删除、`docker system prune --volumes` 或未经审查的第三方清理脚本。

详细规则见：

- [安全边界](references/safety-boundaries.md)
- [AI 工具数据分级](references/ai-tool-data.md)
- [Home 隐藏目录核验](references/dotfiles-audit.md)

## 安装

要求：

- macOS
- Codex
- Python 3（隐藏目录审计使用）

克隆到 Codex Skills 目录：

```bash
git clone https://github.com/Voice-2026/clean-macos-disk.git \
  "${CODEX_HOME:-$HOME/.codex}/skills/clean-macos-disk"
```

重启 Codex 或开始一个新任务后即可使用。

更新 Skill：

```bash
git -C "${CODEX_HOME:-$HOME/.codex}/skills/clean-macos-disk" pull --ff-only
```

## 在 Codex 中使用

可以直接描述目标，例如：

```text
用 clean-macos-disk 扫描磁盘空间，先不要删除。
```

```text
检查 Codex、Claude 和其他 AI 工具留下的缓存与会话。
```

```text
检查 ~/. 下的隐藏目录，确认对应 App 或 CLI 是否仍在使用。
```

Skill 会先说明理解、执行计划和影响范围。只读扫描完成后，它会给出候选清单；清理需要用户再次确认具体路径。

## 只读扫描脚本

也可以直接运行脚本查看证据：

```bash
cd "${CODEX_HOME:-$HOME/.codex}/skills/clean-macos-disk"

scripts/safe_scan.sh overview
scripts/safe_scan.sh projects
scripts/safe_scan.sh installers
scripts/safe_scan.sh docker
scripts/safe_scan.sh brew
scripts/safe_scan.sh ai
scripts/safe_scan.sh dotfiles
```

| 模式 | 作用 |
| --- | --- |
| `overview` | 查看数据卷和常见大目录 |
| `projects` | 扫描批准项目根目录中的构建产物 |
| `installers` | 列出桌面、下载目录和共享目录中的安装包 |
| `docker` | 查看运行容器和 Docker 空间占用 |
| `brew` | 查看 cask、顶层 formula 和 cleanup/autoremove 预览 |
| `ai` | 分级审计 AI 工具缓存、日志、会话和进程 |
| `dotfiles` | 审计 Home 隐藏目录及其所有者证据 |

降低 `.cache` 子目录的显示阈值：

```bash
DOTFILES_CACHE_MIN_MB=1 scripts/safe_scan.sh dotfiles
```

## 可选依赖

- [Mole](https://github.com/tw93/Mole)：可作为补充扫描器。Skill 默认阻止其遍历整个 Home；扩大只读扫描范围仍需用户明确同意。
- Docker CLI：仅在使用 `docker` 模式时需要。
- Homebrew：仅在使用 `brew` 模式或安装 Mole 时需要。

Mole 的 Home 范围预览需要显式开启：

```bash
ALLOW_MOLE_HOME_SCAN=1 scripts/safe_scan.sh mole
```

该命令仍然只是 dry-run，不会删除文件。

## 项目结构

```text
clean-macos-disk/
├── SKILL.md
├── agents/openai.yaml
├── references/
│   ├── ai-tool-data.md
│   ├── dotfiles-audit.md
│   └── safety-boundaries.md
└── scripts/
    ├── dotfiles_audit.py
    └── safe_scan.sh
```

## 说明

目录大小与 APFS 实际可用空间变化可能不完全一致。清理缓存也可能导致后续重新下载依赖或首次启动变慢；执行前请确认重要数据已有备份。
