from pathlib import Path

from cookiecutter.exceptions import (FailedHookException,
                                     OutputDirExistsException)
from cookiecutter.main import cookiecutter
from termcolor import cprint
from fastapi_template.cli import run_command
from fastapi_template.input_model import BuilderContext

script_dir = Path(__file__).parent


def generate_project(context: BuilderContext) -> None:
    """
    Generate actual project with given context.

    :param context: builder_context
    :raises FailedHookException: If an error occurs during the project generation process.
    :raises OutputDirExistsException: If the output directory already exists.

    """
    try:
        cookiecutter(
            template=f"{script_dir}/template",
            extra_context=context.dict(),
            default_config=BuilderContext().dict(),
            no_input=True,
            overwrite_if_exists=context.force,
        )
    except (FailedHookException, OutputDirExistsException) as exc:
        if isinstance(exc, OutputDirExistsException):
            cprint("Directory with such name already exists!", "red")
        return
    cprint(
        "Project successfully generated. You can read information about usage in README.md"
    )


def main() -> None:
    """
    Starting point.

    This function serves as the starting point of the program.

    Raises:
        Any exceptions raised by the run_command or generate_project functions.

    Returns:
        None
    """
    run_command(generate_project)


if __name__ == "__main__":
    main()
