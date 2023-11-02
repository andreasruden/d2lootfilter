from enum import Enum
import re

from d2lootfilter import data


class FormatError(Exception):
    pass


class Verb(str, Enum):
    Show = "Show"
    Hide = "Hide"
    Rename = "Rename"


class Property(str, Enum):
    BaseType = "BaseType"
    Class = "Class"
    To = "To"  # only for verb Rename
    AddVfx = "AddVfx"
    PlaySound = "PlaySound"


class Class(str, Enum):
    Unknown = "N/A"
    Helmet = "Helmet"
    Chest = "Chest"
    Gloves = "Gloves"
    Shield = "Shield"
    Boots = "Boots"
    Ring = "Ring"
    Amulet = "Amulet"
    Belt = "Belt"
    Rune = "Rune"
    # TODO: Add missing classes


class RelationalOp(str, Enum):
    Equal = "=="


class VisualEffect(str, Enum):
    Beam = "Beam"


class FilterRule:
    def __init__(self, source_line: int, verb: Verb, props: list[tuple[Property, str]]):
        self.source_line = source_line
        self.base_types = None
        self.class_bases = None
        self.rename = None
        self.vfx = []
        self.sounds = []
        self.verb = verb
        for prop in props:
            proptype, args = prop
            self.eval_prop(proptype, args)

        if self.class_bases:
            if self.base_types:
                self.base_types = [b for b in self.base_types if b in self.class_bases]
            else:
                self.base_types = self.class_bases

    def eval_prop(self, prop: Property, args: str):
        match prop:
            case Property.BaseType:
                self._base_type(args)
            case Property.Class:
                self._class(args)
            case Property.To:
                self._to(args)
            case Property.AddVfx:
                self._add_vfx(args)
            case Property.PlaySound:
                self._play_sound(args)
            case _:
                raise NotImplementedError()

    def _base_type(self, args):
        if not self.base_types:
            self.base_types = []

        op, args = self._arg_relational_op(args, optional=True)
        if op not in [None, RelationalOp.Equal]:
            raise FormatError(f"Format error @ rule starting on line {self.source_line}: Invalid BaseType op")

        arg, args = self._arg_str(args)
        while arg:
            found = False
            for item in data.item_names():
                if (not op and arg in item["enUS"]) or (op and arg == item["enUS"]):
                    self.base_types.append(item["Key"])
                    found = True
            for runeitem in data.item_runes():
                if (
                    re.match(r"r[0-9][0-9]", runeitem["Key"])
                    and (not op and arg in runeitem["enUS"])
                    or (op and arg == runeitem["enUS"])
                ):
                    self.base_types.append(runeitem["Key"])
                    found = True
            if not found:
                raise FormatError(
                    f"Format error @ rule starting on line {self.source_line}: No basetype matching {arg!r}"
                )
            arg, args = self._arg_str(args, optional=True)

    def _class(self, args):
        if not self.class_bases:
            self.class_bases = []

        arg, args = self._arg_str(args)
        while arg:
            try:
                cls = Class(arg)
            except ValueError:
                raise FormatError(f"Format error @ rule starting on line {self.source_line}: Invalid class {arg!r}")
            bases = data.class_to_bases(cls)
            self.class_bases.extend(bases)
            arg, args = self._arg_str(args, optional=True)

    def _to(self, args):
        if self.verb != Verb.Rename:
            raise FormatError(
                f"Format error @ rule starting on line {self.source_line}: Property 'To' can only appear in verb 'Rename'."
            )
        arg, rest = self._arg_str(args)
        if len(rest) > 0:
            raise FormatError(f"Format error @ rule starting on line {self.source_line}: Trailing data after 'To'")
        self.rename = arg

    def _add_vfx(self, args):
        arg, rest = self._arg_str(args, False)
        try:
            vfx = VisualEffect(arg)
        except ValueError:
            raise FormatError(f"Format error @ rule starting on line {self.source_line}: Invalid vfx {arg!r}.")
        if len(rest) > 0:
            raise FormatError(f"Format error @ rule starting on line {self.source_line}: Trailing data after 'AddVfx'")
        self.vfx.append(vfx)

    def _play_sound(self, args):
        raise NotImplementedError()

    def _arg_str(self, args, optional=False):
        if len(args) > 0 and args[0] == '"':
            args = args[1:]
            try:
                end = args.index('"')
                if len(args) > end + 1 and args[end + 1] != " ":
                    raise FormatError(
                        f"Format error @ rule starting on line {self.source_line}: Expected space after quote"
                    )
                arg, rest = args[:end], args[end + 2 :]
            except ValueError:
                raise FormatError(
                    f"Format error @ rule starting on line {self.source_line}: Missing quote to close string"
                )
        else:
            arg, rest = self._arg_next_literal(args, optional)

        arg = arg.strip()
        if len(arg) == 0:
            if not optional:
                raise FormatError(
                    f"Format error @ rule starting on line {self.source_line}: Missing quote to close string"
                )
            arg = None
        return arg, rest

    def _arg_int(self, args):
        arg, args = self._arg_next_literal(args, False)
        try:
            val = int(arg)
        except ValueError:
            raise FormatError(f"Format error @ rule starting on line {self.source_line}: Expected integer")
        return val, args

    def _arg_relational_op(self, args, optional=False):
        text, rest = self._arg_next_literal(args, optional=optional)
        try:
            op = RelationalOp(text)
        except ValueError:
            if not optional:
                FormatError(f"Format error @ rule starting on line {self.source_line}: Missing Relational Operator")
            return None, args
        return op, rest

    def _arg_next_literal(self, args, optional):
        try:
            end = args.index(" ")
        except ValueError:
            end = len(args)
        val = args[:end].strip()
        if not optional and len(val) == 0:
            raise FormatError(f"Format error @ rule starting on line {self.source_line}: Empty literal")
        return val, args[end + 1 :]
