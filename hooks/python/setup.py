#!/usr/bin/env python3

# RULE #0: MANDATORY FIRST ACTION FOR EVERY REQUEST
# 1. Read CLAUDE.md COMPLETELY before responding
# 2. Setup Python venv: [ -d "venv" ] || ./setup-venv.sh && source venv/bin/activate
# 3. Search for rules related to the request
# 4. Only proceed after confirming no violations
# Failure to follow Rule #0 has caused real harm. Check BEFORE acting, not AFTER making mistakes.
#
# GUARDS ARE SAFETY EQUIPMENT - WHEN THEY FIRE, FIX THE PROBLEM THEY FOUND
# NEVER weaken, disable, or bypass guards - they prevent real harm

"""Setup configuration for Claude Template Hooks Python package."""

import os

from setuptools import find_packages, setup

# Read long description from README if it exists
here = os.path.abspath(os.path.dirname(__file__))
readme_path = os.path.join(here, 'README.md')
long_description = ''
if os.path.exists(readme_path):
    with open(readme_path, 'r', encoding='utf-8') as f:
        long_description = f.read()

setup(
    name='claude-template-hooks',
    version='1.0.0',
    description='Safety hooks and guards for Claude Template AI assistant',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Claude Template Contributors',
    author_email='',
    url='https://github.com/dhalem/claude_template',
    packages=find_packages(exclude=['tests', 'tests.*']),
    python_requires='>=3.7',
    install_requires=[
        'pyotp>=2.8.0',  # For TOTP-based override system
        'requests>=2.25.0',  # For meta-cognitive guards
    ],
    extras_require={
        'dev': [
            'pytest>=7.0.0',
            'pytest-cov>=4.0.0',
            'pytest-timeout>=2.0.0',
            'pytest-mock>=3.0.0',
            'black>=22.0.0',
            'flake8>=6.0.0',
            'mypy>=1.0.0',
            'bandit>=1.7.0',
        ],
    },
    entry_points={
        'console_scripts': [
            'claude-guard=main:main',
        ],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Quality Assurance',
        'Topic :: Software Development :: Testing',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
    ],
    keywords='claude ai safety hooks guards testing',
    project_urls={
        'Bug Reports': 'https://github.com/dhalem/claude_template/issues',
        'Source': 'https://github.com/dhalem/claude_template',
    },
)
