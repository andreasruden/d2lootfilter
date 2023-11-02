from csv import DictReader
import json
from pathlib import Path

from d2lootfilter.format import Class

_item_names = []
_item_runes = []

_class_map = {}


def init(path: Path):
    global _item_names, _item_runes
    with open(path / "local" / "lng" / "strings" / "item-names.json", encoding="utf-8-sig") as f:
        _item_names = json.load(f)
    with open(path / "local" / "lng" / "strings" / "item-runes.json", encoding="utf-8-sig") as f:
        _item_runes = json.load(f)

    for cls in Class:
        _class_map[cls] = set()

    with open(path / "global" / "excel" / "armor.txt") as f:
        for row in DictReader(f, delimiter="\t"):
            # TODO: Proper class selection
            n = row["name"]
            cls = Class.Unknown
            if "Cap" in n or "Helm" in n:
                cls = Class.Helmet
            elif "Armor" in n or "Mail" in n or "Plate" in n:
                cls = Class.Chest
            elif "Armor" in n or "Mail" in n or "Plate" in n:
                cls = Class.Chest
            elif "Gloves" in n:
                cls = Class.Gloves
            elif "Boots" in n:
                cls = Class.Boots
            elif "Belt" in n:
                cls = Class.Belt
            _class_map[cls].add(row["code"])
    # TODO: weapon.txt, misc.txt -> class_map

    # Rune class
    for i in range(1, 34):
        _class_map[Class.Rune].add(f"r{i:02d}")


def item_names() -> list:
    return _item_names


def item_runes() -> list:
    return _item_runes


def class_to_bases(cls: str) -> set:
    return _class_map[cls]
