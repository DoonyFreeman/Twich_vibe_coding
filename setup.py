from setuptools import setup, find_packages

setup(
    name="vibe-coding",
    version="0.1.0",
    description="Twitch Vibe Coding - approval workflow for streams",
    author="VibeCoder",
    packages=find_packages(),
    install_requires=[
        "aiosqlite>=0.19.0",
        "pyyaml>=6.0",
        "typer>=0.9.0",
        "python-dotenv>=1.0.0",
        "rich>=13.0.0",
    ],
    entry_points={
        "console_scripts": [
            "vibe=vibe_coding.cli.main:app",
        ],
    },
    python_requires=">=3.11",
)