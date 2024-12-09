"""Setup file for market-analysis package."""
from setuptools import setup, find_namespace_packages
from pathlib import Path

def read_requirements(filename: str) -> list[str]:
    """Read requirements from a file."""
    reqs_path = Path(__file__).parent / "requirements" / filename
    with open(reqs_path, "r") as f:
        return [line.strip() for line in f if line.strip() and not line.startswith("#")]

# Read core requirements
install_requires = read_requirements("requirements-core.txt")

# Read provider-specific requirements
ibrokers_requires = read_requirements("requirements-ibrokers.txt")
binance_requires = read_requirements("requirements-binance.txt")

# All providers combined
all_requires = ibrokers_requires + binance_requires

setup(
    name="market-analysis",
    version="0.1.0",
    packages=find_namespace_packages(include=['src.*']),
    package_dir={"": "."},
    install_requires=install_requires,
    extras_require={
        "ibrokers": ibrokers_requires,
        "binance": binance_requires,
        "all": all_requires,
    },
    python_requires=">=3.8",
)
