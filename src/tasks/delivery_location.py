WULING_DELIVERY_LOCATIONS = ("武陵城", "试验园区")
WULING_OCR_PRIORITY_LOCATIONS = ("试验园区", "武陵城")
LOCATION_TO_TRANSFER_SEARCH_AREA = {
    "试验园区": "right",
    "武陵城": "top",
}


def extract_delivery_location(text: str) -> str | None:
    """从OCR文本中提取送货地点；命中返回地点名称，未命中返回 None。"""
    for location_name in WULING_DELIVERY_LOCATIONS:
        if location_name in text:
            return location_name
    return None


def get_transfer_search_area_key(location_name: str | None) -> str | None:
    """根据送货地点返回传送点搜索区域键：试验园区->right，武陵城->top，未知->None。"""
    return LOCATION_TO_TRANSFER_SEARCH_AREA.get(location_name)
