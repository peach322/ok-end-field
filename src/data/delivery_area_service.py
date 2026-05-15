from src.data.delivery_area import DELIVERY_AREA_CONFIG


def _get_area_config(area_name: str) -> dict:
    if area_name not in DELIVERY_AREA_CONFIG:
        supported = "、".join(DELIVERY_AREA_CONFIG.keys())
        raise ValueError(f"不支持的送货区域: {area_name}，当前支持: {supported}")
    return DELIVERY_AREA_CONFIG[area_name]


def get_delivery_locations(area_name: str) -> list[str]:
    return _get_area_config(area_name)["delivery_locations"]


def get_delivery_targets(area_name: str) -> list[str]:
    area_config = _get_area_config(area_name)
    targets_by_location = area_config["delivery_targets_by_location"]
    targets = []
    for location_name in area_config["delivery_locations"]:
        targets.extend(targets_by_location.get(location_name, []))
    return targets


def get_ocr_priority_locations(area_name: str) -> list[str]:
    return _get_area_config(area_name)["ocr_priority_locations"]


def get_full_cycle_targets(area_name: str, location_name: str) -> list[str]:
    return _get_area_config(area_name)["delivery_targets_by_location"].get(location_name, [])


def extract_delivery_location(text: str, area_name: str) -> str | None:
    for location_name in get_delivery_locations(area_name):
        if location_name in text:
            return location_name
    return None


def get_transfer_search_area(location_name: str | None, area_name: str) -> dict | None:
    """返回指定地点的传送搜索配置；可能是 {"preset": "..."}、坐标字典或 None。"""
    if location_name is None:
        return None
    return _get_area_config(area_name)["transfer_search_area"].get(location_name)
