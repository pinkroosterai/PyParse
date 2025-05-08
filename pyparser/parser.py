# pyparser/parser.py

import ast, os, platform

# Visitor class to walk the AST and collect code structure information
class CodeVisitor(ast.NodeVisitor):
    def __init__(self):
        # Lists to store discovered imports, classes, functions, and variables
        self.imports = []
        self.classes = []
        self.functions = []
        self.variables = []
        
    def visit_Import(self, node):
        # Handle 'import ...' statements
        for name in node.names:
            self.imports.append({
                "type": "import",
                "name": name.name,
                "alias": name.asname
            })
        self.generic_visit(node)
        
    def visit_ImportFrom(self, node):
        # Handle 'from ... import ...' statements
        module = node.module
        for name in node.names:
            self.imports.append({
                "type": "from_import",
                "module": module,
                "name": name.name,
                "alias": name.asname
            })
        self.generic_visit(node)
        
    def visit_ClassDef(self, node):
        # Handle class definitions
        class_info = {
            "name": node.name,
            "bases": [self._get_name(base) for base in node.bases],
            "decorators": self._extract_decorators(node),
            "methods": [],
            "class_variables": []
        }

        # Extract triple-quoted string literal as docstring/comment if present
        if (
            node.body
            and isinstance(node.body[0], ast.Expr)
            and isinstance(node.body[0].value, ast.Constant)
            and isinstance(node.body[0].value.value, str)
        ):
            class_info["comment"] = node.body[0].value.value

        # Extract methods and class variables from the class body
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                method_info = self._extract_function_info(item)
                class_info["methods"].append(method_info)
            elif isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        class_info["class_variables"].append({
                            "name": target.id,
                            "value": self._get_value(item.value)
                        })

        self.classes.append(class_info)
        self.generic_visit(node)
        
    def visit_FunctionDef(self, node):
        # Only add top-level functions (not methods)
        for ancestor in self.ancestors:
            if isinstance(ancestor, ast.ClassDef):
                return

        func_info = self._extract_function_info(node)

        # Extract triple-quoted string literal as docstring/comment if present
        if (
            node.body
            and isinstance(node.body[0], ast.Expr)
            and isinstance(node.body[0].value, ast.Constant)
            and isinstance(node.body[0].value.value, str)
        ):
            func_info["comment"] = node.body[0].value.value

        self.functions.append(func_info)
        self.generic_visit(node)
        
    def visit_AsyncFunctionDef(self, node):
        # Handle async functions similarly to regular functions
        for ancestor in self.ancestors:
            if isinstance(ancestor, ast.ClassDef):
                return
                
        func_info = self._extract_function_info(node, is_async=True)
        self.functions.append(func_info)
        self.generic_visit(node)
        
    def visit_Assign(self, node):
        # Only capture module-level variables (not inside functions/classes)
        for ancestor in self.ancestors:
            if isinstance(ancestor, (ast.FunctionDef, ast.ClassDef)):
                return
                
        for target in node.targets:
            if isinstance(target, ast.Name):
                self.variables.append({
                    "name": target.id,
                    "value": self._get_value(node.value)
                })
        self.generic_visit(node)
        
    def _extract_function_info(self, node, is_async=False):
        # Extract function/method information
        func_info = {
            "name": node.name,
            "decorators": self._extract_decorators(node),
            "args": self._extract_arguments(node.args),
            "is_async": is_async
        }
        # Extract triple-quoted string literal as docstring/comment if present
        if (
            node.body
            and isinstance(node.body[0], ast.Expr)
            and isinstance(node.body[0].value, ast.Constant)
            and isinstance(node.body[0].value.value, str)
        ):
            func_info["comment"] = node.body[0].value.value
        return func_info
        
    def _extract_decorators(self, node):
        # Extract decorator names from a node
        decorators = []
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name):
                decorators.append(decorator.id)
            elif isinstance(decorator, ast.Call):
                if isinstance(decorator.func, ast.Name):
                    decorators.append(decorator.func.id)
        return decorators
        
    def _extract_arguments(self, args):
        # Extract argument information for a function/method
        result = []
        
        # Handle positional args
        for arg in args.args:
            arg_info = {"name": arg.arg, "type": "positional"}
            if arg.annotation:
                arg_info["annotation"] = self._get_name(arg.annotation)
            result.append(arg_info)
            
        # Handle *args
        if args.vararg:
            result.append({
                "name": args.vararg.arg,
                "type": "vararg"
            })
            
        # Handle keyword-only args
        for arg in args.kwonlyargs:
            arg_info = {"name": arg.arg, "type": "keyword_only"}
            if arg.annotation:
                arg_info["annotation"] = self._get_name(arg.annotation)
            result.append(arg_info)
            
        # Handle **kwargs
        if args.kwarg:
            result.append({
                "name": args.kwarg.arg,
                "type": "kwarg"
            })
            
        return result
        
    def _get_name(self, node):
        # Get a string representation of a node's name
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        elif isinstance(node, ast.Subscript):
            return f"{self._get_name(node.value)}[{self._get_name(node.slice)}]"
        elif isinstance(node, ast.Constant):
            return str(node.value)
        return "unknown"
        
    def _get_value(self, node):
        # Get a string representation of a node's value
        if isinstance(node, ast.Constant):
            return str(node.value)
        elif isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.List):
            return "[...]"
        elif isinstance(node, ast.Dict):
            return "{...}"
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                return f"{node.func.id}(...)"
            elif isinstance(node.func, ast.Attribute):
                return f"{self._get_name(node.func.value)}.{node.func.attr}(...)"
        return "..."
        
    def generic_visit(self, node):
        # Track ancestors for context (e.g., to distinguish top-level functions)
        if not hasattr(self, 'ancestors'):
            self.ancestors = []
        self.ancestors.append(node)
        super().generic_visit(node)
        self.ancestors.pop()

