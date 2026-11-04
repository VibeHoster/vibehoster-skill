#!/usr/bin/env python3
"""Create a bounded ZIP of an already-built, public static site."""
import argparse
import os
from pathlib import Path
import stat
import sys
import zipfile

MAX_FILE = 20 * 1024 * 1024
MAX_TOTAL = 100 * 1024 * 1024
MAX_FILES = 2000
ALLOWED = {'.html', '.css', '.js', '.json', '.png', '.jpg', '.jpeg', '.gif', '.webp', '.ico', '.woff', '.woff2'}


def open_relative(root, rel):
    """Open a regular file without following any directory symlinks."""
    directory = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        parts = rel.split('/')
        for component in parts[:-1]:
            next_fd = os.open(component, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=directory)
            os.close(directory)
            directory = next_fd
        return os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
    finally:
        os.close(directory)


def package(root, destination):
    root = root.resolve(strict=True)
    if not root.is_dir():
        raise ValueError('Build path must be a directory')
    destination = destination.absolute()
    if destination.is_relative_to(root) or destination.resolve().is_relative_to(root):
        raise ValueError('Archive must be outside the build directory')
    if destination.exists() or destination.is_symlink():
        raise ValueError('Archive path already exists')
    files, total = [], 0
    def fail_on_walk_error(error):
        raise error
    for current, dirs, names in os.walk(root, followlinks=False, onerror=fail_on_walk_error):
        for name in dirs + names:
            entry = Path(current) / name
            info = entry.lstat()
            rel = entry.relative_to(root).as_posix()
            if (name.startswith('.') or '\\' in rel or len(rel) > 512 or len(name) > 128
                    or any(ord(c) < 32 or ord(c) == 127 for c in rel)):
                raise ValueError(f'Hidden or invalid path: {rel}')
            if stat.S_ISLNK(info.st_mode):
                raise ValueError(f'Symlink is not supported: {rel}')
            if stat.S_ISDIR(info.st_mode):
                continue
            if not stat.S_ISREG(info.st_mode) or entry.suffix.lower() not in ALLOWED:
                raise ValueError(f'Unsupported file: {rel}')
            if info.st_size > MAX_FILE:
                raise ValueError(f'File exceeds 20 MiB: {rel}')
            total += info.st_size
            files.append((entry, rel, info.st_size))
            if total > MAX_TOTAL or len(files) > MAX_FILES:
                raise ValueError('Build exceeds platform size or file-count limit')
    if not any(rel == 'index.html' for _, rel, _ in files):
        raise ValueError('Build must contain index.html at its root')
    if len({name.casefold() for _, name, _ in files}) != len(files):
        raise ValueError('Build contains case-colliding paths')
    try:
        # Exclusive creation prevents accidental overwrite and symlink following.
        fd = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, 'wb') as output, zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as archive:
            for entry, rel, expected in sorted(files, key=lambda item: item[1]):
                # Reject a file swapped for a symlink after the initial scan.
                fd = open_relative(root, rel)
                with os.fdopen(fd, 'rb') as source:
                    info = os.fstat(source.fileno())
                    if not stat.S_ISREG(info.st_mode) or info.st_size != expected:
                        raise ValueError(f'File changed during packaging: {rel}')
                    data = source.read(MAX_FILE + 1)
                    if len(data) != expected:
                        raise ValueError(f'File changed during packaging: {rel}')
                    archive.writestr(rel, data)
        if destination.stat().st_size > MAX_TOTAL:
            raise ValueError('Archive exceeds 100 MiB')
    except Exception:
        # Only remove a file created by this invocation.
        if 'output' in locals():
            destination.unlink(missing_ok=True)
        raise
    return len(files), total


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('build_directory', type=Path)
    parser.add_argument('archive', type=Path)
    args = parser.parse_args()
    try:
        count, size = package(args.build_directory, args.archive)
    except (OSError, ValueError, zipfile.BadZipFile) as exc:
        print(f'Unable to package site: {exc}', file=sys.stderr)
        return 1
    print(f'Prepared {count} files ({size} bytes) in {args.archive}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
