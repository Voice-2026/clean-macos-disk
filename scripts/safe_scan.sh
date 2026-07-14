#!/usr/bin/env bash

set -u
set -o pipefail

mode="${1:-overview}"

usage() {
  printf 'Usage: %s {overview|mole|projects|installers|docker|brew|ai|dotfiles|all}\n' "$0"
}

report_known_path() {
  local risk="$1"
  local label="$2"
  local path="$3"
  local size_kb
  local modified

  [ -e "$path" ] || return 0
  size_kb=$(du -sk "$path" 2>/dev/null | awk '{print $1}')
  size_kb="${size_kb:-0}"
  modified=$(stat -f '%Sm' -t '%Y-%m-%d' "$path" 2>/dev/null || printf 'unknown')
  case "$risk" in
    REBUILDABLE) AI_REBUILDABLE_KB=$((AI_REBUILDABLE_KB + size_kb)) ;;
    REVIEW) AI_REVIEW_KB=$((AI_REVIEW_KB + size_kb)) ;;
    PROTECTED) AI_PROTECTED_KB=$((AI_PROTECTED_KB + size_kb)) ;;
  esac
  awk -v risk="$risk" -v label="$label" -v size_kb="$size_kb" \
    -v modified="$modified" -v path="$path" \
    'BEGIN {printf "%-11s %10.1f MiB  modified=%-10s  %-28s %s\n", risk, size_kb/1024, modified, label, path}'
}

disk_overview() {
  printf '\n[Disk]\n'
  df -h / /System/Volumes/Data

  printf '\n[Known large roots]\n'
  local roots=()
  local root
  for root in \
    "$HOME/Documents/Projects" \
    "$HOME/Documents/Archives" \
    "$HOME/Documents/Worktrees" \
    "$HOME/Documents/Codex" \
    "$HOME/Library" \
    "$HOME/Downloads" \
    "$HOME/.codex" \
    "$HOME/.config"; do
    if [ -e "$root" ]; then
      roots+=("$root")
    fi
  done

  if [ "${#roots[@]}" -gt 0 ]; then
    (du -sh "${roots[@]}" 2>/dev/null || true) | sort -hr
  fi
}

mole_preview() {
  if ! command -v mo >/dev/null 2>&1; then
    printf 'Mole is not installed. Ask for confirmation before running: brew install mole\n' >&2
    return 1
  fi
  if [ "${ALLOW_MOLE_HOME_SCAN:-0}" != "1" ]; then
    printf 'Refusing broad Mole scan: it traverses protected Home/Documents paths.\n' >&2
    printf 'After explicit user approval, opt in with ALLOW_MOLE_HOME_SCAN=1.\n' >&2
    return 3
  fi
  printf '\n[Mole clean dry-run]\n'
  mo clean --dry-run
}

project_preview() {
  printf '\n[Project artifacts in approved roots]\n'
  local roots=()
  local root
  for root in "$HOME/Documents/Projects" "$HOME/workers" "$HOME/bees"; do
    if [ -d "$root" ]; then
      roots+=("$root")
    fi
  done

  if [ "${#roots[@]}" -eq 0 ]; then
    printf 'No approved project roots found.\n'
    return 0
  fi

  find "${roots[@]}" \
    -type d \( -name .git -o -name .private -o -name Worktrees \) -prune -o \
    -type d \( \
      -name target -o -name node_modules -o -name dist -o -name build -o \
      -name .next -o -name .venv -o -name .dart_tool -o -name .gradle -o -name .nx -o \
      -name __pycache__ -o -name .pytest_cache -o -name .astro \
    \) -prune -print0 2>/dev/null |
    while IFS= read -r -d '' path; do
      size_kb=$(du -sk "$path" 2>/dev/null | awk '{print $1}')
      modified=$(stat -f '%Sm' -t '%Y-%m-%d' "$path" 2>/dev/null)
      project=$(dirname "$path")
      git_root=$(git -C "$project" rev-parse --show-toplevel 2>/dev/null || true)
      commit='-'
      if [ -n "$git_root" ]; then
        commit=$(git -C "$git_root" log -1 --format='%cs' 2>/dev/null || printf '-')
      fi
      printf '%s\t%s\t%s\t%s\n' "${size_kb:-0}" "${modified:-unknown}" "$commit" "$path"
    done | sort -nr | awk -F '\t' -v min_mb="${MIN_SIZE_MB:-10}" \
      '$1 >= min_mb * 1024 {printf "%.1f MiB\tmodified=%s\tcommit=%s\t%s\n", $1/1024, $2, $3, $4}'
}

