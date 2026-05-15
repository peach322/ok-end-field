DEFAULT_DELIVERY_AREA = "武陵"

DELIVERY_AREA_CONFIG = {
    "武陵": {
        "delivery_locations": ["武陵城", "试验园区"],
        "delivery_targets_by_location": {
            "武陵城": ["常沄", "资源", "彦宁", "齐纶"],
            "试验园区": ["赵昭", "裴令容", "阿禾"],
        },
        "transfer_search_area": {
            "武陵城": {"preset": "top"},
            "试验园区": {"preset": "right"},
        },
        "ocr_priority_locations": ["试验园区", "武陵城"],
    }
}


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


def get_transfer_search_area(location_name: str | None, area_name: str):
    """返回指定委托地点的传送点搜索区域配置。

    返回值支持两种格式：
    1) {"preset": "<screen_position_name>"}，对应 ScreenPosition 的预设区域；
    2) {"x": float, "y": float, "to_x": float, "to_y": float}，按屏幕比例定义自定义区域。
    """
    return _get_area_config(area_name)["transfer_search_area"].get(location_name)
