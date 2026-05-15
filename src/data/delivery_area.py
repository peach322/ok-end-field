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
