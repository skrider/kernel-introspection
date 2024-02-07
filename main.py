#!/bin/env python3

from dataclasses import dataclass
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
        printf("[kin:start:%s]", tag); \\
        statement; \\
        printf("[kin:end:%s]", tag); \\
    } \\
"""

START_REGEX = r"\[kin:start:(?P<tag>.+)\]"
END_REGEX = r"\[kin:end:(?P<tag>.+)\]"

@dataclass
class Section:
    tag: str
    content: List[str]

    def append_content(self, line):
        self.content.append(line)

    def content_str(self):
        return "\n".join(self.content)

@dataclass
class TagInfo:
    content: List[str]

def main(args):
    # iterate through lines in file
    with open(args.file, "r") as f:
        acc = []
        cur = None
        for line in f:
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

    out = {}
    for section in acc:
        if section.tag not in out:
            out[section.tag] = TagInfo(section.content)
        else:
            out[section.tag].content.append(section.content_str())
    
    out_str = json.dumps(out, indent=4)
    
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
    parser.add_argument("file", type=str, help="File to parse.")
    
    args, cmd = parser.parse_args()
    if args.print_macros:
        print(MACROS)
        sys.exit(0)
    main(args)
