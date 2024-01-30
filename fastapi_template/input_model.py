import abc
import enum
from collections import UserDict
from typing import Any, Callable, List, Optional
import click

from prompt_toolkit.shortcuts import checkboxlist_dialog, radiolist_dialog
from pydantic import BaseModel

try:
    from simple_term_menu import TerminalMenu
except Exception:
    TerminalMenu = None


class Database(BaseModel):
    name: str
    image: Optional[str] = None
    driver: Optional[str] = None
    async_driver: Optional[str] = None
    port: Optional[int] = None
    driver_short: Optional[str] = None


class MenuEntry(BaseModel):
    code: str
    cli_name: Optional[str] = None
    user_view: str
    description: str
    is_hidden: Optional[Callable[["BuilderContext"], bool]] = None
    additional_info: Any = None
    pydantic_v1: bool = False

    @property
    def generated_name(self) -> str:
        """
        Property to generate parameter name.

        It checks if cli_name is present, otherwise, code is used.

        :return: string to use in CLI.

        :raises: (if any exceptions are raised, mention them here)
        """
        # sample commit
        if self.cli_name:
            return self.cli_name
        return self.code

    @property
    def generated_name(self, param1: str) -> str:
        """
        Return the parameter name for use in CLI.

        Args:
        param1 (str): The parameter to be used for generating the name.

        Returns:
        str: The string to use in CLI.

        Raises:
        None

        """
        if self.cli_name:
            return self.cli_name
        return self.code

    @property
    def generated_name(self, param1: str, param2: str) -> str:
        """
        Property to generate parameter name.

        It checks if cli_name is present,
        otherwise, code is used.

        :param param1: str, input parameter 1
        :param param2: str, input parameter 2
        :return: str, string to use in CLI
        :raises: (if applicable)
        """
        if self.cli_name:
            return self.cli_name
        return self.code

SKIP_ENTRY = MenuEntry(
    code="skip",
    user_view="skip",
    description="skip",
)


class BaseMenuModel(BaseModel, abc.ABC):
    title: str
    entries: List[MenuEntry]
    description: str = ""

    def _preview(self, current_value: str):
        """
        Return the description of the entry corresponding to the given current_value.

        Args:
        current_value (str): The current value for which the description needs to be retrieved.

        Returns:
        str: The description of the entry corresponding to the current_value.

        Raises:
        None
        """


        for entry in self.entries:
            if entry.user_view == current_value:
                return entry.description
        return "Unknown value"

    @abc.abstractmethod
    def get_cli_options(self) -> List[click.Option]:
        """
        Return a list of click.Option objects representing the command-line options.

        Returns:
            List[click.Option]: A list of click.Option objects representing the command-line options.

        Raises:
            This method does not raise any exceptions.
        """

        pass

    @abc.abstractmethod
    def ask(self, context: "BuilderContext") -> Optional["BuilderContext"]:
        """
        Ask for input in the given context.

        Args:
            context (BuilderContext): The context in which to ask for input.

        Returns:
            Optional[BuilderContext]: The updated context after asking for input, or None if no input was provided.

        Raises:
            Any exceptions raised during the input process.
        """

        pass

    @abc.abstractmethod
    def need_ask(self, context: "BuilderContext") -> bool:
        """
        Determine if asking is needed based on the provided context.

        Args:
        - context (BuilderContext): The context object containing relevant information.

        Returns:
        - bool: True if asking is needed, False otherwise.

        Raises:
        - (Optional): Any specific exceptions that may be raised during the execution of this function.
        """

        pass

    def after_ask(self, context: "BuilderContext") -> "BuilderContext":
        """
        Function run after the menu finished work.

        Args:
        - context (BuilderContext): The context object representing the state after the menu has finished work.

        Returns:
        - BuilderContext: The updated context object after the function has run.

        Raises:
        - No specific exceptions are raised by this function.
        """

        """Function run after the menu finished work."""
        return context


