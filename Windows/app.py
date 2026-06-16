#!/usr/bin/env python3
"""Small desktop app that blocks selected SNS domains for a fixed time."""

from __future__ import annotations

import json
import os
import re
import shlex
import subprocess
import sys
import tempfile
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from tkinter import messagebox
import tkinter as tk
from tkinter import ttk


APP_NAME = "SNS Access Blocker"
MARKER_START = "# SNS_ACCESS_BLOCKER_START"
MARKER_END = "# SNS_ACCESS_BLOCKER_END"
STATE_FILE = Path.home() / ".sns_access_blocker_state.json"
if sys.platform == "win32":
    HOSTS_PATH = (
        Path(os.environ.get("SystemRoot", r"C:\Windows"))
        / "System32"
        / "drivers"
        / "etc"
        / "hosts"
    )
else:
    HOSTS_PATH = Path("/etc/hosts")

DOMAIN_RE = re.compile(
    r"^(?=.{1,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z0-9][a-z0-9-]{1,62}$"
)

PRESETS: dict[str, list[str]] = {
    "X / Twitter": [
        "x.com",
        "www.x.com",
        "twitter.com",
        "www.twitter.com",
        "mobile.twitter.com",
        "api.twitter.com",
        "pbs.twimg.com",
        "video.twimg.com",
        "abs.twimg.com",
        "tweetdeck.twitter.com",
    ],
    "Instagram": [
        "instagram.com",
        "www.instagram.com",
        "i.instagram.com",
        "graph.instagram.com",
        "cdninstagram.com",
        "www.cdninstagram.com",
    ],
    "TikTok": [
        "tiktok.com",
        "www.tiktok.com",
        "m.tiktok.com",
        "vm.tiktok.com",
        "tiktokcdn.com",
        "www.tiktokcdn.com",
    ],
    "Facebook": [
        "facebook.com",
        "www.facebook.com",
        "m.facebook.com",
        "fb.com",
        "www.fb.com",
        "messenger.com",
        "www.messenger.com",
    ],
    "YouTube": [
        "youtube.com",
        "www.youtube.com",
        "m.youtube.com",
        "youtu.be",
        "youtube-nocookie.com",
        "www.youtube-nocookie.com",
        "googlevideo.com",
        "www.googlevideo.com",
        "ytimg.com",
        "www.ytimg.com",
    ],
    "Reddit": [
        "reddit.com",
        "www.reddit.com",
        "old.reddit.com",
        "new.reddit.com",
        "redd.it",
        "www.redd.it",
    ],
}


def now_local() -> datetime:
    return datetime.now().astimezone()


def parse_iso_datetime(value: str) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.astimezone()
    return parsed


def normalize_domain(raw: str) -> str | None:
    value = raw.strip().lower()
    if not value:
        return None
    if "://" in value:
        value = value.split("://", 1)[1]
    value = value.split("/", 1)[0].split("?", 1)[0].split("#", 1)[0]
    value = value.split("@")[-1].split(":", 1)[0]
    value = value.strip(".")
    if DOMAIN_RE.fullmatch(value):
        return value
    return None


