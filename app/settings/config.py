import os

from dynaconf import Dynaconf  # type: ignore

current_directory = os.path.dirname(os.path.realpath(__file__))

settings = Dynaconf(
    envvar_prefix=False,
    settings_files=[
        f"{current_directory}/settings.toml",
        f"{current_directory}/.secrets.toml",
    ],
    load_dotenv=True,
    environments=True,
)
