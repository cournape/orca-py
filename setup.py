from setuptools import find_packages, setup


if __name__ == "__main__":
    setup(
        name="orca-py",
        version="0.0.1.dev0",
        packages=find_packages(where="src"),
        package_dir={"": "src"},
    )
