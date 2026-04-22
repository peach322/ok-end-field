import copy
import json
import os
import threading
import uuid
from typing import Any, Dict, List, Tuple

from ok.util.file import ensure_dir_for_file, get_relative_path

_STORE_PATH = get_relative_path("configs", "account_scoped_overrides.json")
_LOCK = threading.Lock()
_CACHE_MTIME = object()
_EMPTY_STORE: Dict[str, Any] = {
    "account_list_text": "",
    "account_registry": {},
    "accounts": {},
}
_CACHE_DATA: Dict[str, Any] = copy.deepcopy(_EMPTY_STORE)


def get_store_path() -> str:
    """返回账号作用域覆盖配置文件路径。"""
    return _STORE_PATH


def _new_store() -> Dict[str, Any]:
    """创建一份新的默认存储结构副本。"""
    return copy.deepcopy(_EMPTY_STORE)


def _clean_text(value: Any) -> str:
    """将任意值规范为字符串，None 转为空字符串。"""
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return str(value)


def _clean_username(value: Any) -> str:
    """规范化账号名并去除首尾空白。"""
    return _clean_text(value).strip()


def _parse_account_list_text_internal(account_list_text: Any) -> Tuple[List[Dict[str, str]], List[str]]:
    """解析账号列表文本，返回有效账号项与非法行。"""
    entries: List[Dict[str, str]] = []
    invalid_lines: List[str] = []

    text = _clean_text(account_list_text)
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue

        # 账号页默认每行仅填写账号名；兼容旧格式：账号,密码。
        if "," in line:
            username_part, password_part = line.split(",", 1)
            username = username_part.strip()
            password = password_part.strip()
        else:
            username = line.strip()
            password = ""

        if not username:
            invalid_lines.append(line)
            continue

        entries.append({"username": username, "password": password})

    return entries, invalid_lines


def parse_account_list_text(account_list_text: Any) -> List[Dict[str, str]]:
    """对外暴露的账号列表解析接口，仅返回有效账号项。"""
    entries, _ = _parse_account_list_text_internal(account_list_text)
    return entries


def _normalize_registry(raw_registry: Any) -> Dict[str, Dict[str, Any]]:
    """规范化 account_registry 结构并清理非法数据。"""
    if not isinstance(raw_registry, dict):
        return {}

    normalized: Dict[str, Dict[str, Any]] = {}
    for raw_account_id, raw_meta in raw_registry.items():
        if not isinstance(raw_account_id, str):
            continue
        account_id = raw_account_id.strip()
        if not account_id:
            continue

        username = ""
        aliases: List[str] = []

        if isinstance(raw_meta, dict):
            username = _clean_username(raw_meta.get("username", ""))
            raw_aliases = raw_meta.get("aliases", [])
            if isinstance(raw_aliases, list):
                for raw_alias in raw_aliases:
                    alias = _clean_username(raw_alias)
                    if alias and alias not in aliases:
                        aliases.append(alias)
        elif isinstance(raw_meta, str):
            username = _clean_username(raw_meta)

        if username and username not in aliases:
            aliases.insert(0, username)
        if not username and aliases:
            username = aliases[0]
        if not username:
            continue

        normalized[account_id] = {
            "username": username,
            "aliases": aliases,
        }

    return normalized


def _normalize_accounts_map(raw_accounts: Any) -> Dict[str, Dict[str, Dict[str, Any]]]:
    """规范化 accounts 映射，仅保留合法账号与任务覆盖项。"""
    if not isinstance(raw_accounts, dict):
        return {}

    normalized_accounts: Dict[str, Dict[str, Dict[str, Any]]] = {}
    for raw_account_key, raw_task_map in raw_accounts.items():
        if not isinstance(raw_account_key, str):
            continue
        account_key = raw_account_key.strip()
        if not account_key or not isinstance(raw_task_map, dict):
            continue

        normalized_task_map: Dict[str, Dict[str, Any]] = {}
        for raw_task_name, raw_override_map in raw_task_map.items():
            if not isinstance(raw_task_name, str):
                continue
            task_name = raw_task_name.strip()
            if not task_name or not isinstance(raw_override_map, dict):
                continue
            normalized_task_map[task_name] = dict(raw_override_map)

        if normalized_task_map:
            normalized_accounts[account_key] = normalized_task_map

    return normalized_accounts


def _find_account_id_by_username(
    registry: Dict[str, Dict[str, Any]],
    username: str,
    include_aliases: bool = False,
) -> str:
    """按账号名查询 account_id，可选包含别名匹配。"""
    if not username:
        return ""

    exact_matches: List[str] = []
    alias_matches: List[str] = []
    for account_id, meta in registry.items():
        current_username = _clean_username(meta.get("username", ""))
        if current_username == username:
            exact_matches.append(account_id)
            continue

        if include_aliases:
            aliases = meta.get("aliases", [])
            if isinstance(aliases, list) and username in aliases:
                alias_matches.append(account_id)

    if exact_matches:
        return sorted(exact_matches)[0]
    if include_aliases and alias_matches:
        return sorted(alias_matches)[0]
    return ""


