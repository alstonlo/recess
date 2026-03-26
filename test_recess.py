import subprocess
import sys
import textwrap
from pathlib import Path

from recess import fix_content

_RECESS = str(Path(__file__).resolve().parent / "recess.py")


def _dedent(s: str) -> str:
    """Dedent and strip leading/trailing blank lines."""
    return textwrap.dedent(s).strip() + "\n"


# ─── Tests: should INSERT blank line ─────────────────────────────────────


def test_basic_class_def():
    before = _dedent("""
        class Foo:
            def __init__(self):
                pass
    """)
    after = _dedent("""
        class Foo:

            def __init__(self):
                pass
    """)
    assert fix_content(before) == after


def test_class_with_inheritance():
    before = _dedent("""
        class Child(Parent, Mixin):
            def __init__(self):
                pass
    """)
    after = _dedent("""
        class Child(Parent, Mixin):

            def __init__(self):
                pass
    """)
    assert fix_content(before) == after


def test_class_with_decorator():
    before = _dedent("""
        class Foo:
            @staticmethod
            def create():
                pass
    """)
    after = _dedent("""
        class Foo:

            @staticmethod
            def create():
                pass
    """)
    assert fix_content(before) == after


def test_class_with_async_def():
    before = _dedent("""
        class Foo:
            async def run(self):
                pass
    """)
    after = _dedent("""
        class Foo:

            async def run(self):
                pass
    """)
    assert fix_content(before) == after


def test_class_with_nested_class():
    before = _dedent("""
        class Outer:
            class Inner:
                pass
    """)
    after = _dedent("""
        class Outer:

            class Inner:
                pass
    """)
    assert fix_content(before) == after


def test_attrs_then_def():
    """The attr: int case."""
    before = _dedent("""
        class User:
            name: str
            age: int
            def __init__(self):
                pass
    """)
    after = _dedent("""
        class User:

            name: str
            age: int

            def __init__(self):
                pass
    """)
    assert fix_content(before) == after


def test_assignment_attrs_then_def():
    before = _dedent("""
        class Config:
            x = 10
            y = 20
            def method(self):
                pass
    """)
    after = _dedent("""
        class Config:

            x = 10
            y = 20

            def method(self):
                pass
    """)
    assert fix_content(before) == after


def test_attrs_then_decorated_def():
    before = _dedent("""
        class Foo:
            x: int
            y: float = 3.14
            @property
            def value(self):
                return self.x
    """)
    after = _dedent("""
        class Foo:

            x: int
            y: float = 3.14

            @property
            def value(self):
                return self.x
    """)
    assert fix_content(before) == after


def test_class_with_comment():
    before = _dedent("""
        class Foo:  # some comment
            def __init__(self):
                pass
    """)
    after = _dedent("""
        class Foo:  # some comment

            def __init__(self):
                pass
    """)
    assert fix_content(before) == after


def test_deeply_nested():
    before = _dedent("""
        class L1:
            class L2:
                class L3:
                    def deep(self):
                        pass
    """)
    after = _dedent("""
        class L1:

            class L2:

                class L3:

                    def deep(self):
                        pass
    """)
    assert fix_content(before) == after


def test_multiple_classes():
    before = _dedent("""
        class A:
            def a(self):
                pass


        class B:
            def b(self):
                pass
    """)
    after = _dedent("""
        class A:

            def a(self):
                pass


        class B:

            def b(self):
                pass
    """)
    assert fix_content(after) == after  # idempotent check too
    assert fix_content(before) == after


def test_mixed_attrs_and_type_annotations():
    before = _dedent("""
        class Model:
            x: int = 0
            name: str
            items: list[str] = []
            DEBUG = False
            def process(self):
                pass
    """)
    after = _dedent("""
        class Model:

            x: int = 0
            name: str
            items: list[str] = []
            DEBUG = False

            def process(self):
                pass
    """)
    assert fix_content(before) == after


def test_enum_members():
    before = _dedent("""
        class Color(Enum):
            RED = 1
            GREEN = 2
            BLUE = 3
            def describe(self):
                return self.name.lower()
    """)
    after = _dedent("""
        class Color(Enum):

            RED = 1
            GREEN = 2
            BLUE = 3

            def describe(self):
                return self.name.lower()
    """)
    assert fix_content(before) == after


def test_enum_only():
    source = _dedent("""
        class Color(Enum):

            RED = 1
            GREEN = 2
            BLUE = 3
    """)
    assert fix_content(source) == source


# ─── Tests: should NOT insert blank line ─────────────────────────────────


def test_class_with_docstring():
    source = _dedent("""
        class Foo:
            \"\"\"Docstring.\"\"\"

            def __init__(self):
                pass
    """)
    assert fix_content(source) == source


def test_already_has_blank_line():
    source = _dedent("""
        class Foo:

            def __init__(self):
                pass
    """)
    assert fix_content(source) == source


def test_attrs_already_spaced():
    source = _dedent("""
        class Foo:

            x: int
            y: str

            def __init__(self):
                pass
    """)
    assert fix_content(source) == source


def test_class_only_attrs():
    source = _dedent("""
        class Foo:

            x: int = 1
            y: int = 2
    """)
    assert fix_content(source) == source


def test_empty_class():
    source = _dedent("""
        class Foo:
            pass
    """)
    assert fix_content(source) == source


def test_no_classes():
    source = _dedent("""
        def foo():
            pass

        x = 1
    """)
    assert fix_content(source) == source


def test_class_with_only_docstring():
    source = _dedent("""
        class Foo:
            \"\"\"Just a docstring.\"\"\"
    """)
    assert fix_content(source) == source


# ─── Tests: idempotency ──────────────────────────────────────────────────


def test_idempotent_basic():
    source = _dedent("""
        class Foo:
            def __init__(self):
                pass
    """)
    once = fix_content(source)
    twice = fix_content(once)
    assert once == twice


def test_idempotent_attrs():
    source = _dedent("""
        class Foo:
            x: int
            def __init__(self):
                pass
    """)
    once = fix_content(source)
    twice = fix_content(once)
    assert once == twice


# ─── Tests: CLI ──────────────────────────────────────────────────────────


def test_cli_check_mode(tmp_path: Path):
    f = tmp_path / "test.py"
    f.write_text("class Foo:\n    def bar(self):\n        pass\n")
    result = subprocess.run(
        [sys.executable, _RECESS, "--check", str(f)],
        capture_output=True,
    )
    assert result.returncode == 1


def test_cli_check_clean(tmp_path: Path):
    f = tmp_path / "test.py"
    f.write_text("class Foo:\n\n    def bar(self):\n        pass\n")
    result = subprocess.run(
        [sys.executable, _RECESS, "--check", str(f)],
        capture_output=True,
    )
    assert result.returncode == 0


def test_cli_inplace(tmp_path: Path):
    f = tmp_path / "test.py"
    f.write_text("class Foo:\n    def bar(self):\n        pass\n")
    subprocess.run([sys.executable, _RECESS, str(f)])
    assert "\n\n    def bar" in f.read_text()


def test_cli_stdin():
    result = subprocess.run(
        [sys.executable, _RECESS, "-"],
        input="class Foo:\n    def bar(self):\n        pass\n",
        capture_output=True,
        text=True,
    )
    assert "\n\n    def bar" in result.stdout