def unique_domains(domains: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for domain in domains:
        normalized = normalize_domain(domain)
        if normalized and normalized not in seen:
            seen.add(normalized)
            result.append(normalized)
    return result


def read_hosts_block() -> dict[str, object] | None:
    try:
        lines = HOSTS_PATH.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return None

    inside = False
    domains: list[str] = []
    expires_at: datetime | None = None
    block_id = ""

    for line in lines:
        stripped = line.strip()
        if stripped == MARKER_START:
            inside = True
            continue
        if stripped == MARKER_END:
            break
        if not inside:
            continue

        if stripped.startswith("# expires_at="):
            expires_at = parse_iso_datetime(stripped.split("=", 1)[1])
            continue
        if stripped.startswith("# block_id="):
            block_id = stripped.split("=", 1)[1]
            continue
        if stripped.startswith("#") or not stripped:
            continue

        parts = stripped.split()
        if len(parts) >= 2:
            domains.append(parts[1])

    domains = unique_domains(domains)
    if not domains and expires_at is None:
        return None
    return {"domains": domains, "expires_at": expires_at, "block_id": block_id}


def applescript_string(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def powershell_string(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def run_admin_macos_shell(script_body: str) -> str:
    fd, path = tempfile.mkstemp(prefix="sns-access-blocker-", suffix=".sh")
    script_path = Path(path)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(script_body)
        script_path.chmod(0o700)

        command = f"/bin/bash {shlex.quote(str(script_path))}"
        apple_script = (
            "do shell script "
            + applescript_string(command)
            + " with administrator privileges"
        )
        completed = subprocess.run(
            ["/usr/bin/osascript", "-e", apple_script],
            text=True,
            capture_output=True,
            check=False,
        )
        if completed.returncode != 0:
            detail = completed.stderr.strip() or completed.stdout.strip() or "admin command failed"
            raise RuntimeError(detail)
        return completed.stdout.strip()
    finally:
        try:
            script_path.unlink()
        except OSError:
            pass


def windows_powershell_exe() -> str:
    system_root = Path(os.environ.get("SystemRoot", r"C:\Windows"))
    candidates = [
        system_root / "Sysnative" / "WindowsPowerShell" / "v1.0" / "powershell.exe",
        system_root / "System32" / "WindowsPowerShell" / "v1.0" / "powershell.exe",
    ]
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    return "powershell.exe"


def run_admin_windows_powershell(script_body: str) -> str:
    fd, path = tempfile.mkstemp(prefix="sns-access-blocker-", suffix=".ps1")
    script_path = Path(path)
    powershell = windows_powershell_exe()
    try:
        with os.fdopen(fd, "w", encoding="utf-8-sig") as handle:
            handle.write(script_body)

        command = (
            "$ErrorActionPreference = 'Stop'; "
            f"$p = Start-Process -FilePath {powershell_string(powershell)} "
            "-ArgumentList @("
            "'-NoProfile',"
            "'-ExecutionPolicy',"
            "'Bypass',"
            "'-File',"
            f"{powershell_string(str(script_path))}"
            ") -Verb RunAs -Wait -PassThru; "
            "exit $p.ExitCode"
        )
        completed = subprocess.run(
            [powershell, "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command],
            text=True,
            capture_output=True,
            check=False,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        if completed.returncode != 0:
            detail = completed.stderr.strip() or completed.stdout.strip() or "admin command failed"
            raise RuntimeError(detail)
        return completed.stdout.strip()
    finally:
        try:
            script_path.unlink()
        except OSError:
            pass


def macos_helper_script(
    *,
    action: str,
    domains: list[str] | None = None,
    duration_seconds: int = 0,
    expires_at: str = "",
    block_id: str = "",
) -> str:
    domain_array = " ".join(shlex.quote(domain) for domain in (domains or []))
    return f"""#!/bin/bash
set -euo pipefail

MARKER_START={shlex.quote(MARKER_START)}
MARKER_END={shlex.quote(MARKER_END)}
ACTION={shlex.quote(action)}
EXPIRES_AT={shlex.quote(expires_at)}
BLOCK_ID={shlex.quote(block_id)}
DURATION_SECONDS={int(duration_seconds)}
DOMAINS=({domain_array})

remove_block() {{
  local tmp
  tmp="$(/usr/bin/mktemp /tmp/sns-access-blocker-hosts.XXXXXX)"
  /usr/bin/awk -v start="$MARKER_START" -v end="$MARKER_END" '
    $0 == start {{ skip = 1; next }}
    $0 == end {{ skip = 0; next }}
    skip != 1 {{ print }}
  ' /etc/hosts > "$tmp"
  /bin/cat "$tmp" > /etc/hosts
  /bin/rm -f "$tmp"
}}

current_block_id() {{
  /usr/bin/awk -v start="$MARKER_START" -v end="$MARKER_END" '
    $0 == start {{ inside = 1; next }}
    $0 == end {{ inside = 0 }}
    inside == 1 && $0 ~ /^# block_id=/ {{
      sub(/^# block_id=/, "")
      print
      exit
    }}
  ' /etc/hosts
}}

remove_block_if_current() {{
  local current
  current="$(current_block_id || true)"
  if [ "$current" = "$BLOCK_ID" ]; then
    remove_block
  fi
}}

flush_dns() {{
  /usr/bin/dscacheutil -flushcache >/dev/null 2>&1 || true
  /usr/bin/killall -HUP mDNSResponder >/dev/null 2>&1 || true
}}

if [ "$ACTION" = "block" ]; then
  remove_block
  {{
    /bin/echo ""
    /bin/echo "$MARKER_START"
    /bin/echo "# managed_by={APP_NAME}"
    /bin/echo "# expires_at=$EXPIRES_AT"
    /bin/echo "# block_id=$BLOCK_ID"
    for domain in "${{DOMAINS[@]}}"; do
      /bin/echo "0.0.0.0 $domain"
      /bin/echo "::1 $domain"
    done
    /bin/echo "$MARKER_END"
  }} >> /etc/hosts
  flush_dns
  (
    trap '' HUP
    /bin/sleep "$DURATION_SECONDS"
    remove_block_if_current
    flush_dns
  ) </dev/null >/dev/null 2>&1 &
  echo "blocked"
elif [ "$ACTION" = "unblock" ]; then
  remove_block
  flush_dns
  echo "unblocked"
else
  echo "unknown action: $ACTION" >&2
  exit 2
fi
"""


def windows_helper_script(
    *,
    action: str,
    domains: list[str] | None = None,
    duration_seconds: int = 0,
    expires_at: str = "",
    block_id: str = "",
) -> str:
    del duration_seconds
    domain_array = "@(" + ", ".join(powershell_string(domain) for domain in (domains or [])) + ")"
    template = r"""
$ErrorActionPreference = "Stop"

$MarkerStart = __MARKER_START__
$MarkerEnd = __MARKER_END__
$ActionName = __ACTION__
$ExpiresAt = __EXPIRES_AT__
$BlockId = __BLOCK_ID__
$Domains = __DOMAINS__
$HostsPath = Join-Path $env:SystemRoot "System32\drivers\etc\hosts"
$DataDir = Join-Path $env:ProgramData "SNSAccessBlocker"
$TaskPrefix = "SNSAccessBlocker-Unblock-"
$Utf8NoBom = New-Object System.Text.UTF8Encoding($false)

function Write-HostsLines {
    param([string[]]$Lines)
    [System.IO.File]::WriteAllLines($HostsPath, $Lines, $Utf8NoBom)
}

function Remove-Block {
    if (-not (Test-Path -LiteralPath $HostsPath)) {
        throw "hosts file not found: $HostsPath"
    }
    $Output = New-Object System.Collections.Generic.List[string]
    $Skip = $false
    foreach ($Line in [System.IO.File]::ReadAllLines($HostsPath)) {
        $Trimmed = $Line.Trim()
        if ($Trimmed -eq $MarkerStart) {
            $Skip = $true
            continue
        }
        if ($Trimmed -eq $MarkerEnd) {
            $Skip = $false
            continue
        }
        if (-not $Skip) {
            [void]$Output.Add($Line)
        }
    }
    Write-HostsLines -Lines ([string[]]$Output)
}

function Flush-Dns {
    & ipconfig /flushdns | Out-Null
}

function Unregister-ExistingTasks {
    Get-ScheduledTask -TaskName "$TaskPrefix*" -ErrorAction SilentlyContinue |
        ForEach-Object {
            Unregister-ScheduledTask -TaskName $_.TaskName -Confirm:$false -ErrorAction SilentlyContinue
        }
}

function Remove-OldScripts {
    if (Test-Path -LiteralPath $DataDir) {
        Get-ChildItem -LiteralPath $DataDir -Filter "unblock-*.ps1" -ErrorAction SilentlyContinue |
            Remove-Item -Force -ErrorAction SilentlyContinue
    }
}

function Add-Block {
    Remove-Block
    Unregister-ExistingTasks
    Remove-OldScripts

    $Current = [System.IO.File]::ReadAllLines($HostsPath)
    $Next = New-Object System.Collections.Generic.List[string]
    $Next.AddRange([string[]]$Current)
    [void]$Next.Add("")
    [void]$Next.Add($MarkerStart)
    [void]$Next.Add("# managed_by=__APP_NAME__")
    [void]$Next.Add("# expires_at=$ExpiresAt")
    [void]$Next.Add("# block_id=$BlockId")
    foreach ($Domain in $Domains) {
        [void]$Next.Add("0.0.0.0 $Domain")
        [void]$Next.Add("::1 $Domain")
    }
    [void]$Next.Add($MarkerEnd)
    Write-HostsLines -Lines ([string[]]$Next)
}

function Install-UnblockTask {
    New-Item -ItemType Directory -Path $DataDir -Force | Out-Null
    $TaskName = "$TaskPrefix$BlockId"
    $UnblockScript = Join-Path $DataDir "unblock-$BlockId.ps1"
    $UnblockScriptBody = @'
param(
    [string]$ExpectedBlockId,
    [string]$TaskName
)

$ErrorActionPreference = "Stop"
$MarkerStart = __MARKER_START__
$MarkerEnd = __MARKER_END__
$HostsPath = Join-Path $env:SystemRoot "System32\drivers\etc\hosts"
$Utf8NoBom = New-Object System.Text.UTF8Encoding($false)

function Write-HostsLines {
    param([string[]]$Lines)
    [System.IO.File]::WriteAllLines($HostsPath, $Lines, $Utf8NoBom)
}

function Get-CurrentBlockId {
    if (-not (Test-Path -LiteralPath $HostsPath)) {
        return ""
    }
    $Inside = $false
    foreach ($Line in [System.IO.File]::ReadAllLines($HostsPath)) {
        $Trimmed = $Line.Trim()
        if ($Trimmed -eq $MarkerStart) {
            $Inside = $true
            continue
        }
        if ($Trimmed -eq $MarkerEnd) {
            $Inside = $false
            continue
        }
        if ($Inside -and $Trimmed.StartsWith("# block_id=")) {
            return $Trimmed.Substring(11)
        }
    }
    return ""
}

function Remove-Block {
    if (-not (Test-Path -LiteralPath $HostsPath)) {
        return
    }
    $Output = New-Object System.Collections.Generic.List[string]
    $Skip = $false
    foreach ($Line in [System.IO.File]::ReadAllLines($HostsPath)) {
        $Trimmed = $Line.Trim()
        if ($Trimmed -eq $MarkerStart) {
            $Skip = $true
            continue
        }
        if ($Trimmed -eq $MarkerEnd) {
            $Skip = $false
            continue
        }
        if (-not $Skip) {
            [void]$Output.Add($Line)
        }
    }
    Write-HostsLines -Lines ([string[]]$Output)
}

try {
    if ((Get-CurrentBlockId) -eq $ExpectedBlockId) {
        Remove-Block
        & ipconfig /flushdns | Out-Null
    }
}
finally {
    if ($TaskName) {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
    }
    if ($PSCommandPath) {
        Remove-Item -LiteralPath $PSCommandPath -Force -ErrorAction SilentlyContinue
    }
}
'@
    Set-Content -LiteralPath $UnblockScript -Value $UnblockScriptBody -Encoding UTF8

    $RunAt = [DateTimeOffset]::Parse($ExpiresAt).LocalDateTime
    $MinimumRunAt = (Get-Date).AddSeconds(30)
    if ($RunAt -lt $MinimumRunAt) {
        $RunAt = $MinimumRunAt
    }

    $PowerShellPath = Join-Path $env:SystemRoot "System32\WindowsPowerShell\v1.0\powershell.exe"
    $TaskArgs = '-NoProfile -ExecutionPolicy Bypass -File "' + $UnblockScript + '" -ExpectedBlockId "' + $BlockId + '" -TaskName "' + $TaskName + '"'
    $TaskAction = New-ScheduledTaskAction -Execute $PowerShellPath -Argument $TaskArgs
    $TaskTrigger = New-ScheduledTaskTrigger -Once -At $RunAt
    $TaskPrincipal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -RunLevel Highest
    Register-ScheduledTask -TaskName $TaskName -Action $TaskAction -Trigger $TaskTrigger -Principal $TaskPrincipal -Force | Out-Null
}

if ($ActionName -eq "block") {
    Add-Block
    Install-UnblockTask
    Flush-Dns
    "blocked"
}
elseif ($ActionName -eq "unblock") {
    Remove-Block
    Unregister-ExistingTasks
    Remove-OldScripts
    Flush-Dns
    "unblocked"
}
else {
    throw "unknown action: $ActionName"
}
"""
    return (
        template.replace("__MARKER_START__", powershell_string(MARKER_START))
        .replace("__MARKER_END__", powershell_string(MARKER_END))
        .replace("__ACTION__", powershell_string(action))
        .replace("__EXPIRES_AT__", powershell_string(expires_at))
        .replace("__BLOCK_ID__", powershell_string(block_id))
        .replace("__DOMAINS__", domain_array)
        .replace("__APP_NAME__", APP_NAME)
    ).lstrip()


def block_domains(domains: list[str], duration_seconds: int, expires_at: str, block_id: str) -> None:
    if sys.platform == "darwin":
        run_admin_macos_shell(
            macos_helper_script(
                action="block",
                domains=domains,
                duration_seconds=duration_seconds,
                expires_at=expires_at,
                block_id=block_id,
            )
        )
        return
    if sys.platform == "win32":
        run_admin_windows_powershell(
            windows_helper_script(
                action="block",
                domains=domains,
                duration_seconds=duration_seconds,
                expires_at=expires_at,
                block_id=block_id,
            )
        )
        return
    raise RuntimeError("This app currently supports macOS and Windows only.")


def unblock_domains() -> None:
    if sys.platform == "darwin":
        run_admin_macos_shell(macos_helper_script(action="unblock"))
        return
    if sys.platform == "win32":
        run_admin_windows_powershell(windows_helper_script(action="unblock"))
        return
    raise RuntimeError("This app currently supports macOS and Windows only.")


def save_state(data: dict[str, object]) -> None:
    STATE_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def remove_state() -> None:
    try:
        STATE_FILE.unlink()
    except FileNotFoundError:
        pass


def format_remaining(expires_at: datetime | None) -> str:
    if expires_at is None:
        return "--:--:--"
    seconds = max(0, int((expires_at - now_local()).total_seconds()))
    hours, rem = divmod(seconds, 3600)
    minutes, seconds = divmod(rem, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


class SNSBlockerApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title(APP_NAME)
        self.root.minsize(580, 620)

        self.site_vars: dict[str, tk.BooleanVar] = {}
        self.duration_var = tk.StringVar(value="60")
        self.status_var = tk.StringVar(value="確認中")
        self.remaining_var = tk.StringVar(value="")
        self.blocked_domains_var = tk.StringVar(value="")
        self.busy = False

        self._build_ui()
        self.refresh_status()
        self.root.after(1000, self._tick)

    def _build_ui(self) -> None:
        style = ttk.Style()
        if "clam" in style.theme_names():
            style.theme_use("clam")
        style.configure("Title.TLabel", font=("Helvetica", 18, "bold"))
        style.configure("Status.TLabel", font=("Helvetica", 13, "bold"))

        main = ttk.Frame(self.root, padding=18)
        main.grid(row=0, column=0, sticky="nsew")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main.columnconfigure(0, weight=1)

        ttk.Label(main, text=APP_NAME, style="Title.TLabel").grid(row=0, column=0, sticky="w")

        target_frame = ttk.LabelFrame(main, text="ブロック対象", padding=12)
        target_frame.grid(row=1, column=0, sticky="ew", pady=(16, 10))
        target_frame.columnconfigure(0, weight=1)
        target_frame.columnconfigure(1, weight=1)

        for index, name in enumerate(PRESETS):
            var = tk.BooleanVar(value=name == "X / Twitter")
            self.site_vars[name] = var
            ttk.Checkbutton(target_frame, text=name, variable=var).grid(
                row=index // 2,
                column=index % 2,
                sticky="w",
                padx=(0, 18),
                pady=4,
            )

        custom_frame = ttk.LabelFrame(main, text="追加ドメイン", padding=12)
        custom_frame.grid(row=2, column=0, sticky="ew", pady=10)
        custom_frame.columnconfigure(0, weight=1)
        self.custom_text = tk.Text(custom_frame, height=4, wrap="word", undo=True)
        self.custom_text.grid(row=0, column=0, sticky="ew")

        duration_frame = ttk.LabelFrame(main, text="時間", padding=12)
        duration_frame.grid(row=3, column=0, sticky="ew", pady=10)
        duration_frame.columnconfigure(2, weight=1)
        tk.Spinbox(
            duration_frame,
            from_=1,
            to=1440,
            increment=5,
            width=7,
            textvariable=self.duration_var,
        ).grid(row=0, column=0, sticky="w")
        ttk.Label(duration_frame, text="分").grid(row=0, column=1, sticky="w", padx=(8, 0))

        button_frame = ttk.Frame(main)
        button_frame.grid(row=4, column=0, sticky="ew", pady=(12, 8))
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)

        self.start_button = ttk.Button(
            button_frame,
            text="ブロック開始",
            command=self.start_block,
        )
        self.start_button.grid(row=0, column=0, sticky="ew", padx=(0, 6), ipady=6)

        self.unlock_button = ttk.Button(
            button_frame,
            text="緊急解除",
            command=self.emergency_unlock,
        )
        self.unlock_button.grid(row=0, column=1, sticky="ew", padx=(6, 0), ipady=6)

        status_frame = ttk.LabelFrame(main, text="状態", padding=12)
        status_frame.grid(row=5, column=0, sticky="nsew", pady=(10, 0))
        status_frame.columnconfigure(0, weight=1)
        main.rowconfigure(5, weight=1)

        ttk.Label(status_frame, textvariable=self.status_var, style="Status.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(status_frame, textvariable=self.remaining_var).grid(
            row=1, column=0, sticky="w", pady=(8, 0)
        )
        ttk.Label(
            status_frame,
            textvariable=self.blocked_domains_var,
            wraplength=520,
            justify="left",
        ).grid(row=2, column=0, sticky="ew", pady=(8, 0))

    def collect_domains(self) -> list[str]:
        domains: list[str] = []
        for name, var in self.site_vars.items():
            if var.get():
                domains.extend(PRESETS[name])

        custom = self.custom_text.get("1.0", "end") if self.custom_text else ""
        custom_parts = re.split(r"[\s,;]+", custom)
        domains.extend(custom_parts)
        return unique_domains(domains)

    def duration_seconds(self) -> int:
        try:
            minutes = int(self.duration_var.get())
        except ValueError as exc:
            raise ValueError("時間は分単位の数字で入力してください。") from exc
        if minutes < 1 or minutes > 1440:
            raise ValueError("時間は1分から1440分の範囲で指定してください。")
        return minutes * 60

    def set_busy(self, busy: bool) -> None:
        self.busy = busy
        state = "disabled" if busy else "normal"
        self.start_button.configure(state=state)
        self.unlock_button.configure(state=state)

    def start_block(self) -> None:
        if self.busy:
            return
        try:
            domains = self.collect_domains()
            if not domains:
                messagebox.showerror(APP_NAME, "ブロック対象を1つ以上選択してください。")
                return
            duration = self.duration_seconds()
        except ValueError as exc:
            messagebox.showerror(APP_NAME, str(exc))
            return

        expires_at_dt = now_local() + timedelta(seconds=duration)
        expires_at = expires_at_dt.isoformat(timespec="seconds")
        preview = ", ".join(domains[:8])
        if len(domains) > 8:
            preview += f" ほか{len(domains) - 8}件"

        confirmed = messagebox.askokcancel(
            APP_NAME,
            f"{duration // 60}分間ブロックします。\n\n{preview}",
        )
        if not confirmed:
            return

        block_id = uuid.uuid4().hex
        self.set_busy(True)
        self.status_var.set("管理者認証を待っています")
        self.root.update_idletasks()

        try:
            block_domains(domains, duration, expires_at, block_id)
            save_state(
                {
                    "domains": domains,
                    "expires_at": expires_at,
                    "block_id": block_id,
                    "created_at": now_local().isoformat(timespec="seconds"),
                }
            )
            self.status_var.set("ブロック中")
        except Exception as exc:
            messagebox.showerror(APP_NAME, f"ブロックに失敗しました。\n\n{exc}")
        finally:
            self.set_busy(False)
            self.refresh_status()

    def emergency_unlock(self) -> None:
        if self.busy:
            return
        current = read_hosts_block()
        if not current:
            remove_state()
            self.refresh_status()
            messagebox.showinfo(APP_NAME, "現在のブロックはありません。")
            return

        confirmed = messagebox.askyesno(APP_NAME, "現在のブロックを解除しますか？")
        if not confirmed:
            return

        self.set_busy(True)
        self.status_var.set("解除中")
        self.root.update_idletasks()
        try:
            unblock_domains()
            remove_state()
        except Exception as exc:
            messagebox.showerror(APP_NAME, f"解除に失敗しました。\n\n{exc}")
        finally:
            self.set_busy(False)
            self.refresh_status()

    def refresh_status(self) -> None:
        current = read_hosts_block()
        if not current:
            self.status_var.set("ブロックなし")
            self.remaining_var.set("")
            self.blocked_domains_var.set("")
            remove_state()
            return

        expires_at = current.get("expires_at")
        domains = current.get("domains") or []
        if isinstance(expires_at, datetime) and expires_at <= now_local():
            self.status_var.set("期限切れのブロックが残っています")
            self.remaining_var.set("残り 00:00:00")
        else:
            self.status_var.set("ブロック中")
            self.remaining_var.set(f"残り {format_remaining(expires_at if isinstance(expires_at, datetime) else None)}")

        joined = ", ".join(str(domain) for domain in domains)
        self.blocked_domains_var.set(joined)

    def _tick(self) -> None:
        self.refresh_status()
        self.root.after(1000, self._tick)


def self_test() -> int:
    assert normalize_domain("https://x.com/home") == "x.com"
    assert normalize_domain("www.twitter.com") == "www.twitter.com"
    assert normalize_domain("not a domain") is None
    domains = unique_domains(["x.com", "https://x.com/a", "twitter.com"])
    assert domains == ["x.com", "twitter.com"]

    macos_info = macos_helper_script(
        action="block",
        domains=["x.com", "twitter.com"],
        duration_seconds=60,
        expires_at=now_local().isoformat(timespec="seconds"),
        block_id="test",
    )
    assert "DOMAINS=(x.com twitter.com)" in macos_info
    fd, path = tempfile.mkstemp(prefix="sns-access-blocker-test-", suffix=".sh")
    script_path = Path(path)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(macos_info)
        if os.name != "nt":
        subprocess.run(["/bin/bash", "-n", str(script_path)], check=True)
    finally:
        try:
            script_path.unlink()
        except OSError:
            pass

    windows_info = windows_helper_script(
        action="block",
        domains=["x.com", "twitter.com"],
        duration_seconds=60,
        expires_at=now_local().isoformat(timespec="seconds"),
        block_id="test",
    )
    assert "$Domains = @('x.com', 'twitter.com')" in windows_info
    assert "Register-ScheduledTask" in windows_info
    assert "System32\\drivers\\etc\\hosts" in windows_info
    print("self-test ok")
    return 0


def main() -> int:
    if "--self-test" in sys.argv:
        return self_test()
    if sys.platform not in {"darwin", "win32"}:
        print("This app currently supports macOS and Windows only.", file=sys.stderr)
        return 2

    root = tk.Tk()
    SNSBlockerApp(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
