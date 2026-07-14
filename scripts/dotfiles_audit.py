#!/usr/bin/env python3
"""Read-only audit of top-level hidden home directories on macOS."""

from __future__ import annotations

import argparse
import os
import shutil
import stat
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True)
class OwnerRule:
    label: str
    commands: tuple[str, ...] = ()
    apps: tuple[str, ...] = ()
    brew: tuple[str, ...] = ()
    process_tokens: tuple[str, ...] = ()
    protected: bool = False
    review: bool = False
    plugin_tokens: tuple[str, ...] = ()
    project_markers: tuple[str, ...] = ()


RULES: dict[str, OwnerRule] = {
    ".android": OwnerRule("Android tools", ("adb", "sdkmanager"), ("Android Studio.app",), ("android-platform-tools",), protected=True),
    ".ansible": OwnerRule("Ansible", ("ansible",), brew=("ansible",), protected=True),
    ".aws": OwnerRule("AWS CLI", ("aws",), brew=("awscli",), protected=True),
    ".azure": OwnerRule("Azure CLI", ("az",), brew=("azure-cli",), protected=True),
    ".bun": OwnerRule("Bun", ("bun",), brew=("bun",), protected=True),
    ".cargo": OwnerRule("Rust Cargo", ("cargo",), brew=("rust",), protected=True),
    ".claude": OwnerRule("Claude Code", ("claude",), ("Claude.app",), process_tokens=("claude",), protected=True),
    ".codex": OwnerRule("Codex", ("codex",), ("Codex.app",), process_tokens=("codex",), protected=True),
    ".cocoapods": OwnerRule("CocoaPods", ("pod",), brew=("cocoapods",), protected=True),
    ".colima": OwnerRule("Colima", ("colima",), brew=("colima",), protected=True),
    ".config": OwnerRule("XDG application configuration", protected=True),
    ".cursor": OwnerRule("Cursor", ("cursor",), ("Cursor.app",), ("cursor",), ("cursor",), protected=True),
    ".dart": OwnerRule("Dart", ("dart",), brew=("dart",), protected=True),
    ".deno": OwnerRule("Deno", ("deno",), brew=("deno",), protected=True),
    ".docker": OwnerRule("Docker", ("docker",), ("Docker.app",), ("docker", "docker-desktop"), ("docker",), protected=True),
    ".gem": OwnerRule("RubyGems", ("gem",), protected=True),
    ".gnupg": OwnerRule("GnuPG credentials", ("gpg",), brew=("gnupg",), protected=True),
    ".gradle": OwnerRule("Gradle", ("gradle",), brew=("gradle",), protected=True, project_markers=("gradlew",)),
    ".helm": OwnerRule("Helm", ("helm",), brew=("helm",), protected=True),
    ".ivy2": OwnerRule("Ivy dependency data", protected=True),
    ".jenv": OwnerRule("jenv", ("jenv",), brew=("jenv",), protected=True),
    ".kiro": OwnerRule("Kiro", ("kiro",), ("Kiro.app",), process_tokens=("kiro",), protected=True),
    ".kube": OwnerRule("Kubernetes", ("kubectl",), brew=("kubernetes-cli",), protected=True),
    ".lima": OwnerRule("Lima", ("limactl",), brew=("lima",), protected=True),
    ".local": OwnerRule("User-local programs and application state", protected=True),
    ".m2": OwnerRule("Maven repository and settings", ("mvn",), brew=("maven",), protected=True),
    ".minikube": OwnerRule("Minikube", ("minikube",), brew=("minikube",), protected=True),
    ".npm": OwnerRule("npm", ("npm",), brew=("node",), protected=True),
    ".nvm": OwnerRule("nvm and Node runtimes", ("node", "npm"), protected=True),
    ".ollama": OwnerRule("Ollama models and state", ("ollama",), ("Ollama.app",), ("ollama",), ("ollama",), protected=True),
    ".orbstack": OwnerRule("OrbStack", ("orb",), ("OrbStack.app",), ("orbstack",), ("orbstack",), protected=True),
    ".pnpm-store": OwnerRule("pnpm store", ("pnpm",), brew=("pnpm",), protected=True),
    ".pub-cache": OwnerRule("Dart and Flutter package cache", ("dart", "flutter"), protected=True, project_markers=("pubspec.yaml",)),
    ".pyenv": OwnerRule("pyenv", ("pyenv",), brew=("pyenv",), protected=True),
    ".rbenv": OwnerRule("rbenv", ("rbenv",), brew=("rbenv",), protected=True),
    ".rustup": OwnerRule("Rust toolchains", ("rustup", "cargo"), protected=True),
    ".sbt": OwnerRule("sbt", ("sbt",), brew=("sbt",), protected=True),
    ".sdkman": OwnerRule("SDKMAN toolchains", protected=True),
    ".ssh": OwnerRule("SSH credentials and configuration", ("ssh",), protected=True),
    ".terraform.d": OwnerRule("Terraform plugins and configuration", ("terraform",), brew=("terraform",), protected=True),
    ".trae": OwnerRule("Trae", ("trae",), ("Trae.app",), process_tokens=("trae",), protected=True),
    ".Trash": OwnerRule("macOS Trash", review=True),
    ".vagrant.d": OwnerRule("Vagrant boxes and configuration", ("vagrant",), ("Vagrant Manager.app",), ("vagrant",), protected=True),
    ".vscode": OwnerRule("Visual Studio Code extensions and state", ("code",), ("Visual Studio Code.app",), ("visual-studio-code",), ("visual studio code",), protected=True),
    ".warp": OwnerRule("Warp terminal", ("warp",), ("Warp.app",), ("warp",), ("warp",), protected=True),
    ".windsurf": OwnerRule("Windsurf", ("windsurf",), ("Windsurf.app",), ("windsurf",), ("windsurf",), protected=True),
    ".yarn": OwnerRule("Yarn", ("yarn",), brew=("yarn",), protected=True),
    ".agent-browser": OwnerRule("Agent Browser runtime", ("agent-browser",), process_tokens=("agent-browser",), protected=True),
    ".agents": OwnerRule("Shared agent skills and state", protected=True),
    ".cc-switch": OwnerRule("CC Switch", apps=("CC Switch.app",), process_tokens=("cc-switch",), protected=True),
    ".cherrystudio": OwnerRule("Cherry Studio", apps=("Cherry Studio.app",), process_tokens=("cherry studio",), protected=True),
    ".chromium-browser-snapshots": OwnerRule("Downloaded Chromium runtime", review=True),
    ".codebuddy": OwnerRule("CodeBuddy", apps=("CodeBuddy.app",), process_tokens=("codebuddy",), protected=True),
    ".codebuddycn": OwnerRule("CodeBuddy CN", apps=("CodeBuddy CN.app",), process_tokens=("codebuddy",), protected=True),
    ".codeium": OwnerRule("Windsurf/Codeium state", apps=("Windsurf.app",), process_tokens=("windsurf", "codeium"), protected=True),
    ".conda": OwnerRule("Conda configuration and environments", ("conda",), protected=True),
    ".gemini": OwnerRule("Gemini/Antigravity state", ("gemini",), ("Gemini.app", "Antigravity.app"), process_tokens=("gemini", "antigravity"), protected=True),
    ".graphify": OwnerRule("Graphify repository indexes", ("graphify",), protected=True),
    ".hermes": OwnerRule("Hermes", ("hermes",), ("Hermes One.app",), process_tokens=("hermes",), protected=True),
    ".ipython": OwnerRule("IPython history and configuration", ("ipython",), protected=True),
    ".jrebel": OwnerRule("JRebel", ("jrebel",), protected=True, plugin_tokens=("jrebel", "jr-ide-idea")),
    ".marscode": OwnerRule("MarsCode", ("marscode",), protected=True, plugin_tokens=("marscode",)),
    ".nexview": OwnerRule("NexView", ("nexview",), ("NexView.app",), process_tokens=("nexview",), protected=True),
    ".opencode": OwnerRule("OpenCode state", ("opencode",), protected=True),
    ".qoder": OwnerRule("Qoder", ("qoder",), ("Qoder.app",), process_tokens=("qoder",), protected=True),
    ".qoderwork": OwnerRule("QoderWork", apps=("QoderWork.app",), process_tokens=("qoderwork",), protected=True),
    ".qwenpaw": OwnerRule("QwenPaw", ("qwenpaw",), process_tokens=("qwenpaw",), protected=True),
    ".semantic_search": OwnerRule("Semantic search models", protected=True),
    ".swiftpm": OwnerRule("Swift Package Manager state", ("swift",), protected=True),
    ".vibe-island": OwnerRule("Vibe Island", apps=("Vibe Island.app",), process_tokens=("vibe-island",), protected=True),
    ".vibe-kanban": OwnerRule("Vibe Kanban", ("vibe-kanban",), process_tokens=("vibe-kanban",), protected=True),
    ".walle": OwnerRule("Walle", ("walle",), ("Walle.app",), process_tokens=("walle",), protected=True),
    ".workbuddy": OwnerRule("WorkBuddy", ("workbuddy",), ("WorkBuddy.app",), process_tokens=("workbuddy",), protected=True),
    ".zcode": OwnerRule("Zcode agents and sessions", ("zcode",), ("Zcode.app",), process_tokens=("zcode",), protected=True),
    ".zsh_sessions": OwnerRule("Shell session history", protected=True),
    ".cache": OwnerRule("Mixed XDG caches", review=True),
}


