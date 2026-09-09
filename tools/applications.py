"""Windows desktop application controls for Astral."""
import csv
import json
import os
import subprocess
import time


# Closing an app invokes PowerShell/taskkill. Keep those console programs from
# attaching to Astral's terminal and changing its display state.
_HIDDEN_CONSOLE = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def _hidden_run_kwargs() -> dict:
    """Run a Windows helper without attaching it to Astral's console."""
    return {"creationflags": _HIDDEN_CONSOLE}


def _matching_processes(pid: int = None, process_name: str = None) -> list[dict]:
    """Return exact process matches, independent of tasklist display order."""
    completed = subprocess.run(
        ["tasklist", "/FO", "CSV", "/NH"], capture_output=True,
        text=True, encoding="utf-8", errors="replace", check=False,
        **_hidden_run_kwargs(),
    )
    if completed.returncode != 0:
        return []
    matches = []
    wanted_name = process_name.casefold() if process_name else None
    for row in csv.reader(completed.stdout.splitlines()):
        if len(row) < 2 or not row[1].isdigit():
            continue
        if pid is not None and int(row[1]) != pid:
            continue
        if wanted_name is not None and row[0].casefold() != wanted_name:
            continue
        matches.append({"name": row[0], "pid": int(row[1])})
    return matches


def list_applications(limit: int = 100, query: str = "") -> list[dict]:
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 500:
        raise ValueError("limit harus integer antara 1 dan 500.")
    if not isinstance(query, str):
        raise ValueError("query harus string.")
    completed = subprocess.run(
        ["tasklist", "/FO", "CSV", "/NH"], capture_output=True,
        text=True, encoding="utf-8", errors="replace", check=False,
        **_hidden_run_kwargs(),
    )
    if completed.returncode != 0:
        return [{"error": completed.stderr.strip() or "tasklist gagal."}]
    rows = []
    needle = query.casefold().strip()
    for row in csv.reader(completed.stdout.splitlines()):
        if len(row) >= 2:
            if needle and needle not in row[0].casefold():
                continue
            rows.append({"name": row[0], "pid": int(row[1]) if row[1].isdigit() else row[1], "memory": row[4] if len(row) > 4 else ""})
    return rows[:limit]


def list_launchable_applications(query: str = "", limit: int = 50) -> list[dict]:
    """List Start Menu applications that can be launched by display name."""
    completed = subprocess.run(
        ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command",
         "Get-StartApps | Select-Object Name,AppID | ConvertTo-Json -Compress"],
        capture_output=True, text=True, encoding="utf-8", errors="replace", check=False,
        **_hidden_run_kwargs(),
    )
    if completed.returncode != 0 or not completed.stdout.strip(): return []
    try: apps = json.loads(completed.stdout)
    except json.JSONDecodeError: return []
    if isinstance(apps, dict): apps = [apps]
    needle = query.casefold().strip()
    apps = [{"name": x.get("Name", ""), "app_id": x.get("AppID", "")} for x in apps]
    return [x for x in apps if not needle or needle in x["name"].casefold()][:limit]


def launch_application(application: str, arguments: list[str] = None) -> dict:
    if not isinstance(application, str) or not application.strip():
        raise ValueError("application harus berupa path executable yang tidak kosong.")
    if arguments is None: arguments = []
    if not isinstance(arguments, list) or any(not isinstance(arg, str) for arg in arguments):
        raise ValueError("arguments harus array string.")
    aliases = {"explorer": "explorer.exe", "file explorer": "explorer.exe"}
    resolved = aliases.get(application.strip().casefold(), application)
    try:
        process = subprocess.Popen(
            [resolved, *arguments],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=_HIDDEN_CONSOLE,
        )
        if resolved.casefold() == "explorer.exe":
            # Explorer forwards the request to the existing Windows shell and
            # exits its bootstrap process almost immediately.  That PID is not
            # the PID of the newly opened window, so never advertise it as a
            # valid close target to the model.
            return {
                "success": True,
                "pid": None,
                "application": application,
                "method": "explorer_shell",
                "close_target": "explorer.exe",
                "note": (
                    "File Explorer was opened by the Windows shell. To close "
                    "its open windows, call close_application with "
                    "process_name='explorer.exe'."
                ),
            }
        return {"success": True, "pid": process.pid, "application": application, "method": "executable"}
    except FileNotFoundError:
        matches = list_launchable_applications(application, limit=10)
        exact = next((x for x in matches if x["name"].casefold() == application.casefold()), None)
        if exact is None and len(matches) == 1: exact = matches[0]
        if exact is None:
            return {"success": False, "error": "Aplikasi tidak ditemukan. Gunakan list_launchable_applications untuk mencari nama tepat.", "matches": matches}
        # explorer shell:AppsFolder launches packaged/Start Menu apps such as WhatsApp.
        # ShellExecute opens the AppsFolder entry directly. Unlike spawning
        # explorer.exe, it does not attach an intermediate console process to
        # Astral's terminal (Spotify and other Store/UWP apps use this path).
        try:
            os.startfile(f"shell:AppsFolder\\{exact['app_id']}")
        except OSError as error:
            return {
                "success": False,
                "application": exact["name"],
                "error": f"Aplikasi Start Menu tidak dapat dibuka: {error}",
            }
        return {
            "success": True,
            "pid": None,
            "application": exact["name"],
            "method": "start_menu",
            "note": (
                "This Start Menu app is launched by the Windows shell, so its "
                "launcher PID is not a close target. Use list_applications to "
                "find its running executable and then close_application with "
                "that PID or process_name."
            ),
        }
    except OSError as error:
        return {"success": False, "application": application, "error": str(error)}


