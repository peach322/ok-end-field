from src.data.characters import characters
from src.data.FeatureList import FeatureList


def get_contact_list_with_feature_list() -> dict[str, str]:
    """
    从角色数据与 FeatureList 交集构建“中文名 -> 联络特征名”映射。
    仅返回在 FeatureList 中存在对应图片资源的角色。
    """
    feature_set = {f.value for f in FeatureList}  # 取 FeatureList 枚举的所有值

    en_to_zh = {info["en"] + "_contact": info["zh"] for info in characters.values()}
    # 构建英文名 -> 中文名字典，英文名后面加 "_contact"

    common = feature_set & en_to_zh.keys()  # 取 feature_set 和字典 key 的交集

    return {en_to_zh[c]: c for c in common}  # 中文名 -> 英文名字典
