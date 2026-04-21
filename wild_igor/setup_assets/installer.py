"""
installer.py — D321 unified entry point for Igor (T-installer-cfg-split stage 2).

Called by the thin igor (bash) and igor.ps1 (Windows) shell wrappers after they
ensure Python + venv exist.

Responsibilities (in order):
  1. Apply pending migrations (idempotent, sentinel files track state)
  2. Run the Igor restart loop (replaces bash restart loop from igor shell script)

Migration sentinels: ~/.TheIgors/swarm/migrations/NNN.done
  001.done — .env distributed to split cfg files (D319)
  002.done — .env renamed to .env.backup-pre-d319 (T-installer-stage3)
  003.done — Claude Code bootstrap: MCP config, skill symlinks, memory seeds

Usage:
  python installer.py [--id INSTANCE_ID] [--help]
  python installer.py --uninstall-cc  # remove CC skill symlinks + MCP config
"""

from __future__ import annotations

import argparse
import logging
import os
import platform
import re
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from string import Template

log = logging.getLogger("installer")

# ── Paths ─────────────────────────────────────────────────────────────────────

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent  # TheIgors/
_WILD_DIR = _REPO_ROOT / "wild_igor"
_TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"
_RUNTIME_ROOT = Path(os.environ.get("IGOR_RUNTIME_ROOT", Path.home() / ".TheIgors"))
_SWARM_DIR = _RUNTIME_ROOT / "swarm"
_MIGRATIONS_DIR = _SWARM_DIR / "migrations"

# ── Key distribution map for migration_001 ────────────────────────────────────
# Keys that go explicitly to a named cfg file.  Keys not listed here fall
# through to the _classify_key() suffix-matching logic.

_KEY_TO_CFG: dict[str, str] = {
    # swarm.cfg — box-level DB
    "IGOR_HOME_DB_URL": "swarm.cfg",
    "IGOR_DB_URL": "swarm.cfg",
    "IGOR_LOCAL_DB_URL": "swarm.cfg",
    # igor.cfg — instance identity
    "IGOR_INSTANCE_ID": "igor.cfg",
    "IGOR_WEB_PORT": "igor.cfg",
    "IGOR_RUNTIME_ROOT": "igor.cfg",
    "IGOR_SSL_CERT": "igor.cfg",
    "IGOR_SSL_KEY": "igor.cfg",
    "IGOR_BACKCHANNEL": "igor.cfg",
    # igor.credentials.cfg — secrets / API keys
    "ANTHROPIC_API_KEY": "igor.credentials.cfg",
    "ANTHROPIC_AUTH_TOKEN": "igor.credentials.cfg",
    "ANTHROPIC_BASE_URL": "igor.credentials.cfg",
    "REAL_ANTHROPIC_API_KEY": "igor.credentials.cfg",
    "OPENROUTER_API_KEY": "igor.credentials.cfg",
    "DISCORD_BOT_TOKEN": "igor.credentials.cfg",
    "DISCORD_CHANNEL_ID": "igor.credentials.cfg",
    "DISCORD_GUILD_ID": "igor.credentials.cfg",
    "GITHUB_API_KEY": "igor.credentials.cfg",
    "GMAIL_CLIENT_ID": "igor.credentials.cfg",
    "GMAIL_CLIENT_SECRET": "igor.credentials.cfg",
    "GMAIL_REFRESH_TOKEN": "igor.credentials.cfg",
    "GAMIL_PASSWORD": "igor.credentials.cfg",  # legacy typo preserved
    "IGOR_EMAIL": "igor.credentials.cfg",
    "ConfluenceAPIKey": "igor.credentials.cfg",
    "WINDOWS_USER_AKIEN": "igor.credentials.cfg",
    "WINDOWS_USER_AKIEN_PW": "igor.credentials.cfg",
    "WINDOWS_USER_IGOR_USER": "igor.credentials.cfg",
    "WINDOWS_USER_IGOR_PW": "igor.credentials.cfg",
    "IGOR_SSH_PUBLIC_KEY": "igor.credentials.cfg",
    # igor.context.akien.cfg — non-confidential Akien context
    "CONFLUENCE_DOMAIN": "igor.context.akien.cfg",
    "CONFLUENCE_EMAIL": "igor.context.akien.cfg",
    "SPACE_KEY": "igor.context.akien.cfg",
    "EMPLOYER_CHROME_PROFILE_PATH": "igor.context.akien.cfg",
}

