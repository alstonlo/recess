# Recess

This tool adds a (line) break after class (headers).

I have been enjoying using `ruff` as a formatter and linter, but it collapses the lines between the class header and the first method or class attribute, if no class docstring is specified. This removes the aesthetic symmetric spacing around class constructs:

```python
class A:

    def __init__(self):
        pass

    def f(self):
        pass

# After ruff format

class A:
    def __init__(self):
        pass

    def f(self):
        pass
```

It does not look like `ruff` plans to support customization of this behavior any time soon, so I have vibe-coded this post-hoc patch.

## Installation

Using pip:
```
pip install git+https://github.com/alstonlo/recess.git
```

Using uv:
```
uv tool install git+https://github.com/alstonlo/recess.git
```

Using pixi:
```
pixi add --pypi git+https://github.com/alstonlo/recess.git
```

## Usage

Format files or directories in-place:
```
recess src/
recess file.py other.py
```

Check without modifying (exits 1 if any file would change):
```
recess --check src/
```

Print a unified diff without writing:
```
recess --diff src/
```

Read from stdin, write to stdout:
```
cat file.py | recess -
```

## VS Code Integration

VS Code's [Custom Local Formatters](https://code.visualstudio.com/docs/editor/custom-layout#_custom-local-formatters) feature lets you pipe a file through a shell command on save. You can chain `ruff` and `recess` together so that linting, formatting, and the blank-line fix all happen in one pass:

```json
// .vscode/settings.json
{
    "customLocalFormatters.formatters": [
        {
            "command": "ruff check --fix - | ruff format - | recess -",
            "languages": ["python"]
        }
    ]
}
```