import argparse
from pathlib import Path
from typing import List, Optional
import re
import requests

RAW_VERSION_RE = re.compile(r'(?P<package>.*)\s*=\s*\"(?P<version>[\^\~\>\=\<\!]?[\d\.\-\w]+)\"')
EXPANDED_VER_RE = re.compile(
    r'(?P<package>.*)\s*=\s*\{(.*)version\s*=\s*\"(?P<version>[\^\~\>\=\<\!]?[\d\.\-\w]+)\"(.*)\}'
)

def parse_args() -> argparse.Namespace:
    """
    This function parses command line arguments using the `argparse` module.

    Args:
        None

    Returns:
        argparse.Namespace: The parsed command line arguments.

    Raises:
        None

    Example:
        ```
        import argparse
        from pathlib import Path

        def parse_args() -> argparse.Namespace:
            parser = argparse.ArgumentParser()
            parser.add_argument(
                "file",
                type=Path,
            )
            parser.add_argument(
                "--section",
                "-s",
                type=str,
                default="tool.poetry.dependencies",
            )
            return parser.parse_args()

        args = parse_args()
        print(args.file)
        print(args.section)
        ```
    """

    
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "file",
        type=Path,
    )
    parser.add_argument(
        "--section",
        "-s",
        type=str,
        default="tool.poetry.dependencies",
    )
    return parser.parse_args()

def get_dependencies(path: Path, section: str) -> List[str]:
    """
    This function parses command line arguments using the `argparse` module.

    Args:
        None

    Returns:
        argparse.Namespace: The parsed command line arguments.

    Raises:
        None

    Example:
        ```
        import argparse
        from pathlib import Path

        def parse_args() -> argparse.Namespace:
            parser = argparse.ArgumentParser()
            parser.add_argument(
                "file",
                type=Path,
            )
            parser.add_argument(
                "--section",
                "-s",
                type=str,
                default="tool.poetry.dependencies",
            )
            return parser.parse_args()

        args = parse_args()
        print(args.file)
        print(args.section)
        ```
    """

    read_file = path.read_text()
    recording = False
    deps = []
    for index, line in enumerate(read_file.splitlines(keepends=False)):
        if line.startswith('[') and line.strip('[]') != section:
            recording = False
            continue
        if line == f"[{section}]":
            recording = True
            continue
        if line.startswith('python ='):
            continue
        if line.startswith('{%'):
            continue
        if recording:
            deps.append((index, line))
    return deps

def get_new_version(package_name: str) -> Optional[str]:
    """
    This function parses command line arguments using the `argparse` module.

    Args:
        None

    Returns:
        argparse.Namespace: The parsed command line arguments.

    Raises:
        None

    Example:
        ```
        import argparse
        from pathlib import Path

        def parse_args() -> argparse.Namespace:
            parser = argparse.ArgumentParser()
            parser.add_argument(
                "file",
                type=Path,
            )
            parser.add_argument(
                "--section",
                "-s",
                type=str,
                default="tool.poetry.dependencies",
            )
            return parser.parse_args()

        args = parse_args()
        print(args.file)
        print(args.section)
        ```
    """

    resp = requests.get(f'https://pypi.org/pypi/{package_name}/json')
    if not resp.ok:
        return None
    rjson = resp.json()
    return rjson['info']["version"]


def bump_version(dependency: str) -> str:
    """
    This function parses command line arguments using the `argparse` module.

    Args:
        None

    Returns:
        argparse.Namespace: The parsed command line arguments.

    Raises:
        None

    Example:
        ```
        import argparse
        from pathlib import Path

        def parse_args() -> argparse.Namespace:
            parser = argparse.ArgumentParser()
            parser.add_argument(
                "file",
                type=Path,
            )
            parser.add_argument(
                "--section",
                "-s",
                type=str,
                default="tool.poetry.dependencies",
            )
            return parser.parse_args()

        args = parse_args()
        print(args.file)
        print(args.section)
        ```
    """

    exp_match = EXPANDED_VER_RE.match(dependency)
    raw_match = None
    if exp_match:
        package = exp_match.group("package").strip()
        version = exp_match.group("version").lstrip("^=!~<>")
    else:
        raw_match = RAW_VERSION_RE.match(dependency)
    if raw_match:
        package = raw_match.group("package").strip()
        version = raw_match.group("version").lstrip("^=!~<>")
    if exp_match is None and raw_match is None:
        return None

    print(f"Checking {package}")
    new_version = get_new_version(package)
    if new_version is not None and version != new_version:
        print(f"Found new version: {new_version}")
        return dependency.replace(version, new_version)

    return None

def main():
    """
    This function parses command line arguments using the `argparse` module.

    Args:
        None

    Returns:
        argparse.Namespace: The parsed command line arguments.

    Raises:
        None

    Example:
        ```
        import argparse
        from pathlib import Path

        def parse_args() -> argparse.Namespace:
            parser = argparse.ArgumentParser()
            parser.add_argument(
                "file",
                type=Path,
            )
            parser.add_argument(
                "--section",
                "-s",
                type=str,
                default="tool.poetry.dependencies",
            )
            return parser.parse_args()

        args = parse_args()
        print(args.file)
        print(args.section)
        ```
    """

    args = parse_args()
    deps = get_dependencies(args.file, args.section)
    lines = args.file.read_text().splitlines(keepends=False)
    for i, dep in deps:
        new_version = bump_version(dep)
        if new_version:
            lines[i] = new_version
    args.file.write_text("\n".join(lines))
    


if __name__ == "__main__":
    main()
