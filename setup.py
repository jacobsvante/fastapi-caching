from setuptools import find_packages, setup

install_requires = ["fastapi", "cachetools"]

extras_require = {
    "redis": ["aioredis"],
    "examples": ["uvicorn==0.11.5"],  # Logging issues with newer versions
    "test": [
        "pytest>=5.4.0",
        "pytest-cov",
        "pytest-asyncio",
        "requests",
        "httpx",
        "fakeredis",
        "lupa",
    ],
    "dev": ["black", "isort", "watchgod>=0.6,<0.7"],
}

extras_require["all"] = [
    dep for _, dependencies in extras_require.items() for dep in dependencies
]

setup(
    name="fastapi-caching",
    version="0.1.0",
    description="Cache library for FastAPI with tag based invalidation",
    url="https://github.com/jmagnusson/fastapi-caching",
    autho="Jacob Magnusson",
    author_email="m@jacobian.se",
    license="MIT",
    packages=find_packages(".", include=["fastapi_caching"]),
    python_requires=">=3.6",
    zip_safe=False,
    package_data={"fastapi_caching": ["py.typed"]},
    install_requires=install_requires,
    extras_require=extras_require,
    classifiers=[
        "Intended Audience :: Information Technology",
        "Intended Audience :: System Administrators",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python",
        "Topic :: Internet",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Software Development :: Libraries",
        "Topic :: Software Development",
        "Typing :: Typed",
        "Development Status :: 2 - Pre-Alpha",
        "Environment :: Web Environment",
        "Framework :: AsyncIO",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Topic :: Internet :: WWW/HTTP",
    ],
)