# Main function to parse a Python file and return structured info
def parse_python_file(filepath, include_code=False):
    import base64

    # Read the source code from the file
    with open(filepath, "r", encoding="utf-8") as f:
        source = f.read()

    # Parse the source code into an AST
    tree = ast.parse(source)
    visitor = CodeVisitor()
    visitor.visit(tree)

    def get_code_b64(node):
        # Try to get the code for the node using lineno/end_lineno
        if hasattr(node, "lineno") and hasattr(node, "end_lineno"):
            lines = source.splitlines(keepends=True)
            code = "".join(lines[node.lineno - 1: node.end_lineno])
            return base64.b64encode(code.encode("utf-8")).decode("ascii")
        return None

    # Deep copy and add code to each class/function/method if requested
    classes = []
    for cls in getattr(visitor, "classes", []):
        cls_copy = dict(cls)
        if include_code:
            # Find the ast.ClassDef node for this class
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef) and node.name == cls["name"]:
                    cls_copy["code"] = get_code_b64(node)
                    break
        # Add code to methods
        methods = []
        for method in cls.get("methods", []):
            method_copy = dict(method)
            if include_code:
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef) and node.name == method["name"]:
                        # Check if this function is inside the class
                        if hasattr(node, "parent") and isinstance(node.parent, ast.ClassDef) and node.parent.name == cls["name"]:
                            method_copy["code"] = get_code_b64(node)
                            break
                        # Fallback: if only one method with this name in the class, assign code
                        elif node in getattr(node, "parent_body", []):
                            method_copy["code"] = get_code_b64(node)
                            break
            methods.append(method_copy)
        cls_copy["methods"] = methods
        classes.append(cls_copy)

    # Add code to top-level functions
    functions = []
    for func in getattr(visitor, "functions", []):
        func_copy = dict(func)
        if include_code:
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == func["name"]:
                    # Only top-level functions
                    if not hasattr(node, "parent") or not isinstance(node.parent, ast.ClassDef):
                        func_copy["code"] = get_code_b64(node)
                        break
        functions.append(func_copy)

    # Add code to top-level variables (assignments)
    variables = []
    for var in getattr(visitor, "variables", []):
        var_copy = dict(var)
        # Not adding code for variables (could be added if needed)
        variables.append(var_copy)

    # Patch AST nodes to have parent references for class/method code extraction
    def set_parents(node, parent=None):
        # Recursively set parent references for all AST nodes
        for child in ast.iter_child_nodes(node):
            child.parent = parent
            if hasattr(parent, "body") and isinstance(parent.body, list):
                child.parent_body = parent.body
            set_parents(child, child)
    set_parents(tree)

    return {
        "meta": {
            "file": os.path.basename(filepath),
            "path": os.path.abspath(filepath),
            "python_version": platform.python_version()
        },
        "imports": getattr(visitor, "imports", []),
        "classes": classes,
        "functions": functions,
        "variables": variables
    }