installer_preview() {
  printf '\n[Installer files]\n'
  local roots=()
  local root
  for root in "$HOME/Downloads" "$HOME/Desktop" /Users/Shared; do
    if [ -d "$root" ]; then
      roots+=("$root")
    fi
  done

  if [ "${#roots[@]}" -eq 0 ]; then
    printf 'No installer search roots found.\n'
    return 0
  fi

  find "${roots[@]}" -maxdepth 2 -type d -name .private -prune -o -type f \
    \( -iname '*.dmg' -o -iname '*.pkg' -o -iname '*.iso' -o -iname '*.xip' -o -iname '*.zip' -o -iname '*.apk' -o -iname '*.tar.gz' \) \
    -print0 2>/dev/null |
    while IFS= read -r -d '' path; do
      size_kb=$(du -k "$path" 2>/dev/null | awk '{print $1}')
      modified=$(stat -f '%Sm' -t '%Y-%m-%d' "$path" 2>/dev/null)
      printf '%s\t%s\t%s\n' "${size_kb:-0}" "${modified:-unknown}" "$path"
    done | sort -nr | awk -F '\t' '{printf "%.1f MiB\t%s\t%s\n", $1/1024, $2, $3}'
}

docker_preview() {
  if ! command -v docker >/dev/null 2>&1; then
    printf 'Docker CLI is not installed.\n' >&2
    return 1
  fi
  printf '\n[Running containers]\n'
  docker ps --format 'table {{.ID}}\t{{.Names}}\t{{.Image}}\t{{.Status}}'
  printf '\n[Docker disk usage]\n'
  docker system df -v
}

brew_preview() {
  if ! command -v brew >/dev/null 2>&1; then
    printf 'Homebrew is not installed.\n' >&2
    return 1
  fi
  local prefix
  prefix=$(brew --prefix)

  printf '\n[Homebrew casks]\n'
  brew list --cask
  printf '\n[Homebrew top-level formulae]\n'
  brew leaves
  printf '\n[Homebrew storage]\n'
  du -sh "$prefix/Cellar" "$prefix/Caskroom" 2>/dev/null
  printf '\n[Homebrew cleanup dry-run]\n'
  brew cleanup -n
  printf '\n[Homebrew autoremove dry-run]\n'
  brew autoremove --dry-run
}

