#!/bin/env python3

from dataclasses import dataclass, asdict
import hashlib
import json
from typing import List
import sys
import os
import re
import argparse

HELP = """
Usage: kin [options] [FILE] 
This is a simple script to parse and display information emitted by CUDA kernels in development.
"""

MACROS = """
#define KIN_PRINT(tag, statement) \\
    if (thread0()) { \\
        printf("[kin:start:%s]\\n", tag); \\
        statement; \\
        printf("\\n[kin:end:%s]\\n", tag); \\
    }
"""

START_REGEX = r"\[kin:start:(?P<tag>.+)\]"
END_REGEX = r"\[kin:end:(?P<tag>.+)\]"
POINTER_FILTER_REGEX = r"0x[0-9a-fA-F]+"
LINES_THRESHOLD = 10

def replace_non_alphanumeric(s: str, replacement: str = "_") -> str:
    return re.sub(r"[^a-zA-Z]", replacement, s)

def deterministic_hash(s: List[str], filter_pointer = True) -> int:
    hash = hashlib.sha256()
    for l in s:
        l_filtered = re.sub(POINTER_FILTER_REGEX, "", l) if filter_pointer else l
        hash.update(l_filtered.encode("utf-8"))
    return int(hash.hexdigest(), 16) % (1 << 16)

@dataclass
class Section:
    tag: str
    content: List[str]

    def append_content(self, line):
        self.content.append(line)

    def content_str(self):
        return "\n".join([l.strip() for l in self.content if l != "" and l != "\n"])

@dataclass
class TagInfo:
    content: List[str]

    def to_json(self, tag, filter_pointer=True):
        return {
            "content": self.content[:LINES_THRESHOLD],
            "tag": tag,
            "digest": deterministic_hash(self.content, filter_pointer)
        }

def parse_input_stream(iterator) -> List[Section]:
    acc = []
    cur = None
    for line in iterator:
        # check if line contains start or end tag
        start_match = re.match(START_REGEX, line)
        end_match = re.match(END_REGEX, line)
        if start_match:
            if cur is not None:
                print(f"Error: section {cur.tag} was not closed.")
                sys.exit(1)
            tag = start_match.group("tag")
            cur = Section(tag, [])
        elif end_match:
            tag = end_match.group("tag")
            if cur is None:
                print(f"Error: section {tag} was not opened.")
                sys.exit(1)
            if tag != cur.tag:
                print(f"Error: mismatched tags: {cur.tag}, {tag}")
                sys.exit(1)
            acc.append(cur)
            cur = None
        elif cur is not None:
            cur.append_content(line.strip())
    return acc
   
def main(args):
    # iterate through lines in file

    if args.file == "-":
        acc = parse_input_stream(sys.stdin)
    else:
        with open(args.file, "r") as f:
            acc = parse_input_stream(f)
    
    out = {}
    for section in acc:
        if section.tag not in out:
            out[section.tag] = TagInfo([])
            out[section.tag].content.extend(section.content)
        else:
            out[section.tag].content.extend(section.content)
    
    out_json = {replace_non_alphanumeric(k): ti.to_json(k, not args.no_filter_pointer) for k, ti in out.items()}

    out_str = json.dumps(out_json, indent=4)
    
    if args.output:
        with open(args.output, "w") as f:
            f.write(out_str)
    else:
        print(out_str)

    pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=HELP)
    parser.add_argument("--print-macros", action="store_true", help="Print the macros needed by the script and exit.")
    parser.add_argument("--output", type=str, help="Output file to write the parsed information to.")
    parser.add_argument("--lines-threshold", type=int, default=LINES_THRESHOLD, help="Max number of lines to display in the output.")
    parser.add_argument("file", nargs='?', type=str, default="-", help="File to parse.")
    parser.add_argument("--no-filter-pointer", action="store_true", help="Do not filter out pointer values from hash")

    args = parser.parse_args()

    LINES_THRESHOLD = args.lines_threshold

    if args.print_macros:
        print(MACROS)
        sys.exit(0)
    main(args)
