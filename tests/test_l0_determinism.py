"""A-9: determinism and purity (SPEC-L0 §4, §5)."""
import ast
import os
import subprocess
import sys

from l0_helpers import ROOT, require_layer0, uscc_2025_inputs

layer0 = require_layer0()

FORBIDDEN_MODULES = {"os", "io", "sys", "pathlib", "socket", "subprocess", "urllib", "http", "shutil", "tempfile",
                     "random", "time", "glob", "json", "logging", "threading", "multiprocessing"}
FORBIDDEN_CALLS = {"open", "print", "input", "eval", "exec", "__import__", "breakpoint"}
FORBIDDEN_ATTRIBUTES = {"now", "today", "utcnow"}
SCRIPT = ("import layer0, l0_helpers\n"
          "period, lists, tournaments, games = l0_helpers.uscc_2025_inputs(layer0)\n"
          "print(repr(layer0.next_list(period, lists, tournaments, games)))\n")


def run_with_hash_seed(seed: str) -> bytes:
    env = dict(os.environ, PYTHONHASHSEED=seed, PYTHONPATH=os.pathsep.join([str(ROOT / "src"), str(ROOT / "tests")]))
    return subprocess.run([sys.executable, "-c", SCRIPT], cwd=ROOT, env=env, capture_output=True, check=True).stdout


def test_identical_output_under_different_hash_seeds():
    first = run_with_hash_seed("0")
    assert first.startswith(b"NextList(")
    assert run_with_hash_seed("12345") == first == run_with_hash_seed("random")


def test_input_order_does_not_matter():
    period, lists, tournaments, games = uscc_2025_inputs(layer0)
    assert layer0.next_list(period, lists, tournaments, list(reversed(games))) == \
        layer0.next_list(period, lists, tournaments, games)


def test_the_engine_performs_no_io():
    files = sorted((ROOT / "src" / "layer0").glob("*.py"))
    assert files
    for f in files:
        tree = ast.parse(f.read_text(encoding="utf-8"), filename=str(f))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                assert not {a.name.split(".")[0] for a in node.names} & FORBIDDEN_MODULES, f
            elif isinstance(node, ast.ImportFrom):
                assert (node.module or "").split(".")[0] not in FORBIDDEN_MODULES, f
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    assert node.func.id not in FORBIDDEN_CALLS, (f, node.func.id)
                elif isinstance(node.func, ast.Attribute):
                    assert node.func.attr not in FORBIDDEN_ATTRIBUTES, (f, node.func.attr)
