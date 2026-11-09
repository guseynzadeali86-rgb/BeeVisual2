"""BeeVisual launcher - core logic (no GUI).

Installs Minecraft 1.21.4 + Fabric, Fabric API, deploys the BeeVisual client jar
and builds the launch command. Everything lives in ~/.beevisual.
"""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import sys
import urllib.parse
import urllib.request
import uuid
from pathlib import Path
from typing import Callable

MC_VERSION = "1.21.4"
LAUNCHER_VERSION = "1.0.0"
BASE_DIR = Path.home() / ".beevisual"
MC_DIR = BASE_DIR / "minecraft"
MODS_DIR = MC_DIR / "mods"
LOG_DIR = BASE_DIR / "logs"
CONFIG_PATH = BASE_DIR / "config.json"
USER_AGENT = f"BeeVisualLauncher/{LAUNCHER_VERSION}"

DEFAULT_CONFIG = {
    "nickname": "Steve_Bee",
    "ram_gb": 4,
    "jvm_extra": "",
    "hide_while_playing": False,
}

LogFn = Callable[[str], None]


def bundle_dir() -> Path:
    """Folder with bundled assets (PyInstaller aware)."""
    return Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))


def app_root() -> Path:
    """Folder next to the exe / main.py (the 'mods' folder with our client jar lives here)."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


# ----------------------------------------------------------------- config
def valid_nickname(name: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z0-9_]{3,16}", name or ""))


def load_config() -> dict:
    cfg = dict(DEFAULT_CONFIG)
    try:
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            cfg.update({k: data[k] for k in DEFAULT_CONFIG if k in data})
    except (OSError, ValueError):
        pass
    if not valid_nickname(str(cfg["nickname"])):
        cfg["nickname"] = DEFAULT_CONFIG["nickname"]
    try:
        cfg["ram_gb"] = max(1, min(64, int(cfg["ram_gb"])))
    except (TypeError, ValueError):
        cfg["ram_gb"] = DEFAULT_CONFIG["ram_gb"]
    return cfg


def save_config(cfg: dict) -> None:
    try:
        BASE_DIR.mkdir(parents=True, exist_ok=True)
        CONFIG_PATH.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError:
        pass


# ----------------------------------------------------------------- helpers
def offline_uuid(name: str) -> str:
    """Same UUID Minecraft derives for offline players."""
    h = bytearray(hashlib.md5(("OfflinePlayer:" + name).encode("utf-8")).digest())
    h[6] = (h[6] & 0x0F) | 0x30
    h[8] = (h[8] & 0x3F) | 0x80
    return str(uuid.UUID(bytes=bytes(h)))


def _request(url: str):
    return urllib.request.Request(url, headers={"User-Agent": USER_AGENT})


def http_json(url: str):
    with urllib.request.urlopen(_request(url), timeout=25) as r:
        return json.loads(r.read().decode("utf-8"))


def download(url: str, dest: Path, sha1: str | None = None) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    part = dest.with_suffix(dest.suffix + ".part")
    h = hashlib.sha1()
    with urllib.request.urlopen(_request(url), timeout=60) as r, open(part, "wb") as f:
        while True:
            chunk = r.read(1 << 16)
            if not chunk:
                break
            h.update(chunk)
            f.write(chunk)
    if sha1 and h.hexdigest().lower() != sha1.lower():
        part.unlink(missing_ok=True)
        raise RuntimeError(f"Контрольная сумма файла {dest.name} не совпала")
    part.replace(dest)


# ----------------------------------------------------------------- mods
def ensure_fabric_api(log: LogFn) -> None:
    MODS_DIR.mkdir(parents=True, exist_ok=True)
    if any(MODS_DIR.glob("fabric-api-*.jar")):
        log("Fabric API уже установлен")
        return
    log("Скачиваю Fabric API…")
    q = urllib.parse.urlencode({"game_versions": json.dumps([MC_VERSION]), "loaders": json.dumps(["fabric"])})
    versions = http_json(f"https://api.modrinth.com/v2/project/fabric-api/version?{q}")
    if not versions:
        raise RuntimeError(f"Fabric API для {MC_VERSION} не найден на Modrinth")
    versions.sort(key=lambda v: (v.get("version_type") == "release", v.get("date_published", "")), reverse=True)
    files = versions[0]["files"]
    f = next((x for x in files if x.get("primary")), files[0])
    download(f["url"], MODS_DIR / f["filename"], f.get("hashes", {}).get("sha1"))
    log(f"Установлен {f['filename']}")


def find_client_jar() -> Path | None:
    """Client jar: first next to the exe (mods/), then the one bundled inside the exe."""
    for src in (app_root() / "mods", bundle_dir() / "mods"):
        if not src.is_dir():
            continue
        jars = sorted(j for j in src.glob("beevisual-*.jar") if not j.name.endswith(("-sources.jar", "-dev.jar")))
        if jars:
            return jars[-1]
    return None


def install_client_mod(log: LogFn) -> bool:
    jar = find_client_jar()
    if jar is None:
        log("Клиент BeeVisual (beevisual-*.jar) не найден в папке mods рядом с лаунчером - запускаю чистый Fabric")
        return False
    MODS_DIR.mkdir(parents=True, exist_ok=True)
    for old in MODS_DIR.glob("beevisual-*.jar"):
        old.unlink(missing_ok=True)
    shutil.copy2(jar, MODS_DIR / jar.name)
    log(f"Клиент установлен: {jar.name}")
    return True


# ----------------------------------------------------------------- minecraft
def find_installed_fabric() -> str | None:
    import minecraft_launcher_lib as mll

    ids = [v["id"] for v in mll.utils.get_installed_versions(str(MC_DIR))]
    cands = sorted(i for i in ids if i.startswith("fabric-loader-") and i.endswith("-" + MC_VERSION))
    return cands[-1] if cands else None


def _runtime_java() -> str | None:
    import minecraft_launcher_lib as mll

    comp = "java-runtime-delta"
    try:
        vjson = json.loads((MC_DIR / "versions" / MC_VERSION / f"{MC_VERSION}.json").read_text(encoding="utf-8"))
        comp = vjson.get("javaVersion", {}).get("component", comp)
    except (OSError, ValueError):
        pass
    try:
        return mll.runtime.get_executable_path(comp, str(MC_DIR))
    except Exception:
        return None


def prepare_launch(cfg: dict, callback: dict, log: LogFn) -> tuple[list[str], str]:
    """Install everything that is missing and return (command, cwd)."""
    import minecraft_launcher_lib as mll

    MC_DIR.mkdir(parents=True, exist_ok=True)
    MODS_DIR.mkdir(parents=True, exist_ok=True)

    version_id = find_installed_fabric()
    if version_id is None:
        log(f"Устанавливаю Minecraft {MC_VERSION}…")
        mll.install.install_minecraft_version(MC_VERSION, str(MC_DIR), callback=callback)
        java = _runtime_java()
        loader = mll.fabric.get_latest_loader_version()
        log(f"Устанавливаю Fabric Loader {loader}…")
        try:
            mll.fabric.install_fabric(MC_VERSION, str(MC_DIR), loader_version=loader, callback=callback, java=java)
        except TypeError:  # older library without the 'java' argument
            mll.fabric.install_fabric(MC_VERSION, str(MC_DIR), loader_version=loader, callback=callback)
        version_id = find_installed_fabric() or f"fabric-loader-{loader}-{MC_VERSION}"
    else:
        log(f"Найден {version_id}")

    has_client = install_client_mod(log)
    try:
        ensure_fabric_api(log)
    except Exception as e:  # network problems
        if has_client:
            raise RuntimeError(f"Не удалось скачать Fabric API, без него клиент не запустится: {e}") from e
        log(f"Fabric API не скачан ({e}) - не критично без клиента")

    ram = int(cfg["ram_gb"])
    jvm = [f"-Xmx{ram}G", f"-Xms{min(ram, 2)}G"] + [a for a in str(cfg.get("jvm_extra", "")).split() if a]
    nick = cfg["nickname"]
    options = {
        "username": nick,
        "uuid": offline_uuid(nick),
        "token": "0",
        "launcherName": "BeeVisual",
        "launcherVersion": LAUNCHER_VERSION,
        "gameDirectory": str(MC_DIR),
        "jvmArguments": jvm,
    }
    java = _runtime_java()
    if java:
        options["executablePath"] = java
    command = mll.command.get_minecraft_command(version_id, str(MC_DIR), options)
    return command, str(MC_DIR)


def start_game(command: list[str], cwd: str):
    """Start Minecraft detached from the launcher. Returns (process, log_path)."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOG_DIR / "latest-launch.log"
    logf = open(log_path, "w", encoding="utf-8", errors="replace")
    flags = 0x08000000 if sys.platform == "win32" else 0  # CREATE_NO_WINDOW
    proc = subprocess.Popen(command, cwd=cwd, stdout=logf, stderr=subprocess.STDOUT, creationflags=flags)
    return proc, str(log_path)


