from d2lootfilter.format import Property, Verb


class ParseError(Exception):
    pass


def parse_format(
    lines: list[str],
) -> list[tuple[int, Verb, list[tuple[Property, str]]]]:
    instructions = []
    verb = None
    indented = False
    properties = []
    source_line = 0
    for n, line in enumerate(lines):
        if line.startswith("#"):
            continue
        if line.startswith(" ") or line.startswith("\t"):
            indented = True

        if len(line) == 0:
            indented = False
            if verb is not None:
                instructions.append((source_line, verb, properties))
                verb = None
                properties = []
        elif not indented:
            if verb:
                raise ParseError(f"Error @ line {n + 1}: Expected indentation")
            try:
                verb = Verb(line)
                source_line = n + 1
            except ValueError:
                raise ParseError(f"Error @ line {n + 1}: Invalid verb {line!r}")
        else:
            splits = line.lstrip().split(" ", maxsplit=1)
            print(splits)
            try:
                prop = Property(splits[0])
            except ValueError:
                raise ParseError(f"Error @ line {n + 1}: Invalid property {splits[0]!r}")
            properties.append((prop, "" if len(splits) == 0 else splits[1]))

    if verb is not None:
        instructions.append((source_line, verb, properties))
    return instructions
