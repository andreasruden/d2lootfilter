from pathlib import Path
import sys
from d2lootfilter import data
from d2lootfilter.format import FilterRule
from d2lootfilter.parser import parse_format
from d2lootfilter.writer import FilterRemover, FilterRuleWriter


def main():
    # TODO: Parse args
    data_dir = Path("C:\\Program Files (x86)\\Diablo II Resurrected\\Data")

    # Remove any previous rules
    remover = FilterRemover(data_dir)
    remover.remove_all_rules()

    # Init data
    data.init(data_dir)

    # Parse filter for rules
    rules = []
    with open("example.filter") as f:
        lines = f.read().splitlines()
        instructions = parse_format(lines)
        for instr in instructions:
            nline, verb, prop = instr
            rules.append(FilterRule(source_line=nline, verb=verb, props=prop))

    # Check for any base type duplicates
    observed = {}
    for rule in rules:
        for base in rule.base_types:
            if base in observed:
                print(f"Error: base {base!r} appears in rule at line {observed[base]} and line {rule.source_line}")
                sys.exit(1)
            observed[base] = rule.source_line

    # Write new rules
    writer = FilterRuleWriter(data_dir)
    for rule in rules:
        writer.write(rule)