CACHE_RULES: dict[str, OwnerRule] = {
    "Homebrew": OwnerRule("Homebrew cache", ("brew",)),
    "go-build": OwnerRule("Go build cache", ("go",)),
    "ms-playwright": OwnerRule("Playwright browsers", ("playwright",)),
    "pip": OwnerRule("pip cache", ("pip", "pip3")),
    "pnpm": OwnerRule("pnpm cache", ("pnpm",)),
    "pre-commit": OwnerRule("pre-commit cache", ("pre-commit",)),
    "ruff": OwnerRule("Ruff cache", ("ruff",)),
    "uv": OwnerRule("uv cache", ("uv",)),
    "yarn": OwnerRule("Yarn cache", ("yarn",)),
}


KNOWN_CACHE_SUBPATHS = (
    (".npm/_cacache", "npm content cache", ("npm",)),
    (".npm/_logs", "npm logs", ("npm",)),
    (".npm/_npx", "npx package cache", ("npx",)),
    (".bun/install/cache", "Bun install cache", ("bun",)),
    (".cargo/registry/cache", "Cargo registry cache", ("cargo",)),
    (".cargo/git/db", "Cargo git dependency cache", ("cargo",)),
    (".gradle/caches", "Gradle dependency/build cache", ("gradle",)),
    (".rustup/downloads", "Rustup download cache", ("rustup",)),
)