def tail(path: str, lines: int = 25) -> str:
    try:
        return "".join(Path(path).read_text(encoding="utf-8", errors="replace").splitlines(True)[-lines:])
    except OSError:
        return ""


# ----------------------------------------------------------------- downloads (Modrinth)
# kind -> (modrinth project_type, folder inside the game dir, loader filter)
KINDS = {
    "mod": ("mod", "mods", ["fabric"]),
    "resourcepack": ("resourcepack", "resourcepacks", None),
    "shader": ("shader", "shaderpacks", None),
}
MANIFEST = BASE_DIR / "installed.json"


def _load_manifest() -> dict:
    try:
        d = json.loads(MANIFEST.read_text(encoding="utf-8"))
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def _save_manifest(d: dict) -> None:
    try:
        BASE_DIR.mkdir(parents=True, exist_ok=True)
        MANIFEST.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError:
        pass


def modrinth_search(query: str, kind: str = "mod", limit: int = 25) -> list[dict]:
    ptype, _folder, _loaders = KINDS[kind]
    facets = [[f"project_type:{ptype}"], [f"versions:{MC_VERSION}"]]
    if kind == "mod":
        facets.append(["categories:fabric"])
    q = urllib.parse.urlencode({"query": query, "facets": json.dumps(facets), "limit": limit, "index": "relevance" if query else "downloads"})
    data = http_json(f"https://api.modrinth.com/v2/search?{q}")
    return [{"id": h["project_id"], "title": h["title"], "desc": h.get("description", ""),
             "author": h.get("author", ""), "downloads": h.get("downloads", 0)} for h in data.get("hits", [])]


