WULING_DELIVERY_LOCATIONS = ("武陵城", "试验园区")


def extract_delivery_location(text: str) -> str | None:
    """从OCR文本中提取送货地点。"""
    for location_name in WULING_DELIVERY_LOCATIONS:
        if location_name in text:
            return location_name
    return None


def get_transfer_search_area_key(location_name: str | None) -> str | None:
    """根据送货地点返回传送点搜索区域键。"""
    if location_name == "试验园区":
        return "right"
    if location_name == "武陵城":
        return "top"
    return None
