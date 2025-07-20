#!/usr/bin/env python
"""
Setup script for Medical Backend package
"""

from setuptools import setup, find_packages
import os

# Read the contents of README file if it exists
this_directory = os.path.abspath(os.path.dirname(__file__))
readme_path = os.path.join(this_directory, "README.md")
if os.path.exists(readme_path):
    with open(readme_path, encoding="utf-8") as f:
        long_description = f.read()
else:
    long_description = "Medical AI Backend - Triage and diagnostic system"

# Read requirements
requirements_path = os.path.join(this_directory, "requirements_python310.txt")
requirements = []
if os.path.exists(requirements_path):
    with open(requirements_path, encoding="utf-8") as f:
        requirements = [
            line.strip()
            for line in f.readlines()
            if line.strip() and not line.startswith("#")
        ]

setup(
    name="medical-backend",
    version="1.0.0",
    author="Medical AI Team",
    author_email="team@medical-ai.com",
    description="Medical AI Backend - Triage and diagnostic system",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/medical-ai/backend",
    packages=find_packages(include=["app", "app.*"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Healthcare Industry",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Scientific/Engineering :: Medical Science Apps.",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.10",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.1",
            "pytest-cov>=4.1.0",
            "black>=23.7.0",
            "isort>=5.12.0",
            "flake8>=6.0.0",
            "mypy>=1.3.0",
        ],
        "docs": [
            "sphinx>=7.1.2",
            "sphinx-rtd-theme>=1.3.0",
        ],
        "security": [
            "bandit>=1.7.5",
            "safety>=2.3.4",
        ],
    },
    entry_points={
        "console_scripts": [
            "medical-triage=app.main:main",
            "medical-chief-bot=demo.demo_chief_bot_orchestrator:main",
            "medical-api-demo=demo.demo_chief_bot_api_integration:main",
        ],
    },
    include_package_data=True,
    package_data={
        "app": ["*.json", "*.yaml", "*.yml", "*.txt"],
        "": ["*.md", "*.txt", "*.json", "*.yaml", "*.yml"],
    },
    zip_safe=False,
    keywords=[
        "medical",
        "ai",
        "triage",
        "healthcare",
        "machine-learning",
        "deep-learning",
        "computer-vision",
        "nlp",
        "fastapi",
        "async",
    ],
    project_urls={
        "Bug Reports": "https://github.com/medical-ai/backend/issues",
        "Source": "https://github.com/medical-ai/backend",
        "Documentation": "https://medical-ai.readthedocs.io/",
    },
)
