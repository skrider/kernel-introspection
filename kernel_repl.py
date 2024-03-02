#!/bin/env python3

import numpy as np
import code
from argparse import ArgumentParser
import sys
import re
from typing import Dict
from dataclasses import dataclass

begin_regex = r"<NUMPY>$"
end_regex = r"^</NUMPY>"
barrier_regex = r"<BARRIER>"
extract_regex = r"(?P<name>\w+)\s*=\s*(?P<value>[\s\S]+)"

MACROS = """
#define PRINT_NUMPY(t)      \\
    cute::print("\n<NUMPY>\n");   \\
    cute::print(#t " = ");        \\
    cute::print_numpy(t);         \\
    cute::print("\n</NUMPY>\n");
#define PRINT_NUMPY_VAL(t)  \\
    cute::print("\n<NUMPY>\n");   \\
    cute::print(#t " = ");        \\
    cute::print(t);               \\
    cute::print("\n</NUMPY>\n");
#define PRINT_NUMPY_STR(t)  \\
    cute::print("\n<NUMPY>\n");   \\
    cute::print(#t " = ");        \\
    cute::print(t);               \\
    cute::print("\n</NUMPY>\n");
#define PRINT_NUMPY_BARRIER() cute::print("\n<BARRIER>\n");

template<class Engine, class Layout>
void
print_numpy(cute::Tensor<Engine,Layout> const& t)
{
    using namespace cute;
	print("np.array([");
	for (int i = 0; i < t.size(); i++) {
		print(t(i));
		if (i < t.size() - 1) {
			print(", ");
		}
		if (i % 10 == 9) {
			print("\n");
		}
	}
	print("])");
	print(".reshape(");
	print(transform_apply(
		t.layout().shape(), 
		// add 0 to force runtime eval and get rid of the underscore
		[](auto const& m) { return size(m) + 0; },  
		[](auto const&... v) { return make_shape(v...); }
	));
	print(", order='F')");
}
"""
    
# read in all of stdin
def main(args):
    if args.file:
        with open(args.file, "r") as f:
            repl(f)
    else:
        repl(sys.stdin)

def parse_section(raw):
    raw_single_line = raw.replace("\n", "")
    match = re.match(extract_regex, raw_single_line)
    assert match
    return match.group("name"), match.group("value")

def repl(input_stream):
    def advance(context):
        state = 0
        acc = ""
        all : Dict[str, str] = {}

        while state != 2:
            try:
                line = next(input_stream)
            except:
                break
            if re.match(begin_regex, line):
                assert state != 1
                state = 1
            elif re.match(end_regex, line):
                assert state == 1
                name, value = parse_section(acc)
                all[name] = value
                acc = ""
                state = 0
            elif re.match(barrier_regex, line):
                assert state == 0
                state = 2
            elif state == 1:
                acc += line

        for name, value in all.items():
            context[name] = eval(value)

    context = {}
    advance(context)
    
    # start code interactive
    repl_local_vars = {}
    repl_local_vars['advance'] = advance
    repl_local_vars['np'] = np
    repl_local_vars['context'] = context

    print(context)

    code.interact(local=repl_local_vars)

if __name__ == "__main__":
    parser = ArgumentParser(description="start a repl with kernel output history")
    parser.add_argument("--file", type=str, help="file to read in", required=False)
    parser.add_argument("--print-macros", type=bool, help="print helper macros", required=False)
    
    args = parser.parse_args()

    if args.print_macros:
        print(MACROS)
    else:
        main(args)
