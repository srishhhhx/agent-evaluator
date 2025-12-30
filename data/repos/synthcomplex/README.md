# Synthetic Complexities Demo Repo

This synthetic repository is designed to demonstrate the final complexity patterns targeted by the RepoAnalyzer:

- **Circular Import**: `circular_a.py` and `circular_b.py` import each other.
- **High Cyclomatic Complexity**: `high_complex.py` contains functions with deep nesting and branching.
- **Implicit State**: `implicit_state.py` demonstrates use of the `global` keyword and mutable module-level state (singletons, caches).
- **Overloaded APIs**: `overloaded_api.py` contains functions with too many parameters or too much branching logic.

Each pattern is implemented in its own file below. See each file's docstring for details.

## Structure

```
synthcomplex/
  README.md            # This file
  circular_a.py        # Circular import A → B
  circular_b.py        # Circular import B → A
  high_complex.py      # High cyclomatic complexity functions
  implicit_state.py    # Global and module-level mutable state
  overloaded_api.py    # Functions with too many parameters or branches
```
