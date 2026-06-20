from setuptools import find_packages, setup


setup(
    name="context-saver-mcp",
    version="0.1.0",
    description="Local context compression, file extraction, archive reading and review helper for coding agents.",
    packages=find_packages("src"),
    package_dir={"": "src"},
    python_requires=">=3.10",
    install_requires=[
        "typer>=0.12",
        "httpx>=0.27",
        "pydantic>=2",
        "python-dotenv>=1",
        "rich>=13",
        "mcp>=1.0",
        "pypdf>=4",
        "python-docx>=1",
        "tiktoken>=0.7",
        "py7zr>=0.21",
        "rarfile>=4",
        "pytest>=8",
    ],
    entry_points={
        "console_scripts": [
            "csp=context_saver.cli:app",
            "context-saver-mcp=context_saver.mcp_server:main",
        ]
    },
)