CONFIG_FILES = (
    ".zshrc",
    ".zprofile",
    ".bashrc",
    ".bash_profile",
    ".profile",
    ".gitconfig",
    ".config/fish/config.fish",
)


def run_lines(command: list[str], timeout: int = 15) -> list[str]:
    try:
        result = subprocess.run(
            command,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=timeout,
        )
    except (OSError, subprocess.TimeoutExpired):
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def size_kib(path: Path) -> int | None:
    lines = run_lines(["/usr/bin/du", "-sk", str(path)], timeout=30)
    if not lines:
        return None
    try:
        return int(lines[0].split()[0])
    except (ValueError, IndexError):
        return None


def modified_date(path: Path) -> str:
    try:
        return datetime.fromtimestamp(path.lstat().st_mtime).strftime("%Y-%m-%d")
    except OSError:
        return "unknown"


def regular_config_bytes(path: Path) -> bytes | None:
    try:
        mode = path.lstat().st_mode
        if not stat.S_ISREG(mode) or path.stat().st_size > 2 * 1024 * 1024:
            return None
        return path.read_bytes()
    except OSError:
        return None


class EvidenceIndex:
    def __init__(self, home: Path) -> None:
        self.home = home
        self.apps = self._apps()
        self.brew = self._brew()
        self.processes = "\n".join(run_lines(["/bin/ps", "-axo", "comm="])).casefold()
        self.launch_agents = self._launch_agents()
        self.ide_plugins = self._ide_plugins()
        self.project_markers = self._project_markers()
        self.configs = self._configs()

    def _apps(self) -> set[str]:
        result: set[str] = set()
        for root in (Path("/Applications"), self.home / "Applications", Path("/System/Applications")):
            try:
                for entry in os.scandir(root):
                    if entry.name.endswith(".app"):
                        result.add(entry.name.casefold())
            except OSError:
                continue
        for app_path in run_lines(["/usr/bin/mdfind", 'kMDItemContentType == "com.apple.application-bundle"'], timeout=30):
            name = Path(app_path).name
            if name.endswith(".app"):
                result.add(name.casefold())
        return result

    def _brew(self) -> set[str]:
        brew = shutil.which("brew")
        if not brew:
            return set()
        values = run_lines([brew, "list", "--formula"], timeout=30)
        values += run_lines([brew, "list", "--cask"], timeout=30)
        return {value.casefold() for value in values}

    def _launch_agents(self) -> str:
        root = self.home / "Library/LaunchAgents"
        try:
            return "\n".join(entry.name for entry in os.scandir(root)).casefold()
        except OSError:
            return ""

    def _configs(self) -> dict[str, bytes]:
        result: dict[str, bytes] = {}
        for relative in CONFIG_FILES:
            path = self.home / relative
            data = regular_config_bytes(path)
            if data is not None:
                result[relative] = data
        return result

    def _ide_plugins(self) -> str:
        names: list[str] = []
        for root in (
            self.home / ".vscode/extensions",
            self.home / ".cursor/extensions",
            self.home / ".windsurf/extensions",
        ):
            try:
                names.extend(entry.name for entry in os.scandir(root) if entry.is_dir(follow_symlinks=False))
            except OSError:
                continue

        jetbrains = self.home / "Library/Application Support/JetBrains"
        try:
            products = [entry for entry in os.scandir(jetbrains) if entry.is_dir(follow_symlinks=False)]
        except OSError:
            products = []
        for product in products:
            plugins = Path(product.path) / "plugins"
            try:
                names.extend(entry.name for entry in os.scandir(plugins) if entry.is_dir(follow_symlinks=False))
            except OSError:
                continue
        return "\n".join(names).casefold()

    def _project_markers(self) -> set[str]:
        markers: set[str] = set()
        excluded = {".git", ".private", "node_modules", "target", "build", ".dart_tool", ".gradle"}
        for root in (self.home / "Documents/Projects", self.home / "workers", self.home / "bees"):
            if not root.is_dir():
                continue
            for _current, directories, files in os.walk(root, followlinks=False):
                directories[:] = [name for name in directories if name not in excluded]
                if "gradlew" in files:
                    markers.add("gradlew")
                if "pubspec.yaml" in files:
                    markers.add("pubspec.yaml")
                if {"gradlew", "pubspec.yaml"}.issubset(markers):
                    return markers
        return markers

    def evidence(self, dot_name: str, rule: OwnerRule | None) -> list[str]:
        evidence: list[str] = []
        if rule:
            for app in rule.apps:
                if app.casefold() in self.apps:
                    evidence.append(f"app={app}")
            for command in rule.commands:
                resolved = shutil.which(command)
                if resolved:
                    evidence.append(f"cli={command}")
            for package in rule.brew:
                if package.casefold() in self.brew:
                    evidence.append(f"brew={package}")
            for token in rule.process_tokens:
                if token.casefold() in self.processes:
                    evidence.append(f"process={token}")
                if token.casefold() in self.launch_agents:
                    evidence.append(f"launchagent={token}")
            for token in rule.plugin_tokens:
                if token.casefold() in self.ide_plugins:
                    evidence.append(f"ide-plugin={token}")
            for marker in rule.project_markers:
                if marker in self.project_markers:
                    evidence.append(f"project-marker={marker}")

        patterns = (
            str(self.home / dot_name).encode(),
            f"~/{dot_name}".encode(),
            f"$HOME/{dot_name}".encode(),
            f"${{HOME}}/{dot_name}".encode(),
        )
        for relative, data in self.configs.items():
            if any(pattern in data for pattern in patterns):
                evidence.append(f"config={relative}")
        return evidence


