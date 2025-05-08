# PyParser 🐍🔍

PyParser is a powerful and friendly command-line tool for analyzing Python source files! 🚀  
It extracts structured information about classes, functions, variables, and imports from your codebase and outputs the results as JSON.  
Perfect for code analysis, documentation generation, or building your own Python tooling. 📦

---

## ✨ Features

- Parses individual Python files or entire directories (recursively) 📂
- Extracts:
  - Imports 📥
  - Classes (with bases, decorators, methods, class variables, and triple-quoted string comments) 🏷️
  - Functions (with arguments, decorators, and triple-quoted string comments) 🛠️
  - Module-level variables 📝
- Optionally includes base64-encoded source code for each entity 🔒
- Outputs results as JSON, with an optional pretty-print mode 🎨
- See [`output.schema.json`](output.schema.json) for the output format 📑

---

## ⚡ Installation

Clone this repository and install dependencies (if any):

```bash
git clone <your-repo-url>
cd <your-repo-directory>
# (Optional) Install dependencies if required:
# pip install -r requirements.txt
```

---

## 🏃 Usage

Run the CLI tool to analyze a Python file or directory:

```bash
python -m pyparser.cli <file_or_directory> [options]
```

### 🛎️ Options

- `-o, --output <file>`: Write output to a JSON file instead of printing to the console.
- `-p, --pretty`: Pretty-print the output JSON.
- `-r, --recursive`: If the input is a directory, recursively parse all `.py` files.
- `-c, --code`: Include base64-encoded source code for each file in the output.

---

### 💡 Examples

Parse a single file and print the result:

```bash
python -m pyparser.cli myscript.py
```

Parse a directory recursively and write pretty-printed output to a file:

```bash
python -m pyparser.cli myproject/ -r -o result.json -p
```

Parse a file and include base64-encoded code in the output:

```bash
python -m pyparser.cli myscript.py -c
```

---

## 📤 Output Format

The output is a JSON array, with one object per file. Each object contains metadata, imports, classes, functions, variables, and optionally the file's code.

### 💬 Comments and Docstrings

Triple-quoted string literals (including docstrings) are extracted and attached as a `"comment"` property to the nearest class or function node in the output. This allows you to access documentation or comments directly from the JSON.

See [`output.schema.json`](output.schema.json) for the full schema.

---

## 🪪 License

MIT License
