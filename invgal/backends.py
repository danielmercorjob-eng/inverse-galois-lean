"""Checked subprocess interface for exact GAP/HAP computations."""

import json
import math
import os
import re
import signal
import subprocess
from fractions import Fraction
from pathlib import Path

from .group import group_order, identity


class InvariantError(RuntimeError):
    """A backend, its dependencies, or a mathematical precondition failed."""


class ResourceLimit(InvariantError):
    """A requested exact calculation exceeded an explicit resource bound."""


def checked_perms(group):
    perms = group.perms or [identity(group.degree)]
    if any(sorted(g) != list(range(group.degree)) for g in perms):
        raise ValueError("invalid permutation generators")
    order = group_order(perms)
    if order != group.order:
        raise ValueError(f"{group.name}: actual order {order}, declared {group.order}")
    return perms


def positive_int(n, name, minimum=1):
    if type(n) is not int or n < minimum:
        raise ValueError(f"{name} must be an integer >= {minimum}")
    return n


def gap_literal(value):
    """Serialize data, never executable expressions, to a GAP literal."""
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, int):
        return str(value)
    if isinstance(value, Fraction):
        return f"({value.numerator}/{value.denominator})"
    if isinstance(value, str):
        return '"' + value.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n') + '"'
    if isinstance(value, (tuple, list)):
        return "[" + ",".join(map(gap_literal, value)) + "]"
    if isinstance(value, dict):
        if any(not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", k) for k in value):
            raise ValueError("invalid GAP record key")
        return "rec(" + ",".join(k + ":=" + gap_literal(v) for k, v in value.items()) + ")"
    raise TypeError(f"cannot serialize {type(value).__name__} to GAP")


def run_json(command, *, source=None, payload=None, timeout=300, env=None):
    if not isinstance(timeout, (float, int)) or not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("timeout must be positive and finite")
    try:
        proc = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, text=True, env=env,
                                start_new_session=True)
        try:
            stdout, stderr = proc.communicate(source if payload is None else json.dumps(payload),
                                               timeout=timeout)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGKILL)
            proc.communicate()
            raise
    except OSError as e:
        raise InvariantError(f"cannot execute {command[0]!r}: {e}") from e
    except subprocess.TimeoutExpired as e:
        raise ResourceLimit(f"{command[0]} exceeded {timeout} seconds; no result certified") from e
    begin, end = "INVGAL_JSON_BEGIN\n", "\nINVGAL_JSON_END"
    if proc.returncode or stdout.count(begin) != 1 or end not in stdout:
        raise InvariantError(f"backend failed (exit {proc.returncode}):\n"
                             + (stdout + "\n" + stderr)[-6000:])
    try:
        return json.loads(stdout.split(begin)[1].split(end)[0])
    except json.JSONDecodeError as e:
        raise InvariantError("backend returned invalid JSON") from e


def gap_compute(group, operation, *, gap="gap", timeout=300, **parameters):
    perms = checked_perms(group)
    helper = Path(__file__).with_name("invariants.g")
    source = ('SizeScreen([1000000,1000000]);;\n'
              'LoadPackage("hap",false);;\n'
              f"Read({gap_literal(str(helper))});;\n"
              f"G:=Group(List({gap_literal([[x+1 for x in g] for g in perms])},PermList));;\n"
              f"if Size(G)<>{group.order} then Error(\"group order mismatch\"); fi;\n"
              f"answer:=IVCompute(G,{group.degree},{gap_literal(operation)},"
              f"{gap_literal(parameters)});;\n"
              'Print("INVGAL_JSON_BEGIN\\n"); IVJson(answer); '
              'Print("\\nINVGAL_JSON_END\\n"); QUIT_GAP(0);\n')
    return run_json([str(gap), "-q", "-b", "-r", "--quitonbreak"], source=source, timeout=timeout)


def abelian_group(invariants):
    """Normalize elementary divisors to invariant factors; 0 denotes a free Z summand."""
    free = invariants.count(0)
    primary = {}
    for n in invariants:
        if type(n) is not int or n < 0:
            raise InvariantError(f"invalid abelian invariant {n!r}")
        if n < 2:
            continue
        q = 2
        while q*q <= n:
            power = 1
            while n % q == 0:
                n //= q
                power *= q
            if power > 1:
                primary.setdefault(q, []).append(power)
            q += 1
        if n > 1:
            primary.setdefault(n, []).append(n)
    length = max(map(len, primary.values()), default=0)
    factors = [1]*length
    for powers in primary.values():
        for i, power in enumerate([1]*(length-len(powers)) + sorted(powers)):
            factors[i] *= power
    return {"free_rank": free, "torsion_invariant_factors": factors}