ai_tool_preview() {
  AI_REBUILDABLE_KB=0
  AI_REVIEW_KB=0
  AI_PROTECTED_KB=0

  printf '\n[AI tool data audit]\n'
  printf 'Metadata only: sizes and modification dates; session contents are not read.\n'

  printf '\n[REBUILDABLE caches — candidates only after exact-path confirmation]\n'
  report_known_path REBUILDABLE 'Claude desktop Cache' "$HOME/Library/Application Support/Claude/Cache"
  report_known_path REBUILDABLE 'Claude desktop Code Cache' "$HOME/Library/Application Support/Claude/Code Cache"
  report_known_path REBUILDABLE 'Claude desktop GPUCache' "$HOME/Library/Application Support/Claude/GPUCache"
  report_known_path REBUILDABLE 'Claude DawnGraphiteCache' "$HOME/Library/Application Support/Claude/DawnGraphiteCache"
  report_known_path REBUILDABLE 'Claude DawnWebGPUCache' "$HOME/Library/Application Support/Claude/DawnWebGPUCache"
  report_known_path REBUILDABLE 'Codex app Cache' "$HOME/Library/Application Support/Codex/Cache"
  report_known_path REBUILDABLE 'Codex app Code Cache' "$HOME/Library/Application Support/Codex/Code Cache"
  report_known_path REBUILDABLE 'Codex app GPUCache' "$HOME/Library/Application Support/Codex/GPUCache"
  report_known_path REBUILDABLE 'Cursor Cache' "$HOME/Library/Application Support/Cursor/Cache"
  report_known_path REBUILDABLE 'Cursor Code Cache' "$HOME/Library/Application Support/Cursor/Code Cache"
  report_known_path REBUILDABLE 'Cursor GPUCache' "$HOME/Library/Application Support/Cursor/GPUCache"
  report_known_path REBUILDABLE 'Windsurf Cache' "$HOME/Library/Application Support/Windsurf/Cache"
  report_known_path REBUILDABLE 'Windsurf Code Cache' "$HOME/Library/Application Support/Windsurf/Code Cache"
  report_known_path REBUILDABLE 'Windsurf GPUCache' "$HOME/Library/Application Support/Windsurf/GPUCache"
  report_known_path REBUILDABLE 'Kiro Cache' "$HOME/Library/Application Support/Kiro/Cache"
  report_known_path REBUILDABLE 'Kiro Code Cache' "$HOME/Library/Application Support/Kiro/Code Cache"
  report_known_path REBUILDABLE 'Kiro GPUCache' "$HOME/Library/Application Support/Kiro/GPUCache"
  report_known_path REBUILDABLE 'Trae Cache' "$HOME/Library/Application Support/Trae/Cache"
  report_known_path REBUILDABLE 'Trae Code Cache' "$HOME/Library/Application Support/Trae/Code Cache"
  report_known_path REBUILDABLE 'Trae GPUCache' "$HOME/Library/Application Support/Trae/GPUCache"
  report_known_path REBUILDABLE 'OpenCode cache' "$HOME/.cache/opencode"

  printf '\n[REVIEW logs and offline caches — inspect purpose before deletion]\n'
  report_known_path REVIEW 'Claude Code debug logs' "$HOME/.claude/debug"
  report_known_path REVIEW 'Codex logs' "$HOME/.codex/log"
  report_known_path REVIEW 'Codex logs database' "$HOME/.codex/logs_2.sqlite"
  report_known_path REVIEW 'Claude logs' "$HOME/Library/Logs/Claude"
  report_known_path REVIEW 'Codex logs' "$HOME/Library/Logs/Codex"
  report_known_path REVIEW 'Cursor logs' "$HOME/Library/Application Support/Cursor/logs"
  report_known_path REVIEW 'Windsurf logs' "$HOME/Library/Application Support/Windsurf/logs"
  report_known_path REVIEW 'Kiro logs' "$HOME/Library/Application Support/Kiro/logs"
  report_known_path REVIEW 'Trae logs' "$HOME/Library/Application Support/Trae/logs"
  report_known_path REVIEW 'Claude Service Worker cache' "$HOME/Library/Application Support/Claude/Service Worker/CacheStorage"
  report_known_path REVIEW 'Cursor Service Worker cache' "$HOME/Library/Application Support/Cursor/Service Worker/CacheStorage"
  report_known_path REVIEW 'Windsurf Service Worker cache' "$HOME/Library/Application Support/Windsurf/Service Worker/CacheStorage"

  printf '\n[PROTECTED sessions, worktrees, settings, credentials and application state]\n'
  report_known_path PROTECTED 'Codex sessions' "$HOME/.codex/sessions"
  report_known_path PROTECTED 'Codex archived sessions' "$HOME/.codex/archived_sessions"
  report_known_path PROTECTED 'Codex worktrees' "$HOME/.codex/worktrees"
  report_known_path PROTECTED 'Codex memories' "$HOME/.codex/memories"
  report_known_path PROTECTED 'Codex plugins' "$HOME/.codex/plugins"
  report_known_path PROTECTED 'Codex skills' "$HOME/.codex/skills"
  report_known_path PROTECTED 'Codex credentials' "$HOME/.codex/auth.json"
  report_known_path PROTECTED 'Codex configuration' "$HOME/.codex/config.toml"
  report_known_path PROTECTED 'Codex state database' "$HOME/.codex/state_5.sqlite"
  report_known_path PROTECTED 'Claude projects/sessions' "$HOME/.claude/projects"
  report_known_path PROTECTED 'Claude file-history' "$HOME/.claude/file-history"
  report_known_path PROTECTED 'Claude tasks' "$HOME/.claude/tasks"
  report_known_path PROTECTED 'Claude todos' "$HOME/.claude/todos"
  report_known_path PROTECTED 'Claude plans' "$HOME/.claude/plans"
  report_known_path PROTECTED 'Claude session-env' "$HOME/.claude/session-env"
  report_known_path PROTECTED 'Claude teams' "$HOME/.claude/teams"
  report_known_path PROTECTED 'Claude hooks' "$HOME/.claude/hooks"
  report_known_path PROTECTED 'Claude skills' "$HOME/.claude/skills"
  report_known_path PROTECTED 'Claude history' "$HOME/.claude/history.jsonl"
  report_known_path PROTECTED 'Claude configuration' "$HOME/.claude/settings.json"
  report_known_path PROTECTED 'Claude account state' "$HOME/.claude.json"
  report_known_path PROTECTED 'Claude VM bundles' "$HOME/Library/Application Support/Claude/vm_bundles"
  report_known_path PROTECTED 'Claude Local Storage' "$HOME/Library/Application Support/Claude/Local Storage"
  report_known_path PROTECTED 'Claude IndexedDB' "$HOME/Library/Application Support/Claude/IndexedDB"
  report_known_path PROTECTED 'Cursor user data' "$HOME/.cursor"
  report_known_path PROTECTED 'Cursor settings/state' "$HOME/Library/Application Support/Cursor/User"
  report_known_path PROTECTED 'Windsurf user data' "$HOME/.windsurf"
  report_known_path PROTECTED 'Windsurf settings/state' "$HOME/Library/Application Support/Windsurf/User"
  report_known_path PROTECTED 'Kiro user data' "$HOME/.kiro"
  report_known_path PROTECTED 'Kiro settings/state' "$HOME/Library/Application Support/Kiro/User"
  report_known_path PROTECTED 'Trae user data' "$HOME/.trae"
  report_known_path PROTECTED 'Trae settings/state' "$HOME/Library/Application Support/Trae/User"
  report_known_path PROTECTED 'OpenCode application state' "$HOME/.local/share/opencode"

  printf '\n[Related running processes — evidence only, never auto-kill]\n'
  ps -axo pid=,ppid=,etime=,comm= 2>/dev/null | awk '
    {
      line=tolower($0)
      if (line ~ /cursoruiviewservice/) next
      if (line ~ /claude|codex|cursor|windsurf|kiro|trae|opencode|mcp-server|model-context-protocol/) print
    }
  ' || true

  printf '\n[AI tool data totals — categories are not deletion authorization]\n'
  awk -v rebuildable="$AI_REBUILDABLE_KB" -v review="$AI_REVIEW_KB" -v protected="$AI_PROTECTED_KB" \
    'BEGIN {printf "REBUILDABLE %.1f MiB\nREVIEW      %.1f MiB\nPROTECTED   %.1f MiB\n", rebuildable/1024, review/1024, protected/1024}'
}

dotfiles_preview() {
  local script_dir
  local cache_min_mb
  script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
  cache_min_mb="${DOTFILES_CACHE_MIN_MB:-10}"
  python3 "$script_dir/dotfiles_audit.py" --cache-min-size-mb "$cache_min_mb"
}

case "$mode" in
  overview)
    disk_overview
    ;;
  mole)
    mole_preview
    ;;
  projects)
    project_preview
    ;;
  installers)
    installer_preview
    ;;
  docker)
    docker_preview
    ;;
  brew)
    brew_preview
    ;;
  ai)
    ai_tool_preview
    ;;
  dotfiles)
    dotfiles_preview
    ;;
  all)
    disk_overview
    project_preview
    installer_preview
    docker_preview
    brew_preview
    ai_tool_preview
    dotfiles_preview
    ;;
  *)
    usage >&2
    exit 2
    ;;
esac
