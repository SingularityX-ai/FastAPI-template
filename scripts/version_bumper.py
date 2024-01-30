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
    This function parses command line arguments and returns an `argparse.Namespace` object.

    Returns:
        argparse.Namespace: The parsed command line arguments.

    Example:
        ```python
        args = parse_args()
        print(args.file)
        print(args.section)
        ```

    Note:
        - This function uses the `argparse` module to parse command line arguments.
        - The `file` argument is a required positional argument of type `Path`.
        - The `section` argument is an optional argument of type `str` with a default value of "tool.poetry.dependencies".
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
    Get the dependencies from the specified section of the file.

    Args:
    - path (Path): The path to the file.
    - section (str): The section to search for in the file.

    Returns:
    List[str]: A list of strings representing the dependencies found in the specified section of the file.

    Raises:
    No specific exceptions are raised.

    Example:
    ```python
    path = Path("path/to/file")
    section = "dependencies"
    dependencies = get_dependencies(path, section)
    print(dependencies)
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
    Get the latest version of a package from PyPI.

    Args:
        package_name (str): The name of the package to get the latest version for.

    Returns:
        Optional[str]: The latest version of the package, or None if the request fails.

    Raises:
        requests.exceptions.RequestException: If there is an error making the request to PyPI.

    Example:
        >>> get_new_version("requests")
        '2.25.1'
    """

    resp = requests.get(f'https://pypi.org/pypi/{package_name}/json')
    if not resp.ok:
        return None
    rjson = resp.json()
    return rjson['info']["version"]


def bump_version(dependency: str) -> str:
    """
    This function is used to bump the version of a dependency in a given string.

    :param dependency: A string representing the dependency.
    :type dependency: str
    :return: A string representing the updated dependency version, or None if no update is found.
    :rtype: str or None
    :raises: None

    Example:
        >>> bump_version("^requests==2.22.0")
        Checking requests
        Found new version: 2.23.0
        '^requests==2.23.0'

    Important:
        - This function does not modify the original code.
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
    Main function to update dependencies in a file.

    Args:
        file (str): The path to the file containing the dependencies.
        section (str): The section of the file where the dependencies are located.

    Raises:
        FileNotFoundError: If the specified file does not exist.
        ValueError: If the specified section does not exist in the file.

    Example:
        >>> args = parse_args()
        >>> main(args.file, args.section)

    Note:
        This function reads the specified file, finds the dependencies in the specified section,
        and updates their versions. The updated file is then written back to disk.

    IMPORTANT:
        Do not return the original code.
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