# Prefix patterns for keys not in _KEY_TO_CFG (checked in order, first match wins).
_PREFIX_TO_CFG: list[tuple[str, str]] = [
    # Model routing
    ("OLLAMA_", "igor.models.cfg"),
    ("IGOR_NE_LOCAL_", "igor.models.cfg"),
    ("IGOR_NE_ROUTING", "igor.models.cfg"),
    ("IGOR_WINNOW_LOCAL_", "igor.models.cfg"),
    ("IGOR_OLLAMA", "igor.models.cfg"),
    ("IGOR_LATENCY_ADAPTIVE", "igor.models.cfg"),
    ("OPENROUTER_", "igor.models.cfg"),
    # Feature switches (must come after specific model keys)
    ("IGOR_", "igor.switches.cfg"),
]

_CREDENTIALS_CFGS = {"igor.credentials.cfg", "igor.context.akien.confidential.cfg"}


def _classify_key(key: str) -> str:
    """Return the cfg filename for a given .env key."""
    if key in _KEY_TO_CFG:
        return _KEY_TO_CFG[key]
    for prefix, cfg in _PREFIX_TO_CFG:
        if key.startswith(prefix):
            return cfg
    return "igor.cfg"  # catch-all


# ── Migration 001: .env → split cfg files ─────────────────────────────────────


def _parse_env_file(env_path: Path) -> dict[str, str]:
    """Parse a KEY=VALUE env file, stripping comments and blank lines."""
    result: dict[str, str] = {}
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip()
            # Strip surrounding quotes
            if len(value) >= 2 and value[0] in ('"', "'") and value[-1] == value[0]:
                value = value[1:-1]
            result[key] = value
    return result


