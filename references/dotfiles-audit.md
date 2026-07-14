# Home 隐藏目录核验

## 证据顺序

1. 检查 `/Applications`、`~/Applications` 和 `/System/Applications` 中的已知 App bundle。
2. 检查 PATH 中的对应 CLI，以及 Homebrew 已安装 formula/cask。
3. 检查进程可执行文件名、`~/Library/LaunchAgents` 文件名，以及 VS Code/Cursor/Windsurf/JetBrains 的插件目录名；不要读取进程命令行参数、plist 或插件内容。
4. 只在批准的项目根目录中检查 `gradlew`、`pubspec.yaml` 等文件名，不读取文件内容，也不进入 worktree、Forge、`.private`、构建产物或依赖目录。
5. 只在 `.zshrc`、`.zprofile`、`.bashrc`、`.bash_profile`、`.profile`、`.gitconfig` 和 fish 主配置中查找隐藏目录的精确路径引用；只报告命中的配置文件名，不输出内容。
6. 记录目录大小和修改时间。时间不是删除依据。

## 状态含义

- `ACTIVE`：至少找到 App、CLI、Homebrew、运行进程、LaunchAgent、IDE 插件或配置引用证据。保留目录；缓存子路径仍可单独评估。
- `NO_OWNER_EVIDENCE`：已识别目录归属，但在有限证据源中没有找到当前所有者。继续核对官方卸载文档、项目引用和目录直接子项；不得自动删除。
- `UNKNOWN`：没有可靠归属映射。不得删除。
- `REVIEW`：缓存容器、Trash 等混合目录，需要逐子项判断。
- `PROTECTED_ACTIVE`：属于保护数据，同时存在所有者证据。
- `PROTECTED_NO_OWNER`：属于保护数据，已执行有限所有者检查但没有证据。可继续调查，但不得直接删除。
- `PROTECTED`：凭证、配置、会话、工具链、模型、工作区或应用状态，且没有适用的所有者检查。只报告总体大小。

扫描并非完整的软件资产系统：App 可能被改名或安装在其他位置，CLI 可能只由 shell 插件加载，目录也可能被脚本间接使用。因此“无证据”不等于“无使用”。

## 删除门禁

只把满足以下条件的精确路径列为高可信残留：

- 所有者映射明确；
- App、CLI、Homebrew、进程、LaunchAgent 和配置引用均无证据；
- 目录内容类型与官方缓存或卸载残留范围一致；
- 不包含项目、会话、数据库、密钥、模型、插件、SDK、VM 或 worktree；
- 用户已看到路径、大小、恢复成本并单独确认。

即使父目录显示 `ACTIVE`，也可评估其明确缓存子路径。包管理器缓存优先使用 `npm cache verify`、`pnpm store prune`、`uv cache prune`、`cargo cache` 等原生命令；实际执行仍需确认。