def _best_version(project: str, kind: str) -> dict | None:
    _ptype, _folder, loaders = KINDS[kind]
    params = {"game_versions": json.dumps([MC_VERSION])}
    if loaders:
        params["loaders"] = json.dumps(loaders)
    versions = http_json(f"https://api.modrinth.com/v2/project/{project}/version?{urllib.parse.urlencode(params)}")
    if not versions:
        return None
    versions.sort(key=lambda v: (v.get("version_type") == "release", v.get("date_published", "")), reverse=True)
    return versions[0]


def install_project(project: str, kind: str, log: LogFn, _seen: set | None = None) -> None:
    """Download a project (and required dependencies for mods) into the game folder."""
    _seen = _seen if _seen is not None else set()
    if project in _seen:
        return
    _seen.add(project)
    _ptype, folder, _l = KINDS[kind]
    manifest = _load_manifest()
    ver = _best_version(project, kind)
    if ver is None:
        raise RuntimeError(f"Нет версии под Minecraft {MC_VERSION}")
    pid = ver["project_id"]
    _seen.add(pid)
    dest_dir = MC_DIR / folder
    f = next((x for x in ver["files"] if x.get("primary")), ver["files"][0])
    target = dest_dir / f["filename"]
    old = manifest.get(pid)
    if old and old != f["filename"]:
        (dest_dir / old).unlink(missing_ok=True)
    if not target.exists():
        log(f"Скачиваю {f['filename']}…")
        download(f["url"], target, f.get("hashes", {}).get("sha1"))
    manifest[pid] = f["filename"]
    _save_manifest(manifest)
    if kind == "mod":
        for dep in ver.get("dependencies", []):
            if dep.get("dependency_type") == "required" and dep.get("project_id") and dep["project_id"] not in _seen:
                if dep["project_id"] in manifest and (dest_dir / manifest[dep["project_id"]]).exists():
                    continue
                log("Ставлю зависимость…")
                install_project(dep["project_id"], "mod", log, _seen)


def list_installed(kind: str) -> list[Path]:
    d = MC_DIR / KINDS[kind][1]
    if not d.is_dir():
        return []
    exts = {".jar"} if kind == "mod" else {".zip"}
    return sorted((p for p in d.iterdir() if p.suffix.lower() in exts), key=lambda p: p.name.lower())


def remove_installed(path: Path) -> None:
    path.unlink(missing_ok=True)
    m = _load_manifest()
    _save_manifest({k: v for k, v in m.items() if v != path.name})