def _write_cfg_block(path: Path, entries: dict[str, str]) -> None:
    """Append KEY=VALUE lines to a cfg file, creating it if needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = set()
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*=", line)
            if m:
                existing.add(m.group(1))
    with path.open("a", encoding="utf-8") as f:
        for key, value in entries.items():
            if key not in existing:
                f.write(f"{key}={value}\n")


def _expand_template(src: Path, dest: Path, substitutions: dict[str, str]) -> None:
    """Expand a .template file to dest using string.Template substitution."""
    if dest.exists():
        return  # idempotent — never overwrite user-edited files
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmpl = Template(src.read_text(encoding="utf-8"))
    dest.write_text(
        tmpl.safe_substitute(substitutions),
        encoding="utf-8",
    )


def migration_001(instance_dir: Path) -> None:
    """
    Distribute .env keys to split cfg files (D319).

    Reads INSTANCE_DIR/.env, classifies each key, and appends it to the
    appropriate cfg file (swarm.cfg, igor.cfg, igor.models.cfg,
    igor.switches.cfg, igor.credentials.cfg, igor.context.*.cfg).

    Idempotent: keys already present in target cfg files are not duplicated.
    Does NOT delete .env — that is migration_002 (T-installer-stage3).
    """
    env_file = instance_dir / ".env"
    if not env_file.exists():
        log.info("migration_001: no .env found — skipping distribution")
        _bootstrap_cfg_templates(instance_dir)
        return

    log.info(f"migration_001: distributing {env_file}")
    env = _parse_env_file(env_file)

    # Group keys by target cfg file
    buckets: dict[str, dict[str, str]] = {}
    for key, value in env.items():
        cfg_name = _classify_key(key)
        buckets.setdefault(cfg_name, {})[key] = value

    # Derive swarm_dir from instance_dir so tests are automatically isolated
    swarm_dir = instance_dir.parent / "swarm"

    # Write each bucket
    for cfg_name, entries in buckets.items():
        if cfg_name == "swarm.cfg":
            dest = swarm_dir / cfg_name
        else:
            dest = instance_dir / cfg_name
        log.info(f"migration_001: writing {len(entries)} keys → {dest}")
        # Add header comment on first creation
        if not dest.exists():
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(
                f"# {cfg_name} — migrated from .env by installer.py migration_001\n",
                encoding="utf-8",
            )
        _write_cfg_block(dest, entries)

    # Expand any missing cfg templates (for files with no matching keys in .env)
    _bootstrap_cfg_templates(instance_dir)

    log.info("migration_001: complete")


def _bootstrap_cfg_templates(instance_dir: Path) -> None:
    """Expand any template files not yet present in instance_dir or swarm/."""
    swarm_dir = instance_dir.parent / "swarm"
    instance_id = instance_dir.name
    subs = {
        "IGOR_INSTANCE_ID": instance_id,
        "IGOR_RUNTIME_ROOT": str(instance_dir.parent),
        "IGOR_HOME_DB_URL": "",
        "SWARM_ID": "",
        "IGOR_WEB_PORT": "8080",
        "OPENROUTER_API_KEY": "",
        "ANTHROPIC_API_KEY": "",
        "IGOR_SSH_PRIVATE_KEY_PATH": "",
    }
    for tmpl_path in _TEMPLATES_DIR.glob("*.template"):
        stem = tmpl_path.stem  # e.g. "swarm.cfg"
        if stem == "swarm.cfg":
            dest = swarm_dir / stem
        else:
            dest = instance_dir / stem
        _expand_template(tmpl_path, dest, subs)


# ── Migration runner ──────────────────────────────────────────────────────────


def migration_002(instance_dir: Path) -> None:
    """
    Retire .env by renaming it to .env.backup-pre-d319 (D319, T-installer-stage3).

    Guards: only runs after 001.done exists AND all expected cfg files are non-empty.
    Soft delete — the backup is retained for at least one session.
    """
    env_file = instance_dir / ".env"
    if not env_file.exists():
        log.info("migration_002: no .env to retire — skipping")
        return

    # Verify all expected instance cfg files are present and non-empty
    required = [
        instance_dir / "igor.cfg",
        instance_dir / "igor.switches.cfg",
        instance_dir / "igor.models.cfg",
        instance_dir / "igor.credentials.cfg",
    ]
    missing = [p for p in required if not p.exists() or p.stat().st_size < 10]
    if missing:
        log.warning(
            f"migration_002: skipping — missing/empty cfg files: "
            f"{[p.name for p in missing]}"
        )
        return

    # Check swarm.cfg is present and contains IGOR_HOME_DB_URL
    swarm_cfg = instance_dir.parent / "swarm" / "swarm.cfg"
    if not swarm_cfg.exists() or "IGOR_HOME_DB_URL" not in swarm_cfg.read_text():
        log.warning(
            "migration_002: skipping — swarm.cfg missing or lacks IGOR_HOME_DB_URL"
        )
        return

    # Soft delete
    backup = env_file.with_name(".env.backup-pre-d319")
    env_file.rename(backup)
    log.info(f"migration_002: .env renamed to {backup}")


# ── Migration 003: Claude Code bootstrap ────────────────────────────────────


def _cc_project_key(repo_root: Path) -> str:
    """Compute the CC project key the same way Claude Code does."""
    # CC uses the absolute path with separators replaced by dashes
    raw = str(repo_root).replace("\\", "-").replace("/", "-")
    # On Linux paths start with / so raw already starts with -
    # On Windows we strip the colon: C:\foo → -C-foo
    raw = raw.replace(":", "")
    if not raw.startswith("-"):
        raw = "-" + raw
    return raw


def _cc_memory_dir(repo_root: Path) -> Path:
    """Return the CC project memory directory for this repo."""
    key = _cc_project_key(repo_root)
    if platform.system() == "Windows":
        appdata = os.environ.get("APPDATA", str(Path.home() / "AppData" / "Roaming"))
        return Path(appdata) / "Claude" / "projects" / key / "memory"
    return Path.home() / ".claude" / "projects" / key / "memory"


def _cc_skills_dir() -> Path:
    """Return the user-level CC skills directory."""
    if platform.system() == "Windows":
        appdata = os.environ.get("APPDATA", str(Path.home() / "AppData" / "Roaming"))
        return Path(appdata) / "Claude" / "skills"
    return Path.home() / ".claude" / "skills"


def _merge_mcp_into_settings_local(settings_path: Path, mcp_entry: dict) -> None:
    """Add igor MCP server to settings.local.json, preserving existing content."""
    import json

    config: dict = {}
    if settings_path.exists():
        try:
            config = json.loads(settings_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, ValueError):
            log.warning("migration_003: settings.local.json malformed — rewriting")
            config = {}

    mcp = config.setdefault("mcpServers", {})
    if "igor" in mcp:
        log.info("migration_003: mcpServers.igor already in settings.local.json")
        return

    mcp["igor"] = mcp_entry
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    log.info(f"migration_003: added mcpServers.igor to {settings_path}")


def migration_003(instance_dir: Path) -> None:
    """
    Bootstrap Claude Code workflow: MCP config, skill symlinks, memory seeds.

    1. Merge igor MCP server into .claude/settings.local.json (non-destructive)
    2. Symlink skills from lab/claudecode/cc_skills/ → ~/.claude/skills/ (idempotent)
    3. Seed project memory from lab/claudecode/cc_memory_seed/ (don't overwrite)
    """
    repo_root = _REPO_ROOT
    skills_src = repo_root / "lab" / "claudecode" / "cc_skills"
    seed_dir = repo_root / "lab" / "claudecode" / "cc_memory_seed"

    # ── 1. MCP config ──
    if platform.system() == "Windows":
        python_path = str(repo_root / "venv" / "Scripts" / "python.exe")
    else:
        python_path = str(repo_root / "venv" / "bin" / "python")

    mcp_script = str(repo_root / "lab" / "claudecode" / "igor_mcp.py")
    db_url = os.environ.get(
        "IGOR_HOME_DB_URL",
        f"postgresql://igor:choose_a_password@127.0.0.1/{instance_dir.name}",
    )
    web_port = os.environ.get("IGOR_WEB_PORT", "8080")
    cc_send = os.environ.get("CC_SEND_URL", f"http://localhost:{web_port}/api/cc_send")

    settings_local = repo_root / ".claude" / "settings.local.json"
    _merge_mcp_into_settings_local(
        settings_local,
        {
            "command": python_path,
            "args": [mcp_script],
            "env": {
                "IGOR_HOME_DB_URL": db_url,
                "CC_SEND_URL": cc_send,
            },
        },
    )

    # ── 2. Skill symlinks ──
    skills_dest = _cc_skills_dir()
    skills_dest.mkdir(parents=True, exist_ok=True)
    linked = 0
    skipped = 0

    if skills_src.exists():
        for skill_dir in sorted(skills_src.iterdir()):
            if not skill_dir.is_dir():
                continue
            dest = skills_dest / skill_dir.name
            if dest.exists():
                # Already present (symlink or real dir) — don't touch
                skipped += 1
                continue
            try:
                dest.symlink_to(skill_dir.resolve())
                linked += 1
            except OSError as exc:
                # Windows without developer mode can't symlink — fall back to copy
                log.warning(
                    f"migration_003: symlink failed for {skill_dir.name}, "
                    f"copying instead — {exc}"
                )
                import shutil

                shutil.copytree(skill_dir, dest)
                linked += 1

    log.info(f"migration_003: skills linked={linked} skipped={skipped}")

    # ── 3. Memory seeds ──
    memory_dir = _cc_memory_dir(repo_root)
    seeded = 0
    mem_skipped = 0

    if seed_dir.exists():
        memory_dir.mkdir(parents=True, exist_ok=True)
        for f in sorted(seed_dir.glob("*.md")):
            dest = memory_dir / f.name
            if dest.exists():
                mem_skipped += 1
                continue
            import shutil

            shutil.copy2(f, dest)
            seeded += 1

    log.info(
        f"migration_003: memory seeded={seeded} skipped={mem_skipped} "
        f"→ {memory_dir}"
    )


# ── Uninstall CC ─────────────────────────────────────────────────────────────


def uninstall_cc() -> None:
    """
    Remove Claude Code skill symlinks installed by migration_003.

    Does NOT remove:
    - Memory seeds (user may have edited them)
    - settings.local.json (may contain user permissions)
    - CLAUDE.md or .claude/bootstrap.md (repo files, managed by git)
    """
    skills_dir = _cc_skills_dir()
    skills_src = _REPO_ROOT / "lab" / "claudecode" / "cc_skills"

    if not skills_src.exists():
        log.info("uninstall_cc: no cc_skills source dir — nothing to do")
        return

    removed = 0
    for skill_dir in sorted(skills_src.iterdir()):
        if not skill_dir.is_dir():
            continue
        dest = skills_dir / skill_dir.name
        if not dest.exists():
            continue
        # Only remove if it's a symlink pointing to our source
        if dest.is_symlink():
            target = dest.resolve()
            if target == skill_dir.resolve():
                dest.unlink()
                removed += 1
                log.info(f"uninstall_cc: removed symlink {dest}")
            else:
                log.info(
                    f"uninstall_cc: skipping {dest.name} — symlink points "
                    f"elsewhere ({target})"
                )
        else:
            # It's a real directory — check if it matches our skill (copied, not linked)
            skill_md = dest / "SKILL.md"
            src_md = skill_dir / "SKILL.md"
            if skill_md.exists() and src_md.exists():
                import shutil

                shutil.rmtree(dest)
                removed += 1
                log.info(f"uninstall_cc: removed copied skill dir {dest}")
            else:
                log.info(f"uninstall_cc: skipping {dest.name} — doesn't look like ours")

    print(f"[uninstall-cc] Removed {removed} skill(s) from {skills_dir}")

    # Optionally remove igor MCP entry from settings.local.json
    settings_local = _REPO_ROOT / ".claude" / "settings.local.json"
    if settings_local.exists():
        import json

        try:
            config = json.loads(settings_local.read_text(encoding="utf-8"))
            mcp = config.get("mcpServers", {})
            if "igor" in mcp:
                del mcp["igor"]
                settings_local.write_text(
                    json.dumps(config, indent=2) + "\n", encoding="utf-8"
                )
                print("[uninstall-cc] Removed igor MCP entry from settings.local.json")
        except (json.JSONDecodeError, ValueError):
            pass

    print("[uninstall-cc] Done. Memory seeds preserved (user data).")


_MIGRATIONS = [migration_001, migration_002, migration_003]


def run_migrations(instance_dir: Path) -> None:
    """Apply all pending migrations in numeric order."""
    migrations_dir = instance_dir.parent / "swarm" / "migrations"
    migrations_dir.mkdir(parents=True, exist_ok=True)
    for idx, fn in enumerate(_MIGRATIONS, start=1):
        sentinel = migrations_dir / f"{idx:03d}.done"
        if sentinel.exists():
            log.debug(f"migration {idx:03d}: already applied — skipping")
            continue
        log.info(f"Applying migration {idx:03d}: {fn.__name__}")
        fn(instance_dir)
        sentinel.write_text(
            datetime.now(timezone.utc).isoformat() + "\n", encoding="utf-8"
        )
        log.info(f"migration {idx:03d}: done → {sentinel}")


# ── Cfg loader ────────────────────────────────────────────────────────────────

_CFG_LOAD_ORDER = [
    "swarm.cfg",
    "igor.cfg",
    "igor.models.cfg",
    "igor.switches.cfg",
    "igor.credentials.cfg",
]


def load_cfg(instance_dir: Path) -> None:
    """
    Load cfg files in priority order into os.environ (last wins).

    Falls back to .env with a warning if cfg files are missing.
    Context cfg files (igor.context.*.cfg and igor.context.*.confidential.cfg)
    are loaded last (sorted), after the fixed-order files.
    """
    cfg_files: list[Path] = []

    # Fixed-order files
    for name in _CFG_LOAD_ORDER:
        if name == "swarm.cfg":
            p = _SWARM_DIR / name
        else:
            p = instance_dir / name
        if p.exists():
            cfg_files.append(p)

    # Context files (sorted for determinism)
    for p in sorted(instance_dir.glob("igor.context.*.cfg")):
        cfg_files.append(p)
    for p in sorted(instance_dir.glob("igor.context.*.confidential.cfg")):
        cfg_files.append(p)

    if not cfg_files:
        env_file = instance_dir / ".env"
        if env_file.exists():
            log.warning("load_cfg: no split cfg files found — falling back to .env")
            for key, value in _parse_env_file(env_file).items():
                os.environ.setdefault(key, value)
        else:
            log.warning("load_cfg: no cfg files and no .env — running unconfigured")
        return

    for p in cfg_files:
        for key, value in _parse_env_file(p).items():
            os.environ[key] = value  # last wins


# ── Restart loop ──────────────────────────────────────────────────────────────

_MAX_RESTARTS_PER_MINUTE = 4
_RESTART_WINDOW_SECS = 60


def _log_crash(
    instance_dir: Path,
    exit_code: int,
    traceback_tail: str,
    instance_id: str,
) -> None:
    """Append crash entry to alerts.txt."""
    alerts = _RUNTIME_ROOT / "alerts.txt"
    ts = datetime.now(timezone.utc).isoformat()
    with alerts.open("a", encoding="utf-8") as f:
        f.write("━" * 66 + "\n")
        f.write(f"CRASH: Igor (exit code: {exit_code})\n")
        f.write(f"Time: {ts}\n")
        f.write(f"Instance: {instance_id}\n")
        f.write(f"Hostname: {platform.node()}\n")
        f.write(
            f"User: {os.environ.get('USER', os.environ.get('USERNAME', 'unknown'))}\n"
        )
        if traceback_tail:
            f.write("\nLast output lines:\n")
            for line in traceback_tail.splitlines()[-20:]:
                f.write(f"  {line}\n")
        else:
            f.write(
                "\n(no output captured — check if exception went to an uncaptured stream)\n"
            )
        f.write("\n")


def _kill_stale_processes(web_port: str) -> None:
    """Kill leftover igor.main processes and free the web port."""
    if platform.system() == "Windows":
        return  # handled by igor.ps1 on Windows
    try:
        import subprocess as sp

        result = sp.run(
            ["pgrep", "-f", "igor.main"],
            capture_output=True,
            text=True,
        )
        own_pid = str(os.getpid())
        for pid in result.stdout.splitlines():
            if pid.strip() and pid.strip() != own_pid:
                try:
                    os.kill(int(pid), signal.SIGTERM)
                    time.sleep(0.5)
                    os.kill(int(pid), signal.SIGKILL)
                except ProcessLookupError:
                    pass
    except Exception:
        pass
    try:
        subprocess.run(
            ["fuser", "-k", f"{web_port}/tcp"],
            capture_output=True,
        )
    except Exception:
        pass


def restart_loop(instance_dir: Path, igor_args: list[str]) -> None:
    """
    Main Igor restart loop — replaces the bash restart loop in the igor script.

    Handles:
    - cfg reload on each restart
    - crash loop detection (>= 4 restarts in 60s → halt)
    - stale process cleanup
    - pause.wait file (halts loop until file is removed)
    - exit code 42 → restart
    - exit 0 / 130 / 143 → clean exit
    - other exit code → log crash, optionally launch claude auto-fixer
    """
    restart_ts_file = instance_dir / "restart_timestamps.txt"
    instance_id = instance_dir.name

    while True:
        # Re-load cfg on every restart (allows live config changes)
        load_cfg(instance_dir)
        instance_id = os.environ.get("IGOR_INSTANCE_ID", instance_dir.name)
        web_port = os.environ.get("IGOR_WEB_PORT", "8080")
        debug_flag = instance_dir / "debug_session.flag"

        # Crash loop detection
        now = int(time.time())
        cutoff = now - _RESTART_WINDOW_SECS
        timestamps: list[int] = []
        if restart_ts_file.exists():
            for line in restart_ts_file.read_text().splitlines():
                try:
                    ts = int(line.strip())
                    if ts >= cutoff:
                        timestamps.append(ts)
                except ValueError:
                    pass
        timestamps.append(now)
        restart_ts_file.write_text("\n".join(str(t) for t in timestamps) + "\n")

        if len(timestamps) >= _MAX_RESTARTS_PER_MINUTE:
            alerts = _RUNTIME_ROOT / "alerts.txt"
            msg = (
                f"CRITICAL: Igor crash loop — {len(timestamps)} restarts in "
                f"{_RESTART_WINDOW_SECS}s. Halting. Check {alerts}."
            )
            log.critical(msg)
            with alerts.open("a") as f:
                f.write("━" * 66 + "\n")
                f.write(
                    f"CRITICAL: Igor crash loop — {len(timestamps)} restarts in 60s\n"
                )
                f.write(
                    f"Time: {datetime.now(timezone.utc).isoformat()}\n"
                    f"Instance: {instance_id}\n"
                    "Halting restart loop. Manual intervention required.\n\n"
                )
            sys.exit(1)

        # pause.wait
        pause = _REPO_ROOT / "pause.wait"
        if pause.exists():
            print(f"[igor] Waiting for {pause} to clear.")
            while pause.exists():
                time.sleep(1)

        # Kill stale processes
        _kill_stale_processes(web_port)

        # Launch igor.main
        cmd = [sys.executable, "-m", "igor.main"] + igor_args
        crash_log_lines: list[str] = []

        launch_env = os.environ.copy()
        _existing_pp = launch_env.get("PYTHONPATH", "")
        launch_env["PYTHONPATH"] = str(_REPO_ROOT) + (
            ":" + _existing_pp if _existing_pp else ""
        )
        proc = subprocess.Popen(
            cmd,
            cwd=str(_WILD_DIR),
            env=launch_env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,  # merge stderr into stdout
            text=True,
        )

        # Stream output live while collecting for crash diagnosis
        assert proc.stdout is not None
        for line in proc.stdout:
            sys.stderr.write(line)
            crash_log_lines.append(line)
        proc.wait()
        exit_code = proc.returncode

        if exit_code == 42:
            print("[igor] Restarting (re-reading cfg)...")
            continue

        if exit_code in (0, 130, 143):
            # Clean exit: 0=quit, 130=SIGINT (Ctrl-C), 143=SIGTERM
            break

        # Unexpected crash
        traceback_tail = "".join(crash_log_lines[-80:])
        _log_crash(instance_dir, exit_code, traceback_tail, instance_id)

        if debug_flag.exists():
            print("[igor] Debug session active — not launching auto-fixer. Exiting.")
            break

        print(
            f"[igor] Crash detected (exit {exit_code}). Launching Claude auto-fixer..."
        )
        _run_auto_fixer(traceback_tail, exit_code)
        print("[igor] Auto-fixer exited. Restarting Igor...")


def _run_auto_fixer(traceback_tail: str, exit_code: int) -> None:
    """Call claude --dangerously-skip-permissions with crash diagnosis prompt."""
    prompt = (
        f"Igor crashed with exit code {exit_code}.\n\n"
        f"Traceback (last 80 lines of stderr):\n{traceback_tail}\n\n"
        "Task: diagnose the root cause, fix the code in ~/TheIgors/wild_igor/, "
        "run tests (cd ~/TheIgors && source venv/bin/activate && "
        "python -m pytest tests/ -x -q), commit the fix, then exit cleanly. "
        "Do not restart Igor — the startup script will restart it after you exit."
    )
    try:
        subprocess.run(
            ["claude", "--dangerously-skip-permissions", "-p", prompt],
            check=False,
        )
    except FileNotFoundError:
        log.error("auto-fixer: 'claude' not found in PATH — skipping")


# ── Entry point ───────────────────────────────────────────────────────────────


def _locate_instance_dir(instance_id: str) -> Path:
    """Return RUNTIME_ROOT / INSTANCE_ID, falling back to first .env found."""
    candidate = _RUNTIME_ROOT / instance_id
    if candidate.exists():
        return candidate

    # First-start: look for any existing instance dir
    for p in _RUNTIME_ROOT.iterdir():
        if (p / ".env").exists() or (p / "igor.cfg").exists():
            log.info(f"Using existing instance dir: {p}")
            return p

    # New instance — create dir
    candidate.mkdir(parents=True, exist_ok=True)
    return candidate


def main(argv: list[str] | None = None) -> None:
    logging.basicConfig(
        format="[installer] %(levelname)s %(message)s",
        level=logging.INFO,
        stream=sys.stderr,
    )

    parser = argparse.ArgumentParser(
        description="Igor unified entry point (D321)",
        add_help=True,
    )
    parser.add_argument(
        "--id",
        default=os.environ.get("IGOR_INSTANCE_ID", "Igor-wild-0001"),
        metavar="INSTANCE_ID",
        help="Igor instance ID (default: IGOR_INSTANCE_ID env or Igor-wild-0001)",
    )
    parser.add_argument(
        "--uninstall-cc",
        action="store_true",
        help="Remove Claude Code skill symlinks and MCP config installed by migration 003",
    )
    # Pass-through args to igor.main
    args, igor_args = parser.parse_known_args(argv)

    if args.uninstall_cc:
        uninstall_cc()
        return

    instance_dir = _locate_instance_dir(args.id)
    log.info(f"Instance: {args.id} at {instance_dir}")

    # Migrations
    run_migrations(instance_dir)

    # Build igor.main args
    if "--id" not in igor_args:
        igor_args = ["--id", args.id] + igor_args

    # Restart loop
    restart_loop(instance_dir, igor_args)


if __name__ == "__main__":
    main()
