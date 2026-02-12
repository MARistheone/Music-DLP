"""
Find Missing Methods in Codebase

Analyzes Python files to find method calls that don't have corresponding definitions.
Helps identify AttributeError risks.

Usage:
    python find_missing_methods.py
"""

import ast
import os
from pathlib import Path
from collections import defaultdict


class MethodAnalyzer(ast.NodeVisitor):
    """Analyze method calls and definitions in AST."""

    def __init__(self):
        self.method_calls = defaultdict(set)  # {class_name: {method_names}}
        self.method_definitions = defaultdict(set)  # {class_name: {method_names}}
        self.current_class = None

    def visit_ClassDef(self, node):
        """Track current class being analyzed."""
        old_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = old_class

    def visit_FunctionDef(self, node):
        """Record method definitions."""
        if self.current_class:
            self.method_definitions[self.current_class].add(node.name)
        self.generic_visit(node)

    def visit_Call(self, node):
        """Record method calls."""
        if isinstance(node.func, ast.Attribute):
            method_name = node.func.attr

            # Try to determine the class
            if isinstance(node.func.value, ast.Name):
                if node.func.value.id == 'self' and self.current_class:
                    self.method_calls[self.current_class].add(method_name)
                elif node.func.value.id in ['db', 'database']:
                    self.method_calls['Database'].add(method_name)
                elif node.func.value.id in ['config']:
                    self.method_calls['ConfigManager'].add(method_name)
                elif node.func.value.id in ['logger']:
                    self.method_calls['Logger'].add(method_name)

        self.generic_visit(node)


def analyze_file(file_path):
    """Analyze a single Python file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read(), filename=str(file_path))

        analyzer = MethodAnalyzer()
        analyzer.visit(tree)

        return analyzer.method_calls, analyzer.method_definitions

    except Exception as e:
        print(f"Error analyzing {file_path}: {e}")
        return None, None


def main():
    """Main execution."""
    print("=" * 80)
    print("Music DLP - Missing Methods Analysis")
    print("=" * 80)

    # Aggregate results across all files
    all_calls = defaultdict(set)
    all_definitions = defaultdict(set)

    # Analyze all Python files
    python_files = []
    for pattern in ['gui/**/*.py', 'core/**/*.py', 'downloaders/**/*.py',
                    'ai/**/*.py', 'converters/**/*.py']:
        python_files.extend(Path('.').glob(pattern))

    print(f"\nAnalyzing {len(python_files)} files...\n")

    for py_file in python_files:
        calls, definitions = analyze_file(py_file)
        if calls and definitions:
            for class_name, methods in calls.items():
                all_calls[class_name].update(methods)
            for class_name, methods in definitions.items():
                all_definitions[class_name].update(methods)

    # Find missing methods
    print("\n" + "=" * 80)
    print("MISSING METHODS BY CLASS")
    print("=" * 80)

    has_missing = False

    for class_name in sorted(all_calls.keys()):
        called_methods = all_calls[class_name]
        defined_methods = all_definitions.get(class_name, set())
        missing_methods = called_methods - defined_methods

        # Filter out common inherited/built-in methods
        ignored = {'__init__', '__str__', '__repr__', 'close', 'commit',
                   'fetchone', 'fetchall', 'execute', 'cursor'}
        missing_methods = {m for m in missing_methods if m not in ignored}

        if missing_methods:
            has_missing = True
            print(f"\n{class_name}:")
            print(f"  Called:  {len(called_methods)} methods")
            print(f"  Defined: {len(defined_methods)} methods")
            print(f"  MISSING: {len(missing_methods)} methods")
            print(f"  Missing methods:")
            for method in sorted(missing_methods):
                print(f"    - {method}()")

    if not has_missing:
        print("\n✅ No missing methods found!")
    else:
        print("\n" + "=" * 80)
        print("RECOMMENDATION")
        print("=" * 80)
        print("\nImplement the missing methods above to fix AttributeError exceptions.")
        print("\nFor each missing method, add a stub in the appropriate class:")
        print("""
def missing_method(self, *args, **kwargs):
    '''TODO: Implement this method.'''
    raise NotImplementedError('missing_method not yet implemented')
""")

    # Also check for common patterns
    print("\n" + "=" * 80)
    print("COMMON PATTERNS TO CHECK MANUALLY")
    print("=" * 80)

    print("\n1. Settings Dialog Attributes:")
    print("   Search for: self.\\w+_entry, self.\\w+_var")
    print("   Verify all widgets are created in __init__ or _create_widgets()")

    print("\n2. Database Methods:")
    print("   Search for: db.delete_*, db.update_*, db.get_*")
    print("   Verify all CRUD operations are implemented")

    print("\n3. GUI Component Methods:")
    print("   Search for: self.refresh, self._on_\\w+, self.get_*")
    print("   Verify all event handlers and refresh methods exist")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
