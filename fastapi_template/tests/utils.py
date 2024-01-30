import os
from pathlib import Path
import shlex
import subprocess
from typing import Any, Optional
from fastapi_template.input_model import BuilderContext
from fastapi_template.__main__ import generate_project


def generate_project_and_chdir(context: BuilderContext):
    """
    Generate a project using the provided BuilderContext and change the current working directory to the project directory.

    Args:
        context (BuilderContext): The BuilderContext object containing information about the project to be generated.

    Raises:
        OSError: If an error occurs while changing the current working directory.

    Returns:
        None
    """

    generate_project(context)
    os.chdir(context.project_name)


def run_pre_commit() -> int:
    """
    Run pre-commit checks and return the return code.

    :return: int - Return code of the pre-commit checks.
    :raises: CalledProcessError - If the subprocess call to 'pre-commit run -a' fails.
    """

    results = subprocess.run(["pre-commit", "run", "-a"])
    return results.returncode


def run_docker_compose_command(
    command: Optional[str] = None,
) -> subprocess.CompletedProcess:
    """
    Run a docker-compose command.

    Args:
        command (str, optional): The command to be executed. Defaults to None.

    Returns:
        subprocess.CompletedProcess: The completed process object.

    Raises:
        <Exceptions to be added here>
    """

    docker_command = [
        "docker-compose",
        "-f",
        "deploy/docker-compose.yml",
        "--project-directory",
        ".",
    ]
    if command:
        docker_command.extend(shlex.split(command))
    else:
        docker_command.extend(
            [
                "build",
            ]
        )
    return subprocess.run(docker_command)


def run_default_check(context: BuilderContext, without_pytest=False):
    """
    Run default check for the project.

    Args:
        context (BuilderContext): The context for the builder.
        without_pytest (bool, optional): Flag to indicate whether to skip running pytest. Defaults to False.

    Raises:
        AssertionError: If the pre-commit check fails or if any of the docker-compose or pytest commands fail.
    """

    generate_project_and_chdir(context)
    compose = Path("./deploy/docker-compose.yml")
    compose_contents = compose.read_text()
    new_compose_lines = []
    for line in compose_contents.splitlines():
        if line.strip().replace(" ", "") == "target:prod":
            continue
        new_compose_lines.append(line)
    compose.write_text("\n".join(new_compose_lines) + "\n")

    assert run_pre_commit() == 0

    if without_pytest:
        return

    build = run_docker_compose_command("build")
    assert build.returncode == 0
    tests = run_docker_compose_command("run --rm api pytest -vv .")
    assert tests.returncode == 0

def model_dump_compat(model: Any):
    """
    Return a model dump compatible with the given model.

    Args:
        model (Any): The model for which the dump is to be generated.

    Returns:
        Any: The model dump compatible with the given model.

    Raises:
        None

    """

    if hasattr(model, 'model_dump'):
        return model.model_dump()
    return model.dict()
    