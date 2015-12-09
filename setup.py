"""Installation and setup configuration."""


from setuptools import setup


setup(
    name='emocapper',
    description="Installation and setup configuration",
    py_modules=['emocapper'],
    entry_points={
        'console_scripts': [
            'emocapper = emocapper:main',
        ],
    },
)
