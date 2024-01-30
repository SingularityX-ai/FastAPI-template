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

        It checks if cli_name is present,
        otherwise, code is used.

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
        Property to generate parameter name.

        It checks if cli_name is present,
        otherwise, code is used.

        :param param1: Input parameter of type str.
        :return: String to use in CLI.
        :raises: (if applicable)
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

        :param param1: The first parameter (str).
        :param param2: The second parameter (str).
        :return: The string to use in CLI (str).
        :raises: (if applicable, add information about exceptions here)
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
            str: The description of the entry corresponding to the current_value, or "Unknown value" if no matching entry is found.

        Raises:
            No specific exceptions are raised.

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
            This method does not raise any specific exceptions.
        """

        pass

    @abc.abstractmethod
    def ask(self, context: "BuilderContext") -> Optional["BuilderContext"]:
        """
        Method to ask for input in the given context.

        Args:
            context (BuilderContext): The context in which the input is being asked for.

        Returns:
            Optional[BuilderContext]: The updated context after asking for input.

        Raises:
            This method does not raise any exceptions.
        """

        pass

    @abc.abstractmethod
    def need_ask(self, context: "BuilderContext") -> bool:
        """
        Determine if asking is needed based on the provided context.

        Args:
            context (BuilderContext): The context object containing relevant information.

        Returns:
            bool: True if asking is needed, False otherwise.

        Raises:
            This function does not raise any exceptions.
        """

        pass

    def after_ask(self, context: "BuilderContext") -> "BuilderContext":
        """
        Function run after the menu finished work.

        Args:
        - context (BuilderContext): The context object after the menu finished work.

        Returns:
        - BuilderContext: The updated context object.

        Raises:
        - No specific exceptions are raised.
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
        Return a list of click.Option objects for the command line interface options.

        Args:
            self: The current instance of the class.

        Returns:
            List[click.Option]: A list of click.Option objects representing the command line interface options.

        Raises:
            This method does not raise any exceptions.

        Example:
            # Usage example of get_cli_options
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
        Check if the specified attribute is present in the given context.

        Args:
        - context (BuilderContext): The context object to check for the attribute.

        Returns:
        - bool: True if the attribute is not present, False otherwise.

        Raises:
        - None

        """

        if getattr(context, self.code, None) is None:
            return True
        return False

    def ask(self, context: "BuilderContext") -> Optional["BuilderContext"]:
        """
        Ask for user input and return the updated BuilderContext.

        Args:
            context (BuilderContext): The context in which the user input is requested.

        Returns:
            Optional[BuilderContext]: The updated BuilderContext after user input.

        Raises:
            Any exceptions that may occur during the execution of this method.
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
        - context (BuilderContext): The context in which the post-processing is performed.

        Returns:
        - BuilderContext: The updated context after post-processing.

        Raises:
        - No specific exceptions are raised within this method.

        Note:
        - If `after_ask_fun` is defined, it will be called with the provided context and self.
          Otherwise, the `super().after_ask` method will be called with the provided context.
        """

        if self.after_ask_fun:
            return self.after_ask_fun(context, self)
        return super().after_ask(context)


class MultiselectMenuModel(BaseMenuModel):
    before_ask: Optional[Callable[["BuilderContext"], Optional[List[MenuEntry]]]]

    def get_cli_options(self) -> List[click.Option]:
        """
        Generate CLI options based on the entries.

        Returns:
            List[click.Option]: A list of click.Option objects representing the CLI options.

        Raises:
            This function does not raise any exceptions.
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
        Check if all the attributes specified in self.entries are present in the given context.

        Args:
            context (BuilderContext): The context object to check for attribute presence.

        Returns:
            bool: True if any attribute is missing, False otherwise.

        Raises:
            None

        """

        for entry in self.entries:
            if getattr(context, entry.code, None) is None:
                return True
        return False

    def ask(self, context: "BuilderContext") -> Optional["BuilderContext"]:
        """
        Ask the user to choose from a list of entries and update the context accordingly.

        Args:
            context (BuilderContext): The context object containing information for the user to choose from.

        Returns:
            Optional[BuilderContext]: The updated context object after the user's selection.

        Raises:
            None: This method does not raise any exceptions.
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
        Initialize the object with the provided keyword arguments.

        Args:
            **kwargs: Variable keyword arguments to initialize the object.

        Raises:
            Any: No specific exceptions are raised.

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
            This method does not raise any specific exceptions.

        Returns:
            None
        """

        self[name] = value

    def dict(self) -> dict[str, Any]:
        """
        Return the 'data' key from the internal dictionary.

        Returns:
            dict[str, Any]: The value associated with the 'data' key in the internal dictionary.

        Raises:
            KeyError: If the 'data' key is not present in the internal dictionary.
        """

        return self.__dict__["data"]