def _generate_account_id(registry: Dict[str, Dict[str, Any]]) -> str:
    """生成不与现有 registry 冲突的账号 ID。"""
    while True:
        account_id = f"acc_{uuid.uuid4().hex[:12]}"
        if account_id not in registry:
            return account_id


def _ensure_registry_entry(
    registry: Dict[str, Dict[str, Any]],
    username: str,
    account_id: str | None = None,
) -> str:
    """确保账号名在 registry 中存在并返回其 account_id。"""
    username = _clean_username(username)
    if not username:
        return ""

    if account_id:
        account_id = account_id.strip()
    if not account_id:
        account_id = _generate_account_id(registry)

    meta = registry.setdefault(account_id, {"username": username, "aliases": [username]})
    aliases = meta.get("aliases", [])
    if not isinstance(aliases, list):
        aliases = []
    if username not in aliases:
        aliases.append(username)

    meta["aliases"] = aliases
    meta["username"] = username
    return account_id


def _merge_task_maps(target: Dict[str, Dict[str, Any]], source: Dict[str, Dict[str, Any]]) -> None:
    """将 source 任务覆盖项合并到 target。"""
    for task_name, override_map in source.items():
        if task_name not in target:
            target[task_name] = dict(override_map)
            continue
        target[task_name].update(dict(override_map))


def _normalize(data: Any) -> Dict[str, Any]:
    """规范化整体存储数据，兼容旧键结构并清理异常项。"""
    if not isinstance(data, dict):
        return _new_store()

    account_list_text = _clean_text(data.get("account_list_text", ""))
    registry = _normalize_registry(data.get("account_registry"))
    raw_accounts = _normalize_accounts_map(data.get("accounts"))

    normalized_accounts: Dict[str, Dict[str, Dict[str, Any]]] = {}
    for raw_account_key, task_map in raw_accounts.items():
        account_id = ""
        if raw_account_key in registry:
            account_id = raw_account_key
        else:
            username = _clean_username(raw_account_key)
            if username:
                account_id = _find_account_id_by_username(registry, username, include_aliases=True)
                if not account_id:
                    account_id = _ensure_registry_entry(registry, username)

        if not account_id:
            continue

        merged_task_map = normalized_accounts.setdefault(account_id, {})
        _merge_task_maps(merged_task_map, task_map)

    return {
        "account_list_text": account_list_text,
        "account_registry": registry,
        "accounts": normalized_accounts,
    }


