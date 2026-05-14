DEFAULT_DELIVERY_AREA = "武陵"

DELIVERY_AREA_CONFIG = {
    "武陵": {
        "delivery_locations": ["武陵城", "试验园区"],
        "delivery_targets": ["常沄", "资源", "彦宁", "齐纶", "赵昭", "裴令容", "阿禾"],
        "delivery_targets_by_location": {
            "武陵城": ["常沄", "资源", "彦宁", "齐纶"],
            "试验园区": ["赵昭", "裴令容", "阿禾"],
        },
        "transfer_search_area": {
            "武陵城": "top",
            "试验园区": "right",
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
    return _get_area_config(area_name)["delivery_targets"]


def get_ocr_priority_locations(area_name: str) -> list[str]:
    return _get_area_config(area_name)["ocr_priority_locations"]


def get_full_cycle_targets(area_name: str, location_name: str) -> list[str]:
    return _get_area_config(area_name)["delivery_targets_by_location"].get(location_name, [])


def extract_delivery_location(text: str, area_name: str) -> str | None:
    for location_name in get_delivery_locations(area_name):
        if location_name in text:
            return location_name
    return None


def get_transfer_search_area_key(location_name: str | None, area_name: str) -> str | None:
    return _get_area_config(area_name)["transfer_search_area"].get(location_name)