def close_application(pid: int = None, process_name: str = None) -> dict:
    if pid is None and (not isinstance(process_name, str) or not process_name.strip()):
        raise ValueError("pid atau process_name diperlukan.")
    if pid is not None and (isinstance(pid, bool) or not isinstance(pid, int) or pid <= 0):
        raise ValueError("pid harus integer positif.")
    if process_name is not None and (not isinstance(process_name, str) or any(x in process_name for x in "\\/")):
        raise ValueError("process_name harus nama executable, misalnya WhatsApp.Root.exe.")
    if process_name and process_name.strip().casefold() == "explorer.exe":
        # Do not use taskkill for Explorer: it terminates the Windows desktop
        # shell, which Windows can restart, while leaving the result ambiguous.
        # Shell.Application exposes File Explorer windows directly and Quit()
        # closes only those windows.
        command = (
            "$windows = @((New-Object -ComObject Shell.Application).Windows() | "
            "Where-Object { $_.FullName -and (Split-Path $_.FullName -Leaf) "
            "-ieq 'explorer.exe' }); "
            "$windows | ForEach-Object { $_.Quit() }; "
            "Write-Output $windows.Count"
        )
        completed = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", command],
            capture_output=True, text=True, encoding="utf-8", errors="replace", check=False,
            creationflags=_HIDDEN_CONSOLE,
        )
        if completed.returncode != 0:
            return {
                "success": False,
                "pid": None,
                "process_name": process_name,
                "message": completed.stderr.strip() or "Gagal menutup jendela File Explorer.",
            }
        try:
            closed_count = int(completed.stdout.strip().splitlines()[-1])
        except (IndexError, ValueError):
            closed_count = 0
        return {
            "success": closed_count > 0,
            "pid": None,
            "process_name": process_name,
            "closed_windows": closed_count,
            "message": (
                f"{closed_count} jendela File Explorer ditutup."
                if closed_count
                else "Tidak ada jendela File Explorer yang terbuka untuk ditutup."
            ),
        }
    target_name = process_name.strip() if process_name else None
    targets = _matching_processes(pid=pid, process_name=target_name)
    if not targets:
        return {
            "success": False,
            "pid": pid,
            "process_name": target_name,
            "message": "Proses target tidak ditemukan; tidak ada aplikasi yang ditutup.",
        }

    # Request a normal window close before force-killing anything. This lets
    # well-behaved apps save state or show their own confirmation dialog.
    graceful_pids = []
    for target in targets:
        close_window = (
            f"$process = Get-Process -Id {target['pid']} -ErrorAction SilentlyContinue; "
            "if ($process -and $process.MainWindowHandle -ne 0) { "
            "$process.CloseMainWindow() | Out-Null; Write-Output $process.Id }"
        )
        completed = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", close_window],
            capture_output=True, text=True, encoding="utf-8", errors="replace", check=False,
            creationflags=_HIDDEN_CONSOLE,
        )
        if completed.returncode == 0 and str(target["pid"]) in completed.stdout.split():
            graceful_pids.append(target["pid"])

    # Give a normal close a brief chance, then force only processes that are
    # still alive. The tool result records this escalation and verifies it.
    time.sleep(1)
    remaining = _matching_processes(pid=pid, process_name=target_name)
    forced_pids = []
    force_messages = []
    for target in remaining:
        completed = subprocess.run(
            ["taskkill", "/PID", str(target["pid"]), "/T", "/F"],
            capture_output=True, text=True, encoding="utf-8", errors="replace", check=False,
            creationflags=_HIDDEN_CONSOLE,
        )
        forced_pids.append(target["pid"])
        message = completed.stdout.strip() or completed.stderr.strip()
        if message:
            force_messages.append(message)

    remaining = _matching_processes(pid=pid, process_name=target_name)
    success = not remaining
    return {
        "success": success,
        "pid": pid,
        "process_name": target_name,
        "target_pids": [target["pid"] for target in targets],
        "graceful_close_requested": graceful_pids,
        "force_killed_pids": forced_pids,
        "remaining_pids": [target["pid"] for target in remaining],
        "message": (
            "Aplikasi ditutup dan prosesnya sudah diverifikasi berhenti."
            if success
            else "Sebagian proses masih berjalan; aplikasi belum sepenuhnya tertutup. "
            + " ".join(force_messages)
        ),
    }