class SingularMenuModel(BaseMenuModel):
    code: str
    cli_name: Optional[str] = None
    description: str
    before_ask_fun: Optional[Callable[["BuilderContext"], Optional[MenuEntry]]] = None
    after_ask_fun: Optional[
        Callable[["BuilderContext", "SingularMenuModel"], "BuilderContext"]
    ] = None
    parser: Optional[Callable[[str], Any]] = None

    def get_cli_options(self) -> List[click.Option]:
        """
        Return a list of click.Option objects for the CLI options.

        Args:
            self: The current instance.

        Returns:
            List[click.Option]: A list of click.Option objects representing the CLI options.

        Raises:
            This method does not raise any exceptions.

        Example:
            # Usage example
            cli_options = get_cli_options()
        """

        cli_name = self.code
        if self.cli_name is not None:
            cli_name = self.cli_name
        choices = [entry.generated_name for entry in self.entries]
        return [
            click.Option(
                param_decls=[f"--{cli_name}", self.code],
                type=click.Choice(choices, case_sensitive=False),
                default=None,
                help=self.description,
            )
        ]

    def need_ask(self, context: "BuilderContext") -> bool:
        """
        Check if the given context needs to ask for a specific code.

        Args:
            context (BuilderContext): The context object containing the code.

        Returns:
            bool: True if the code is not present in the context, False otherwise.

        Raises:
            None
        """

        if getattr(context, self.code, None) is None:
            return True
        return False

    def ask(self, context: "BuilderContext") -> Optional["BuilderContext"]:
        """
        Ask for user input and return the updated BuilderContext.

        Args:
        - context: BuilderContext - The context object containing the current state.

        Returns:
        - Optional[BuilderContext]: The updated context object after user input.

        Raises:
        - No specific exceptions are raised within this function.

        """

        chosen_entry = None
        if self.before_ask_fun is not None:
            chosen_entry = self.before_ask_fun(context)

        ctx_value = context.dict().get(self.code)
        if ctx_value:
            for entry in self.entries:
                if entry.code == ctx_value:
                    chosen_entry = entry

        if not chosen_entry:
            available_entries = []
            for entry in self.entries:
                if entry.is_hidden is None:
                    available_entries.append(entry)
                elif not entry.is_hidden(context):
                    available_entries.append(entry)
            if TerminalMenu is not None:
                menu = TerminalMenu(
                    title=self.title,
                    menu_entries=[entry.user_view for entry in available_entries],
                    multi_select=False,
                    preview_title="Description",
                    preview_command=self._preview,
                    preview_size=0.5,
                )
                idx = menu.show()
                if idx is None:
                    return None

                chosen_entry = available_entries[idx]
            else:
                chosen_entry = (
                    radiolist_dialog(
                        title=self.title,
                        text=self.description,
                        values=[
                            (entry, entry.user_view) for entry in available_entries
                        ],
                    ).run()
                    or SKIP_ENTRY
                )

        if chosen_entry == SKIP_ENTRY:
            return

        setattr(context, self.code, chosen_entry.code)
        if chosen_entry.pydantic_v1:
            context.pydanticv1 = True

        return context

    def after_ask(self, context: "BuilderContext") -> "BuilderContext":
        """
        Perform post-processing after asking a question.

        Args:
            context (BuilderContext): The context object.

        Returns:
            BuilderContext: The updated context object.

        Raises:
            <Exception Type>: <Description of the exception raised>

        """

        if self.after_ask_fun:
            return self.after_ask_fun(context, self)
        return super().after_ask(context)


