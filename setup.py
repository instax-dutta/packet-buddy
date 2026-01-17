from setuptools import setup, find_packages

setup(
    name="packetbuddy",
    version="1.3.2",
    description="Ultra-lightweight cross-platform network usage tracker",
    author="PacketBuddy Team",
    python_requires=">=3.11",
    packages=find_packages(),
    install_requires=[
        "psutil>=5.9.6",
        "fastapi>=0.104.1",
        "uvicorn[standard]>=0.24.0",
        "asyncpg>=0.29.0",
        "tomli>=2.0.1",
        "click>=8.1.7",
        "tabulate>=0.9.0",
    ],
    entry_points={
        "console_scripts": [
            "packetbuddy=src.cli.main:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
