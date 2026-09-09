"""Eksekusi PowerShell terkonfirmasi untuk Astral."""

import subprocess

from config import SHELL_COMMAND_TIMEOUT_SECONDS, WORKSPACE_ROOT


# ``capture_output`` keeps command text out of Astral's transcript.  On
# Windows this flag also prevents PowerShell from allocating a second console
# window when a command is run from a console host such as Windows Terminal.
_HIDDEN_CONSOLE = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def _captured_text(value) -> str:
    """Normalize subprocess output for safe JSON tool results."""
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)


def run_shell_command(command: str, timeout_seconds: int = None) -> dict:
    """Jalankan satu perintah PowerShell dengan workspace sebagai cwd.

    Persetujuan pengguna dilakukan oleh Agent sebelum fungsi ini dipanggil.
    Perintah tetap dapat mengakses lokasi lain jika pengguna menyetujuinya;
    tool ini tidak mengklaim sandbox keamanan OS.
    """
    if not command or not command.strip():
        raise ValueError("Command tidak boleh kosong.")

    timeout = timeout_seconds or SHELL_COMMAND_TIMEOUT_SECONDS
    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)):
        raise ValueError("timeout_seconds harus berupa angka.")
    if not 1 <= timeout <= 300:
        raise ValueError("timeout_seconds harus berada antara 1 dan 300.")

    try:
        completed = subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-NonInteractive",
                "-Command",
                command,
            ],
            cwd=WORKSPACE_ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
            creationflags=_HIDDEN_CONSOLE,
        )
        return {
            "success": completed.returncode == 0,
            "exit_code": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
        }
    except subprocess.TimeoutExpired as error:
        return {
            "success": False,
            "error": f"Command timeout setelah {timeout} detik.",
            "stdout": _captured_text(error.stdout),
            "stderr": _captured_text(error.stderr),
        }
    except OSError as error:
        return {
            "success": False,
            "error": f"PowerShell tidak dapat dijalankan: {error}",
        }


__all__ = ["run_shell_command"]
