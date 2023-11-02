from pathlib import Path
from d2lootfilter import data
from d2lootfilter.format import FilterRule
from d2lootfilter.parser import parse_format
from d2lootfilter.writer import FilterRemover, FilterRuleWriter


def main():
    # TODO: Parse args
    data_dir = Path("C:\\Program Files (x86)\\Diablo II Resurrected\\Data")

    # Init data
    data.init(data_dir)

    # Parse filter for rules
    rules = []
    with open("test.filter") as f:
        lines = f.read().splitlines()
        instructions = parse_format(lines)
        for instr in instructions:
            nline, verb, prop = instr
            rules.append(FilterRule(nline, verb, prop))

    # Remove any previous rules
    remover = FilterRemover(data_dir)
    remover.remove_all_rules()

    # Write new rules
    writer = FilterRuleWriter(data_dir)
    for rule in rules:
        writer.write(rule)