def status_for(rule: OwnerRule | None, evidence: list[str]) -> str:
    if rule and rule.protected:
        owner_checks = bool(
            rule.commands
            or rule.apps
            or rule.brew
            or rule.process_tokens
            or rule.plugin_tokens
            or rule.project_markers
        )
        if evidence:
            return "PROTECTED_ACTIVE"
        if owner_checks:
            return "PROTECTED_NO_OWNER"
        return "PROTECTED"
    if evidence:
        return "ACTIVE"
    if rule and rule.review:
        return "REVIEW"
    if rule:
        return "NO_OWNER_EVIDENCE"
    return "UNKNOWN"


def format_size(kib: int | None) -> str:
    return "unknown" if kib is None else f"{kib / 1024:.1f} MiB"


def print_row(status: str, size: int | None, modified: str, label: str, path: Path, evidence: list[str]) -> None:
    evidence_text = ",".join(evidence[:6]) if evidence else "-"
    print(f"{status:<18}\t{format_size(size):>12}\t{modified}\t{label}\t{path}\t{evidence_text}")


def hidden_directories(home: Path) -> list[Path]:
    result: list[Path] = []
    try:
        entries = os.scandir(home)
    except OSError:
        return result
    with entries:
        for entry in entries:
            if entry.name == ".private" or not entry.name.startswith("."):
                continue
            try:
                if entry.is_dir(follow_symlinks=False):
                    result.append(Path(entry.path))
            except OSError:
                continue
    return result


