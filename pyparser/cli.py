# pyparser/cli.py

import argparse
import json
import os
import base64
from pyparser.parser import parse_python_file

def run():
    import sys
    # Set up command-line argument parsing
    parser = argparse.ArgumentParser(description="Parse a Python file and extract classes, functions, variables, and imports.")
    parser.add_argument("file", help="Python file to parse")
    parser.add_argument("--output", "-o", help="Output to a JSON file instead of console")
    parser.add_argument("--pretty", "-p", action="store_true", help="Pretty print the output JSON")
    parser.add_argument(
      "-r", "--recursive",
      action="store_true",
      help="If <file> is a directory, walk it recursively and parse all .py files"
    )
    parser.add_argument(
      "-c", "--code",
      action="store_true",
      help="Include the base64-encoded code for each file in the output JSON"
    )

    # Show help if no arguments are provided
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args()

    results_list = []

    def add_code_to_result(result, filepath):
        # Add base64-encoded code to the result dictionary
        with open(filepath, "rb") as f:
            code_bytes = f.read()
        code_b64 = base64.b64encode(code_bytes).decode("ascii")
        result["code"] = code_b64

    if args.recursive:
        # Recursively parse all .py files in a directory
        if not os.path.isdir(args.file):
            print(f"Error: {args.file} is not a directory")
            sys.exit(1)
        py_files = []
        for root, dirs, files in os.walk(args.file):
            for fname in files:
                if fname.endswith(".py"):
                    py_files.append(os.path.join(root, fname))
        for path in py_files:
            result = parse_python_file(path, include_code=args.code)
            if args.code:
                add_code_to_result(result, path)
            results_list.append(result)
    else:
        # Parse a single file
        result = parse_python_file(args.file, include_code=args.code)
        if args.code:
            add_code_to_result(result, args.file)
        results_list = [result]

    if args.output:
        # Write output to a file
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(results_list, f, indent=2 if args.pretty else None)
        print(f"Wrote output to {args.output}")
    else:
        # Always use pretty print for console output for better readability
        print(json.dumps(results_list, indent=2))

if __name__ == "__main__":
    run()
