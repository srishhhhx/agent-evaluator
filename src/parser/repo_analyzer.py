"""Analyzes a Python repository for various types of code complexity.

This module provides the `RepoAnalyzer` class, which scans a given repository
for multiple complexity metrics, and helper functions to format them for other tools.
"""

import ast
import json
import os
import random
from pathlib import Path
from typing import Any, Dict, List

from radon.complexity import cc_visit
from radon.visitors import Function


def _normalize_issue(issue: Dict[str, Any]) -> Dict[str, Any] | None:
    """Converts a raw issue dictionary into a standardized format."""
    issue_type = issue.get('type')
    try:
        if issue_type == 'high_complexity':
            return {
                "type": "high_complexity",
                "file": issue['file'],
                "function": issue['function'],
                "details": {
                    "complexity_score": issue['complexity'],
                    "lineno": issue['lineno'],
                    "end_lineno": None # Radon version support varies
                }
            }
        elif issue_type == 'circular_import':
            return {"type": "circular_import", "file": issue['file_a'], "details": {"imports": [issue['file_a'], issue['file_b']]}}
        elif issue_type == 'implicit_state':
            return {"type": "implicit_state", "file": issue['file'], "details": {"variable": issue['variable'], "line": issue['line'], "state_type": issue['state_type']}}
        elif issue_type == 'overloaded_api':
            return {"type": "overloaded_api", "file": issue['file'], "function": issue['function'], "details": {"line": issue['line'], "parameters": issue['parameters'], "branches": issue['branches']}}
    except KeyError as e:
        print(f"Warning: Could not normalize issue due to missing key: {e}. Issue: {issue}")
    return None

def select_and_normalize_issues(all_issues: List[Dict], repo_name: str, num_to_select: int = 2) -> Dict[str, Any]:
    """Shuffles issues, selects a few, normalizes them, and returns the final payload."""
    if not all_issues:
        return {"repo_name": repo_name, "selected_complexities": []}
    
    num_to_select = min(num_to_select, len(all_issues))
    selected_issues = random.sample(all_issues, num_to_select)
    normalized_complexities = [norm_issue for issue in selected_issues if (norm_issue := _normalize_issue(issue)) is not None]

    print(f"\nSelected {len(normalized_complexities)} complexities for DSPy:")
    for i, norm_issue in enumerate(normalized_complexities):
        target_name = norm_issue.get('function') or norm_issue.get('details', {}).get('variable')
        target = f"{norm_issue['file']}::{target_name}"
        print(f"{i+1}) {norm_issue['type']} → {target}")
    
    return {"repo_name": repo_name, "selected_complexities": normalized_complexities}


