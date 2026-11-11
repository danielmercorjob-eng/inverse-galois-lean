#!/usr/bin/env python3
"""Compile the Lean definitions with a Mathlib Lake project."""

import argparse
import os
import re
from pathlib import Path
import subprocess
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mathlib-project",required=True,type=Path)
    parser.add_argument("--audit-axioms",action="store_true",
                        help="reject axioms other than Lean's standard logical axioms")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    project = args.mathlib_project.expanduser().resolve()
    # Read only tool paths. Do not copy or print credentials from the environment.
    lean = subprocess.check_output(["lake","env","which","lean"],cwd=project,text=True).strip()
    search = subprocess.check_output(["lake","env","printenv","LEAN_PATH"],cwd=project,text=True).strip()
    with tempfile.TemporaryDirectory(prefix="invgal-lean-") as tmp:
        env = dict(os.environ,LEAN_PATH=tmp+os.pathsep+search)
        for module in ("GroupCohomologyInvariants","FiniteGroupInvariants","CohomologyInvariants"):
            subprocess.run([lean,"-DwarningAsError=true","-R",str(root),"-o",str(Path(tmp)/(module+".olean")),
                            str(root/(module+".lean"))],cwd=project,env=env,check=True)
            print(f"Checked {module}.lean",flush=True)
        if args.audit_axioms:
            declarations = []
            for module, namespace in (("GroupCohomologyInvariants", "FiniteGroupCohomology"),
                                      ("FiniteGroupInvariants", "FiniteGroupInvariants"),
                                      ("CohomologyInvariants", "FiniteGroupInvariants")):
                names = re.findall(r"^(?:def|abbrev|instance|theorem|structure)\s+(\w+)",
                                   (root/(module+".lean")).read_text(), re.MULTILINE)
                declarations.extend(namespace+"."+name for name in names)
            audit = Path(tmp)/"Audit.lean"
            audit.write_text("import CohomologyInvariants\n" +
                             "\n".join("#print axioms "+name for name in declarations)+"\n")
            result = subprocess.run([lean,"-DwarningAsError=true","-R",tmp,str(audit)],
                                    cwd=project,env=env,check=True,capture_output=True,text=True)
            lists = re.findall(r"depends on axioms: \[([^]]*)\]",result.stdout,re.DOTALL)
            axioms = {name.strip() for names in lists for name in names.split(",") if name.strip()}
            extra = axioms - {"propext", "Classical.choice", "Quot.sound"}
            if extra:
                raise RuntimeError("unexpected axioms: "+", ".join(sorted(extra)))
            print(f"Audited {len(declarations)} declarations: standard logical axioms only",flush=True)


if __name__ == "__main__":
    main()