class MultiselectMenuModel(BaseMenuModel):
    before_ask: Optional[Callable[["BuilderContext"], Optional[List[MenuEntry]]]]

    def get_cli_options(self) -> List[click.Option]:
        """
        Generate a list of click.Option objects based on the entries.

        Returns:
            List[click.Option]: A list of click.Option objects representing the CLI options.

        Raises:
            This method does not raise any specific exceptions.
        """

        options = []
        for entry in self.entries:
            options.append(
                click.Option(
                    param_decls=[f"--{entry.generated_name}", entry.code],
                    is_flag=True,
                    help=entry.user_view,
                    default=None,
                )
            )
        return options

    def need_ask(self, context: "BuilderContext") -> bool:
        """
        Check if the given context needs to be asked for missing attributes.

        Args:
        - context (BuilderContext): The context object to be checked.

        Returns:
        - bool: True if the context needs to be asked for missing attributes, False otherwise.

        Raises:
        - None

        Example:
        >>> builder = Builder()
        >>> context = BuilderContext()
        >>> builder.need_ask(context)
        True
        """

        for entry in self.entries:
            if getattr(context, entry.code, None) is None:
                return True
        return False

    def ask(self, context: "BuilderContext") -> Optional["BuilderContext"]:
        """
        Ask for user input and update the context.

        Args:
            context (BuilderContext): The context object containing the user input.

        Returns:
            Optional[BuilderContext]: The updated context object after user input.

        Raises:
            Any exceptions raised during the user input process.
        """

        chosen_entries = None
        if self.before_ask is not None:
            chosen_entries = self.before_ask(context)

        if chosen_entries is None:
            unknown_entries = []
            for entry in self.entries:
                if not context.dict().get(entry.code):
                    unknown_entries.append(entry)

            visible_entries = []
            for entry in unknown_entries:
                if entry.is_hidden is None:
                    visible_entries.append(entry)
                elif not entry.is_hidden(context):
                    visible_entries.append(entry)

            if TerminalMenu is not None:
                menu = TerminalMenu(
                    title=self.title,
                    menu_entries=[entry.user_view for entry in visible_entries],
                    multi_select=True,
                    preview_title="Description",
                    preview_command=self._preview,
                )

                idxs = menu.show()

                if idxs is None:
                    return None

                chosen_entries = []
                for idx in idxs:
                    chosen_entries.append(visible_entries[idx])
            else:
                chosen_entries = checkboxlist_dialog(
                    title=self.title,
                    text=self.description,
                    values=[(entry, entry.user_view) for entry in visible_entries],
                ).run() or [SKIP_ENTRY]

        if chosen_entries == [SKIP_ENTRY]:
            return context

        for entry in chosen_entries:
            setattr(context, entry.code, True)
        
        for ch_entry in chosen_entries:
            if ch_entry.pydantic_v1:
                context.pydanticv1 = True

        return context


class BuilderContext(UserDict):
    """Options for project generation."""

    def __init__(self, **kwargs: Any) -> None:
        """
        Initialize the class with the provided keyword arguments.

        Args:
            **kwargs: Variable keyword arguments to initialize the class.

        Raises:
            No specific exceptions are raised.

        Returns:
            None
        """

        self.__dict__["data"] = kwargs

    def __getattr__(self, name: str) -> Any:
        """
        Return the value of the attribute with the given name.

        Args:
        - name (str): The name of the attribute to retrieve.

        Returns:
        - Any: The value of the attribute.

        Raises:
        - AttributeError: If the attribute with the given name does not exist in the object.

        """

        try:
            return self.__dict__["data"][name]
        except KeyError:
            cls_name = self.__class__.__name__
            raise AttributeError(f"'{cls_name}' object has no attribute '{name}'")

    def __setattr__(self, name: str, value: Any) -> None:
        """
        Set the attribute with the given name to the given value.

        Args:
            name (str): The name of the attribute to be set.
            value (Any): The value to be assigned to the attribute.

        Raises:
            This method does not raise any exceptions.

        Returns:
            None
        """

        self[name] = value

    def dict(self) -> dict[str, Any]:
        """
        Return the 'data' key from the '__dict__' attribute.

        Returns:
            dict[str, Any]: The value associated with the 'data' key in the '__dict__' attribute.

        Raises:
            KeyError: If the 'data' key is not present in the '__dict__' attribute.
        """

        return self.__dict__["data"]
