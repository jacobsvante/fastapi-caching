import hashlib
import pathlib
from typing import Sequence, Union

import pkg_resources

__all__ = ("files_hash", "installed_packages_hash")


def files_hash(
    *paths: Union[pathlib.Path, str],
    include: Sequence[str] = ("*",),
    digest_size: int = 4,
) -> str:
    """Create a reproducible hash (hex digest) from the file contents of the given paths

    Paths that point to directories will be traversed recursively.

    Mainly useful for cache busting scenarios.

    Args:
        paths: The directory/file paths to extract file contents from
        include:
            The types of files to include in the creation of the hash,
            specified as a list of file extensions.
            Defaults to all files. Example: ["py", "rs"]
        digest_size:
            The amount of bytes to use for the hex digest to return.
            Defaults to 4 which equals 8 characters.

    """
    h = hashlib.blake2b(digest_size=digest_size)

    for path in paths:
        path = pathlib.Path(path)
        if path.is_dir():
            for sub_path in sorted(
                p
                for file_ext in include
                for p in path.rglob(f"*.{file_ext}")
                if p.is_file()
            ):
                h.update(str(sub_path).encode())
                h.update(sub_path.read_bytes())
        elif path.is_file():
            h.update(str(path).encode())
            h.update(path.read_bytes())
        else:
            raise RuntimeError(f"Unsupported path: {path} (does it exist?)")

    return h.hexdigest()


def installed_packages_hash(digest_size: int = 4) -> str:
    """Return a reproducible hash (hex digest) of the installed python packages

    Args:
        digest_size:
            The amount of bytes to use for the hex digest to return.
            Defaults to 4 which equals 8 characters.

    """
    packages = sorted(
        f"{d.project_name}=={d.version}".encode() for d in pkg_resources.working_set
    )
    return hashlib.blake2b(b" ".join(packages), digest_size=digest_size).hexdigest()