def _sync_account_list_text_on_data(data: Dict[str, Any], text: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """将账号列表文本同步到存储数据并返回变更摘要。"""
    normalized = _normalize(data)
    new_entries, invalid_lines = _parse_account_list_text_internal(text)

    registry = normalized.setdefault("account_registry", {})
    accounts = normalized.setdefault("accounts", {})

    reused_count = 0
    created_count = 0
    assigned_ids: List[str] = []

    for entry in new_entries:
        username = entry.get("username", "")
        account_id = _find_account_id_by_username(registry, username)

        if account_id:
            reused_count += 1
        else:
            # 业务约束：账号名就是手机号，手机号变化直接视为新账号。
            account_id = _generate_account_id(registry)
            created_count += 1

        _ensure_registry_entry(registry, username, account_id=account_id)
        assigned_ids.append(account_id)

    keep_ids = set(assigned_ids) | set(accounts.keys())
    for account_id in list(registry.keys()):
        if account_id not in keep_ids and not accounts.get(account_id):
            registry.pop(account_id, None)

    normalized["account_list_text"] = _clean_text(text)

    summary = {
        "total_valid": len(new_entries),
        "invalid_count": len(invalid_lines),
        "reused_count": reused_count,
        "created_count": created_count,
        "identity_by_username_only": True,
        "password_ignored_for_identity": True,
        "username_change_creates_new_id": True,
    }
    return normalized, summary


def load_overrides(force: bool = False) -> Dict[str, Any]:
    """读取覆盖配置，支持基于 mtime 的内存缓存。"""
    global _CACHE_MTIME
    global _CACHE_DATA

    with _LOCK:
        if os.path.exists(_STORE_PATH):
            current_mtime: Any = os.path.getmtime(_STORE_PATH)
        else:
            current_mtime = None

        if not force and current_mtime == _CACHE_MTIME:
            return copy.deepcopy(_CACHE_DATA)

        if current_mtime is None:
            data = _new_store()
        else:
            try:
                with open(_STORE_PATH, "r", encoding="utf-8") as fp:
                    data = json.load(fp)
            except Exception:
                data = _new_store()

        normalized = _normalize(data)
        _CACHE_DATA = normalized
        _CACHE_MTIME = current_mtime
        return copy.deepcopy(normalized)


def save_overrides(data: Dict[str, Any]) -> Dict[str, Any]:
    """规范化并持久化覆盖配置，同时刷新缓存。"""
    global _CACHE_MTIME
    global _CACHE_DATA

    normalized = _normalize(data)

    with _LOCK:
        ensure_dir_for_file(_STORE_PATH)
        with open(_STORE_PATH, "w", encoding="utf-8") as fp:
            json.dump(normalized, fp, ensure_ascii=False, indent=2)

        _CACHE_DATA = normalized
        _CACHE_MTIME = os.path.getmtime(_STORE_PATH)

    return copy.deepcopy(normalized)


def sync_account_list_text(text: str) -> Dict[str, Any]:
    """同步账号列表文本并返回同步摘要。"""
    data = load_overrides(force=True)
    updated, summary = _sync_account_list_text_on_data(data, text if isinstance(text, str) else str(text))
    save_overrides(updated)
    return summary


def resolve_account_id(username: str, create_if_missing: bool = False) -> str:
    """根据账号名解析 account_id，可按需自动创建。"""
    account_name = _clean_username(username)
    if not account_name:
        return ""

    data = load_overrides(force=create_if_missing)
    registry = data.setdefault("account_registry", {})
    account_id = _find_account_id_by_username(registry, account_name)
    if account_id or not create_if_missing:
        return account_id

    account_id = _ensure_registry_entry(registry, account_name)
    save_overrides(data)
    return account_id


def get_account_task_overrides(account: str, task_name: str, account_name: str = "") -> Dict[str, Any]:
    """读取指定账号与任务的覆盖配置。"""
    if not task_name:
        return {}

    account_key = _clean_username(account)
    account_name = _clean_username(account_name)
    if not account_key and not account_name:
        return {}

    data = load_overrides()
    accounts = data.get("accounts") or {}
    registry = data.get("account_registry") or {}

    resolved_key = ""
    if account_key in registry or account_key in accounts:
        resolved_key = account_key
    if not resolved_key and account_key:
        resolved_key = _find_account_id_by_username(registry, account_key)
    if not resolved_key and account_name:
        resolved_key = _find_account_id_by_username(registry, account_name)

    if resolved_key and isinstance(accounts.get(resolved_key), dict):
        return dict(accounts.get(resolved_key, {}).get(task_name, {}))

    # 兼容旧结构：账号名作为直接键。
    legacy_key = account_name or account_key
    if legacy_key and isinstance(accounts.get(legacy_key), dict):
        return dict(accounts.get(legacy_key, {}).get(task_name, {}))

    return {}


def _resolve_account_id_for_write(data: Dict[str, Any], account: str) -> str:
    """写入前解析或创建账号对应的 account_id。"""
    account_key = _clean_username(account)
    if not account_key:
        return ""

    registry = data.setdefault("account_registry", {})
    if account_key in registry:
        return account_key

    account_id = _find_account_id_by_username(registry, account_key)
    if account_id:
        return account_id

    return _ensure_registry_entry(registry, account_key)


def set_account_task_overrides(account: str, task_name: str, values: Dict[str, Any]) -> None:
    """设置（或清除）账号在指定任务上的覆盖配置。"""
    if not account or not task_name:
        return

    data = load_overrides()
    account_id = _resolve_account_id_for_write(data, account)
    if not account_id:
        return

    accounts = data.setdefault("accounts", {})
    task_map = accounts.setdefault(account_id, {})

    if values:
        task_map[task_name] = dict(values)
    else:
        task_map.pop(task_name, None)

    if not task_map:
        accounts.pop(account_id, None)

    save_overrides(data)


def remove_account_task_overrides(account: str, task_name: str) -> None:
    """删除账号在指定任务上的覆盖配置。"""
    if not account or not task_name:
        return

    data = load_overrides()
    account_id = _resolve_account_id_for_write(data, account)
    if not account_id:
        return

    accounts = data.get("accounts", {})
    task_map = accounts.get(account_id)
    if not isinstance(task_map, dict):
        return

    task_map.pop(task_name, None)
    if not task_map:
        accounts.pop(account_id, None)

    save_overrides(data)


def list_accounts() -> list[str]:
    """列出当前存在任务覆盖数据的账号 ID。"""
    data = load_overrides()
    return list((data.get("accounts") or {}).keys())


def get_account_list_text() -> str:
    """读取账号列表原始文本配置。"""
    data = load_overrides()
    value = data.get("account_list_text", "")
    return value if isinstance(value, str) else str(value)


def set_account_list_text(text: str) -> None:
    """写入账号列表文本并触发同步。"""
    sync_account_list_text(text)
