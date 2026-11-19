"""Bouw of ververs de schone `student`-branch vanuit `JRNDgrt` zonder merge-conflicten.

Gebruikt een tijdelijke Git-index zodat je werkmap (`gegevens/werk/`, open bestanden)
volledig ongemoeid blijft. De commit op `student` krijgt de huidige `student`- of
`main`-branch als parent en neemt de volledige bestandsboom van `JRNDgrt` over,
zonder `docent/` en zonder proefinleverbestanden (`gegevens/inlevering/*.json`,
`gegevenswerkca.crt`). Daardoor blijft `main` altijd zonder merge-conflict
fast-forward bij te werken.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

WEGLATEN_PADEN = [
    "docent",
    "gegevenswerkca.crt",
]


def git(*args: str, env: dict[str, str] | None = None, check: bool = True) -> str:
    res = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
    )
    if check and res.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} faalde:\n{res.stderr.strip()}")
    return res.stdout.strip()


def ref_bestaat(ref: str) -> bool:
    res = subprocess.run(
        ["git", "rev-parse", "--verify", "--quiet", ref],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    return res.returncode == 0


def maak_student_commit(bron_ref: str, doel_branch: str, basis_branch: str) -> str:
    if not ref_bestaat(bron_ref):
        raise RuntimeError(f"Bronbranch '{bron_ref}' bestaat niet.")
    if not ref_bestaat(basis_branch):
        raise RuntimeError(f"Basisbranch '{basis_branch}' bestaat niet.")

    parent_ref = doel_branch if ref_bestaat(doel_branch) else basis_branch
    # Controleer dat parent_ref afstamt van of gelijk is aan basis_branch
    is_anc = subprocess.run(
        ["git", "merge-base", "--is-ancestor", basis_branch, parent_ref],
        cwd=ROOT,
    )
    if is_anc.returncode != 0:
        parent_ref = basis_branch

    with tempfile.TemporaryDirectory() as tmp:
        index_pad = Path(tmp) / "student.index"
        env = dict(os.environ, GIT_INDEX_FILE=str(index_pad))

        git("read-tree", bron_ref, env=env)
        inlever_jsons = [
            p
            for p in git("ls-files", "--", "gegevens/inlevering/*.json", env=env).splitlines()
            if p
        ]
        te_verwijderen = WEGLATEN_PADEN + inlever_jsons
        git("rm", "-r", "--cached", "-q", "--ignore-unmatch", "--", *te_verwijderen, env=env)

        boom = git("write-tree", env=env)

        # Controleer dat niets uit docent/ of inlevering/*.json overbleef
        overgebleven_docent = git("ls-tree", "-r", "--name-only", boom, "--", "docent", env=env)
        if overgebleven_docent:
            raise AssertionError(f"docent/ nog aanwezig in boom: {overgebleven_docent}")
        overgebleven_json = git(
            "ls-tree", "-r", "--name-only", boom, "--", "gegevens/inlevering/*.json", env=env
        )
        if overgebleven_json:
            raise AssertionError(f"Proef-JSON nog aanwezig in boom: {overgebleven_json}")

        huidige_boom = git("rev-parse", f"{parent_ref}^{{tree}}")
        if boom == huidige_boom and ref_bestaat(doel_branch):
            print(f"Geen wijzigingen: '{doel_branch}' is al gelijk aan de schone snapshot van '{bron_ref}'.")
            return git("rev-parse", doel_branch)

        bron_sha = git("rev-parse", "--short", bron_ref)
        bericht = f"Werk studentenversie bij vanuit {bron_ref} ({bron_sha})"
        commit_sha = git("commit-tree", boom, "-p", parent_ref, "-m", bericht)
        git("branch", "-f", doel_branch, commit_sha)
        print(f"OK '{doel_branch}' bijgewerkt naar {commit_sha[:7]} (parent: {parent_ref}).")
        return commit_sha


def werk_main_bij(doel_branch: str, basis_branch: str) -> None:
    is_anc = subprocess.run(
        ["git", "merge-base", "--is-ancestor", basis_branch, doel_branch],
        cwd=ROOT,
    )
    if is_anc.returncode != 0:
        raise RuntimeError(f"'{basis_branch}' kan niet fast-forward naar '{doel_branch}'.")
    huidige_branch = git("branch", "--show-current")
    if huidige_branch == basis_branch:
        git("merge", "--ff-only", doel_branch)
    else:
        sha = git("rev-parse", doel_branch)
        git("branch", "-f", basis_branch, sha)
    print(f"OK '{basis_branch}' fast-forward bijgewerkt naar {doel_branch}.")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--bron", default="JRNDgrt", help="Docentbranch (standaard: JRNDgrt)")
    p.add_argument("--doel", default="studentenversie", help="Studentenbranch (standaard: studentenversie)")
    p.add_argument("--main", default="main", help="Basisbranch (standaard: main)")
    p.add_argument(
        "--werk-main-bij",
        action="store_true",
        help="Zet ook main via fast-forward op de nieuwe student-commit.",
    )
    args = p.parse_args()

    maak_student_commit(args.bron, args.doel, args.main)
    if args.werk_main_bij:
        werk_main_bij(args.doel, args.main)


if __name__ == "__main__":
    main()
