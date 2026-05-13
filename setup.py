from setuptools import setup, find_packages
import os

setup(
    name="PassPort",
    version="1.0.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "typer>=0.9.0",
        "questionary>=2.0.1",
        "rich>=13.7.0",
        "cryptography>=41.0.7",
        "python-dotenv>=1.0.0",
        "pyperclip>=1.8.2",
    ],
    entry_points={
        "console_scripts": [
            "passport=passport.main:main",
        ],
    },
    python_requires=">=3.8",
    author="Tazbik Islam",
    description="Encrypt, manage, and carry your passwords everywhere securely.",
    long_description=open("README.md").read() if os.path.exists("README.md") else "",
    long_description_content_type="text/markdown",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)