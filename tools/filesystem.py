from pathlib import Path
import shutil

from config import ASTRAL_D_ROOT, ASTRAL_USER_ROOT, WORKSPACE_ROOT


def _allowed_roots():
    roots = [WORKSPACE_ROOT]
    for root in (ASTRAL_USER_ROOT, ASTRAL_D_ROOT):
        if root not in roots:
            roots.append(root)
    return tuple(roots)


def _display_path(target: Path) -> str:
    try:
        return str(target.relative_to(WORKSPACE_ROOT))
    except ValueError:
        return str(target)


def list_allowed_directory() -> dict:
    """Describe the filesystem roots available to Astral's file tools."""
    labels = {
        WORKSPACE_ROOT: "workspace",
        ASTRAL_USER_ROOT: "user_profile",
        ASTRAL_D_ROOT: "drive_d",
    }
    return {
        "success": True,
        "directories": [
            {
                "name": labels.get(root, "allowed_root"),
                "path": str(root),
                "read": True,
                "write": True,
                "write_requires_confirmation": True,
            }
            for root in _allowed_roots()
        ],
    }

def _safe_path(path: str) -> Path:
    """
    Mengubah path menjadi absolute path
    dan memastikan path tetap berada di workspace.
    """

    requested = Path(path)
    target = (requested if requested.is_absolute() else WORKSPACE_ROOT / requested).resolve()

    if not any(target == root or root in target.parents for root in _allowed_roots()):
        raise PermissionError(
            "Akses ditolak. Path berada di luar root filesystem Astral."
        )

    return target


def list_directory(path: str = ".") -> dict:
    """
    Menampilkan isi directory.
    """

    target = _safe_path(path)

    if not target.exists():
        return {
            "success": False,
            "error": f"Directory tidak ditemukan: {path}"
        }

    if not target.is_dir():
        return {
            "success": False,
            "error": f"Bukan directory: {path}"
        }

    items = []

    for item in sorted(
        target.iterdir(),
        key=lambda x: (not x.is_dir(), x.name.lower())
    ):
        items.append({
            "name": item.name,
            "type": "directory" if item.is_dir() else "file"
        })

    return {
        "success": True,
        "path": _display_path(target),
        "items": items
    }


def read_file(path: str) -> dict:
    """
    Membaca isi file teks.
    """

    target = _safe_path(path)

    if not target.exists():
        return {
            "success": False,
            "error": f"File tidak ditemukan: {path}"
        }

    if not target.is_file():
        return {
            "success": False,
            "error": f"Bukan file: {path}"
        }

    try:
        content = target.read_text(
            encoding="utf-8"
        )

        return {
            "success": True,
            "path": _display_path(target),
            "content": content
        }

    except UnicodeDecodeError:
        return {
            "success": False,
            "error": "File bukan file teks UTF-8."
        }


def write_file(
    path: str,
    content: str
) -> dict:
    """
    Membuat atau menimpa file.
    """

    target = _safe_path(path)

    target.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    target.write_text(
        content,
        encoding="utf-8"
    )

    return {
        "success": True,
        "path": _display_path(target),
        "message": "File berhasil ditulis."
    }


def create_directory(path: str) -> dict:
    """
    Membuat directory.
    """

    target = _safe_path(path)

    target.mkdir(
        parents=True,
        exist_ok=True
    )

    return {
        "success": True,
        "path": _display_path(target),
        "message": "Directory berhasil dibuat."
    }


def delete_file(path: str) -> dict:
    """
    Menghapus file.
    """

    target = _safe_path(path)

    if not target.exists():
        return {
            "success": False,
            "error": f"File tidak ditemukan: {path}"
        }

    if not target.is_file():
        return {
            "success": False,
            "error": "Tool ini hanya bisa menghapus file."
        }

    target.unlink()

    return {
        "success": True,
        "path": _display_path(target),
        "message": "File berhasil dihapus."
    }


def move_file(
    source: str,
    destination: str
) -> dict:
    """
    Memindahkan atau rename file.
    """

    source_path = _safe_path(source)
    destination_path = _safe_path(destination)

    if not source_path.exists():
        return {
            "success": False,
            "error": f"Source tidak ditemukan: {source}"
        }

    destination_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    shutil.move(
        str(source_path),
        str(destination_path)
    )

    return {
        "success": True,
        "source": _display_path(source_path),
        "destination": _display_path(destination_path),
        "message": "File berhasil dipindahkan."
    }


__all__ = [
    "list_allowed_directory",
    "list_directory",
    "read_file",
    "write_file",
    "create_directory",
    "delete_file",
    "move_file"
]
