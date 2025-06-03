from setuptools import setup, find_packages

setup(
    name="weather-monitoring",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "numpy>=1.24.3",
        "pandas>=2.0.2",
        "scikit-learn>=1.2.2",
        "python-dotenv>=1.0.0",
        "pyserial>=3.5",
        "aiohttp>=3.8.4",
        "bleak>=0.20.2",
        "websockets>=11.0.3",
        "joblib>=1.2.0"
    ],
    python_requires=">=3.8",
)