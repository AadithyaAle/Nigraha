from setuptools import setup

setup(
    name="stacksentinel",
    version="1.1.0",
    py_modules=[
        "app_paths",
        "auth",
        "brain",
        "cloud",
        "diagnose",
        "drift",
        "guard",
        "history",
        "hooks_engine",
        "main",
        "notifier",
        "sentinel_profile",
        "server",
        "snapshot",
        "voice",
        "gym",
    ],
    install_requires=[
        "openai",
        "psutil",
        "flask",
        "rich",
        "distro",
        "GPUtil",
    ],
    entry_points={
        "console_scripts": [
            "stacksentinel=main:cli_entry_point",
            "stacksentinel-ui=server:start_server",
        ],
    },
    author="Aadithya Ale",
    description="A local Linux repair assistant powered by OpenAI",
)
