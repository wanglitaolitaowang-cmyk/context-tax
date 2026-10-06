#!/usr/bin/env python3
"""Create-only local skill installer. Python 3.10+, standard library only.

No downloads, config/PATH edits, hooks, accounts or dependency installation.
Run from a trusted extracted distribution. --check compares bundled bytes.
"""
from __future__ import annotations
import argparse
import hashlib
import os
import stat
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / 'skills' / 'context-tax'


def linked(path: Path) -> bool:
    info = path.lstat()
    return stat.S_ISLNK(info.st_mode) or bool(getattr(info, 'st_file_attributes', 0) & 0x400)


def ensure_parents_not_links(path: Path) -> None:
    for parent in [path, *path.parents]:
        if parent.exists() or parent.is_symlink():
            if linked(parent):
                raise ValueError('A destination component is a symlink/reparse point; use a regular local directory.')


def bundle_files() -> list[Path]:
    if not SOURCE.is_dir() or linked(SOURCE):
        raise ValueError('Bundled skill directory is missing or linked.')
    out = []
    for folder, dirs, names in os.walk(SOURCE, followlinks=False):
        dirs[:] = sorted(d for d in dirs if d != '__pycache__')
        for name in dirs:
            if linked(Path(folder) / name):
                raise ValueError('A bundled directory is linked; installation refused.')
        for name in sorted(names):
            if name.endswith(('.pyc', '.pyo')):
                continue
            p = Path(folder) / name
            if linked(p) or not p.is_file():
                raise ValueError('A bundled file is not a regular file; installation refused.')
            out.append(p.relative_to(SOURCE))
    if Path('SKILL.md') not in out or Path('scripts/context_tax.py') not in out:
        raise ValueError('Incomplete skill distribution.')
    return out


def check(destination: Path, files: list[Path]) -> list[str]:
    failures = []
    if not destination.is_dir():
        return ['destination_missing']
    ensure_parents_not_links(destination)
    for rel in files:
        target = destination / rel
        ensure_parents_not_links(target)
        if not target.is_file():
            failures.append(f'missing:{rel.as_posix()}')
        elif hashlib.sha256(target.read_bytes()).digest() != hashlib.sha256((SOURCE / rel).read_bytes()).digest():
            failures.append(f'changed:{rel.as_posix()}')
    return failures


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--target', choices=['codex', 'claude'], default='codex')
    p.add_argument('--dest', type=Path, help='Exact alternative destination directory, ending in context-tax')
    mode = p.add_mutually_exclusive_group()
    mode.add_argument('--dry-run', action='store_true')
    mode.add_argument('--check', action='store_true', help='Read-only check of bundled files; extra local files are not validated')
    args = p.parse_args(argv)
    destination = args.dest or (Path.home() / ('.agents' if args.target == 'codex' else '.claude') / 'skills' / 'context-tax')
    destination = destination.expanduser().absolute()
    try:
        if sys.version_info < (3, 10):
            raise ValueError('Python 3.10 or newer is required.')
        if destination.name != 'context-tax':
            raise ValueError('--dest must be the exact skill folder and end in context-tax.')
        files = bundle_files()
        ensure_parents_not_links(destination)
        if args.check:
            failures = check(destination, files)
            if failures:
                print('CHECK FAILED: ' + '; '.join(failures), file=sys.stderr)
                return 1
            print(f'CHECK OK: {len(files)} bundled files match. Extra local files are not checked.\nDestination: {destination}')
            return 0
        if destination.exists() or destination.is_symlink():
            raise ValueError('Destination already exists; nothing was overwritten. Use --check or choose a fresh destination.')
        if args.dry_run:
            print(f'DRY RUN: would create {len(files)} files in {destination}. No changes made.')
            return 0
        # mkdir is an exclusive reservation; existing directories are never reused.
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.mkdir(exist_ok=False)
        for rel in files:
            target = destination / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open('xb') as stream:
                stream.write((SOURCE / rel).read_bytes())
        failures = check(destination, files)
        if failures:
            raise ValueError('Post-install byte check failed. Installation directory was left for inspection; no automatic deletion.')
        print(f'INSTALLED: {len(files)} verified files in {destination}\nNo agent configuration, PATH or hooks were changed. Host discovery still needs manual verification.')
        return 0
    except (OSError, ValueError) as exc:
        message = str(exc) if isinstance(exc, ValueError) else 'Filesystem operation failed. A partial new directory may remain; inspect it before retrying.'
        print(f'context-tax installer: {message}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