class RepoAnalyzer:
    """Scans a Python repository for code complexity metrics."""
    def __init__(self, repo_path: str, debug: bool = False):
        self.repo_path = Path(repo_path).resolve()
        self.debug = debug

    def _get_py_files(self) -> List[Path]:
        return [f for f in self.repo_path.rglob("*.py") if "venv" not in f.parts and "tests" not in f.parts]

    def _resolve_import_path(self, from_path: Path, import_str: str) -> Path | None:
        """Resolves an import string to a file path."""
        try:
            # Simplistic resolution assuming top-level project structure
            parts = import_str.split('.')
            target_path = self.repo_path.joinpath(*parts).with_suffix('.py')
            if target_path.exists():
                return target_path
            # Check for package imports (__init__.py)
            target_path = self.repo_path.joinpath(*parts, '__init__.py')
            if target_path.exists():
                return target_path
        except Exception:
            pass
        return None

    def analyze(self) -> List[Dict[str, Any]]:
        py_files = self._get_py_files()
        
        all_issues = []
        all_issues.extend(self.find_complex_functions(py_files))
        all_issues.extend(self.find_implicit_state(py_files))
        all_issues.extend(self.find_overloaded_apis(py_files))
        all_issues.extend(self.find_circular_imports(py_files))
        
        print(f"Found {len(all_issues)} total complexity points.")
        return all_issues
        
    def find_circular_imports(self, py_files: List[Path]) -> List[Dict[str, Any]]:
        imports_map = {}
        for file_path in py_files:
            relative_path = str(file_path.relative_to(self.repo_path))
            imports_map[relative_path] = []
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    tree = ast.parse(f.read(), filename=str(file_path))
                for node in ast.walk(tree):
                    module_str = None
                    if isinstance(node, ast.Import) and node.names:
                        module_str = node.names[0].name
                    elif isinstance(node, ast.ImportFrom):
                        module_str = node.module
                    
                    if module_str:
                        resolved_path = self._resolve_import_path(file_path, module_str)
                        if resolved_path:
                             imports_map[relative_path].append(str(resolved_path.relative_to(self.repo_path)))
            except Exception as e:
                if self.debug: print(f"DEBUG: Error parsing imports in {file_path}: {e}")

        circular_imports, checked_pairs = [], set()
        for file_a, imported_files in imports_map.items():
            for file_b in imported_files:
                if file_b in imports_map and file_a in imports_map.get(file_b, []):
                    if (file_a, file_b) not in checked_pairs and (file_b, file_a) not in checked_pairs:
                        circular_imports.append({'type': 'circular_import', 'file_a': file_a, 'file_b': file_b})
                        checked_pairs.add((file_a, file_b))
        return circular_imports
        
    def find_complex_functions(self, py_files: List[Path]) -> List[Dict[str, Any]]:
        complex_functions = []
        for py_file in py_files:
            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    visitors = cc_visit(f.read())
                for visitor in visitors:
                    if isinstance(visitor, Function) and visitor.complexity > 10:
                        complex_functions.append({"type": "high_complexity", "file": str(py_file.relative_to(self.repo_path)), "function": visitor.name, "complexity": visitor.complexity, "lineno": visitor.lineno})
            except Exception: pass
        return complex_functions

    def find_implicit_state(self, py_files: List[Path]) -> List[Dict[str, Any]]:
        implicit_states = []
        for py_file in py_files:
            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    tree = ast.parse(f.read(), filename=str(py_file))
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.Global):
                        for name in node.names:
                            implicit_states.append({"type": "implicit_state", "file": str(py_file.relative_to(self.repo_path)), "variable": name, "line": node.lineno, "state_type": "mutable_global"})
                
                for node in tree.body:
                    if isinstance(node, ast.Assign):
                        if isinstance(node.value, (ast.List, ast.Dict, ast.Set, ast.Call)):
                            for target in node.targets:
                                if isinstance(target, ast.Name) and not target.id.isupper():
                                    implicit_states.append({"type": "implicit_state", "file": str(py_file.relative_to(self.repo_path)), "variable": target.id, "line": node.lineno, "state_type": "module_singleton"})
            except Exception: pass
        return implicit_states

    def find_overloaded_apis(self, py_files: List[Path]) -> List[Dict[str, Any]]:
        overloaded_apis = []
        for py_file in py_files:
            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    tree = ast.parse(f.read(), filename=str(py_file))
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        num_params = len(node.args.args)
                        if any(arg.arg in ['self', 'cls'] for arg in node.args.args):
                            num_params -=1

                        branch_count = sum(1 for body_item in node.body if isinstance(body_item, (ast.If, ast.For, ast.While, ast.Try)))
                        
                        if num_params >= 6 or branch_count >= 5:
                            overloaded_apis.append({"type": "overloaded_api", "file": str(py_file.relative_to(self.repo_path)), "function": node.name, "line": node.lineno, "parameters": num_params, "branches": branch_count})
            except Exception: pass
        return overloaded_apis

if __name__ == "__main__":
    repo_directory = "data/repos/synthcomplex"
    if Path(repo_directory).exists():
        try:
            analyzer = RepoAnalyzer(repo_directory, debug=True)
            raw_issues = analyzer.analyze()
            dspy_payload = select_and_normalize_issues(raw_issues, Path(repo_directory).name)
            
            print("\n--- Final DSPy Payload ---")
            print(json.dumps(dspy_payload, indent=2))
        except Exception as e:
            print(f"An unexpected error occurred: {e}", exc_info=True)
    else:
        print(f"Error: The example repository '{repo_directory}' was not found.")