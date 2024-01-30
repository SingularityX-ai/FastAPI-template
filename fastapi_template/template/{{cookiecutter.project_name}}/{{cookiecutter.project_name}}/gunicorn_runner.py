from typing import Any

from gunicorn.app.base import BaseApplication
from gunicorn.util import import_app
from uvicorn.workers import UvicornWorker as BaseUvicornWorker

try:
    import uvloop  # noqa: WPS433 (Found nested import)
except ImportError:
    uvloop = None  # type: ignore  # noqa: WPS440 (variables overlap)



class UvicornWorker(BaseUvicornWorker):
    """
    Configuration for uvicorn workers.

    This class is subclassing UvicornWorker and defines
    some parameters class-wide, because it's impossible,
    to pass these parameters through gunicorn.
    """

    CONFIG_KWARGS = {  # noqa: WPS115 (upper-case constant in a class)
        "loop": "uvloop" if uvloop is not None else "asyncio",
        "http": "httptools",
        "lifespan": "on",
        "factory": True,
        "proxy_headers": False,
    }


class GunicornApplication(BaseApplication):
    """
    Custom gunicorn application.

    This class is used to start guncicorn
    with custom uvicorn workers.
    """

    def __init__(  # noqa: WPS211 (Too many args)
        self,
        app: str,
        host: str,
        port: int,
        workers: int,
        **kwargs: Any,
    ):
        """
        Initialize the GunicornRunner class.

        Args:
            app (str): The application to run.
            host (str): The host to bind.
            port (int): The port to bind.
            workers (int): The number of worker processes.
            **kwargs: Additional keyword arguments.

        Raises:
            Any: This method does not explicitly raise any exceptions.

        Returns:
            None
        """

        self.options = {
            "bind": f"{host}:{port}",
            "workers": workers,
            "worker_class": "{{cookiecutter.project_name}}.gunicorn_runner.UvicornWorker",
            **kwargs
        }
        self.app = app
        super().__init__()

    def load_config(self) -> None:
        """
        Load config for web server.

        This function is used to set parameters to gunicorn
        main process. It only sets parameters that
        gunicorn can handle. If you pass unknown
        parameter to it, it crashes with an error.

        Raises:
            Any exceptions raised by the gunicorn configuration settings.

        """
        for key, value in self.options.items():
            if key in self.cfg.settings and value is not None:
                self.cfg.set(key.lower(), value)

    def load(self) -> str:
        """
        Load the actual application.

        Gunicorn loads the application based on the return value of this function,
        which is the Python path to the app's factory.

        :returns: Python path to the app factory.
        :raises: Exception if there is an error while importing the app.
        """
        return import_app(self.app)
