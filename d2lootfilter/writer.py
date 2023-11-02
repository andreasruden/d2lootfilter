from contextlib import contextmanager
from io import TextIOWrapper
from itertools import chain
import json
import os
from pathlib import Path
import re
import shutil
from typing import Any, Iterator
from d2lootfilter.data import item_asset

from d2lootfilter.format import Color, FilterRule, Verb, VisualEffect


class FilterRuleWriter:
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir

    def write(self, rule: FilterRule):
        match rule.verb:
            case Verb.Rename:
                self._rename(rule.base_types, rule.rename, rule.text_color)
            case Verb.Hide:
                self._rename(rule.base_types, "", rule.text_color)
            case Verb.Show:
                if rule.text_color:
                    self._rename(rule.base_types, "$BaseType$", rule.text_color)
            case _:
                raise NotImplementedError()
        for vfx in rule.vfx:
            self._vfx(rule.base_types, vfx)

    def _rename(self, bases: list[str], name: str, color: Color | None):
        names = None
        runes = None
        for base in bases:
            if re.match(r"^r[0-9][0-9]$", base):
                if runes is None:
                    runes = self._read_json(self.data_dir / "local" / "lng" / "strings" / "item-runes.json")
                for entry in runes:
                    if entry["Key"] == base:
                        entry["enUS"] = self._color(color) + name.replace("$BaseType$", entry["enUS"])
                        break
            else:
                if names is None:
                    names = self._read_json(self.data_dir / "local" / "lng" / "strings" / "item-names.json")
                for entry in names:
                    if entry["Key"] == base:
                        entry["enUS"] = self._color(color) + name.replace("$BaseType$", entry["enUS"])
                        break
        if names:
            self._write_json(self.data_dir / "local" / "lng" / "strings" / "item-names.json", names)
        if runes:
            self._write_json(self.data_dir / "local" / "lng" / "strings" / "item-runes.json", names)

    def _vfx(self, bases: list[str], vfx: VisualEffect):
        for base in bases:
            path = item_asset(base)
            dat = self._read_json(path)
            match vfx:
                case VisualEffect.Beam:
                    dat["dependencies"]["particles"].append(
                        {"path": "data/hd/vfx/particles/overlays/object/horadric_light/fx_horadric_light.particles"}
                    )
                    dat["entities"].append(
                        {
                            "type": "Entity",
                            "name": "entity_beam",
                            "id": 987654321001,
                            "components": [
                                {
                                    "type": "TransformDefinitionComponent",
                                    "name": "component_transform1",
                                    "position": {"x": 0, "y": 0, "z": 0},
                                    "orientation": {"x": 0, "y": 0, "z": 0, "w": 1},
                                    "scale": {"x": 1, "y": 1, "z": 1},
                                    "inheritOnlyPosition": False,
                                },
                                {
                                    "type": "VfxDefinitionComponent",
                                    "name": "entity_vfx_beam",
                                    "filename": "data/hd/vfx/particles/overlays/object/horadric_light/fx_horadric_light.particles",
                                    "hardKillOnDestroy": False,
                                },
                            ],
                        }
                    )
                case VisualEffect.Glitter:
                    dat["entities"].append(
                        {
                            "type": "Entity",
                            "name": "entity_glitter",
                            "id": 987654321002,
                            "components": [
                                {
                                    "type": "VfxDefinitionComponent",
                                    "name": "entity_vfx_glitter",
                                    "filename": "data/hd/vfx/particles/overlays/paladin/aura_fanatic/aura_fanatic.particles",
                                    "hardKillOnDestroy": False,
                                }
                            ],
                        }
                    )
                case VisualEffect.Flash:
                    dat["entities"].append(
                        {
                            "type": "Entity",
                            "name": "entity_flash",
                            "id": 987654321003,
                            "components": [
                                {
                                    "type": "TransformDefinitionComponent",
                                    "name": "component_transform1",
                                    "position": {"x": 0, "y": 0, "z": 0},
                                    "orientation": {"x": 0, "y": 0, "z": 0, "w": 1},
                                    "scale": {"x": 1, "y": 1, "z": 1},
                                    "inheritOnlyPosition": False,
                                },
                                {
                                    "type": "VfxDefinitionComponent",
                                    "name": "entity_vfx_flash",
                                    "filename": "data/hd/vfx/particles/overlays/common/valkyriestart/valkriestart_overlay.particles",
                                    "hardKillOnDestroy": False,
                                },
                            ],
                        }
                    )
                case _:
                    raise RuntimeError(f"Unhandled vfx type {vfx}")
            self._write_json(path, dat)

    @contextmanager
    def _open_bk(self, path: Path) -> Iterator[TextIOWrapper]:
        bk_path = path.parent / (path.name + ".d2lootfilter")
        if not bk_path.exists():
            shutil.copy(path, bk_path)
        f = open(path, "w", encoding="utf-8-sig")
        yield f
        f.close()

    def _write_json(self, path: Path, data: Any):
        with self._open_bk(path) as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"Wrote new rules to {path.relative_to(self.data_dir)}")

    def _read_json(self, path: Path):
        with open(path, encoding="utf-8-sig") as f:
            return json.load(f)

    def _color(self, color: Color | None) -> str:
        match color:
            case Color.Red:
                return "ÿc1"
            case Color.Blue:
                return "ÿc3"
            case Color.Purple:
                return "ÿc;"
            case _:
                pass
        return ""


class FilterRemover:
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir

    def remove_all_rules(self):
        paths = chain(self.data_dir.glob("local/**/*.d2lootfilter"), self.data_dir.glob("hd/**/*.d2lootfilter"))
        for path in paths:
            dst_path = Path(path).with_suffix("")
            os.replace(path, dst_path)
            print(f"Removed filter rules in {dst_path.relative_to(self.data_dir)}")