def cache_children(home: Path, minimum_kib: int) -> list[tuple[int | None, Path]]:
    root = home / ".cache"
    result: list[tuple[int | None, Path]] = []
    try:
        entries = os.scandir(root)
    except OSError:
        return result
    with entries:
        for entry in entries:
            if entry.name == ".private":
                continue
            try:
                if not entry.is_dir(follow_symlinks=False):
                    continue
            except OSError:
                continue
            path = Path(entry.path)
            size = size_kib(path)
            if size is None or size >= minimum_kib:
                result.append((size, path))
    return sorted(result, key=lambda item: item[0] if item[0] is not None else -1, reverse=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache-min-size-mb", type=float, default=10.0)
    args = parser.parse_args()
    home = Path.home()
    evidence_index = EvidenceIndex(home)

    print("[Top-level hidden home directories]")
    print("Read-only metadata audit. .private is excluded; session and credential contents are not read.")
    rows = []
    for path in hidden_directories(home):
        size = size_kib(path)
        rows.append((size, path))
    rows.sort(key=lambda item: item[0] if item[0] is not None else -1, reverse=True)
    for size, path in rows:
        rule = RULES.get(path.name)
        evidence = evidence_index.evidence(path.name, rule)
        label = rule.label if rule else "Unmapped hidden directory"
        print_row(status_for(rule, evidence), size, modified_date(path), label, path, evidence)

    print("\n[Known cache subpaths]")
    print("Exact cache paths only. Presence here is not deletion authorization.")
    for relative, label, commands in KNOWN_CACHE_SUBPATHS:
        path = home / relative
        if not path.exists():
            continue
        evidence = [f"cli={command}" for command in commands if shutil.which(command)]
        print_row("REBUILDABLE", size_kib(path), modified_date(path), label, path, evidence)

    print(f"\n[.cache children >= {args.cache_min_size_mb:g} MiB]")
    print("NO_OWNER_EVIDENCE means only that the limited evidence sources found no owner.")
    minimum_kib = max(0, int(args.cache_min_size_mb * 1024))
    for size, path in cache_children(home, minimum_kib):
        rule = CACHE_RULES.get(path.name)
        evidence = evidence_index.evidence(f".cache/{path.name}", rule)
        if rule and evidence:
            status = "OWNER_ACTIVE"
            label = rule.label
        elif rule:
            status = "NO_OWNER_EVIDENCE"
            label = rule.label
        else:
            status = "UNKNOWN_OWNER"
            label = "Unmapped cache owner"
        print_row(status, size, modified_date(path), label, path, evidence)

    print("\nNo files were deleted. NO_OWNER_EVIDENCE, PROTECTED_NO_OWNER and UNKNOWN require further inspection.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
