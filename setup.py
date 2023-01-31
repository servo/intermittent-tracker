from setuptools import setup

setup(
    name='intermittent_tracker',
    version='0.1.0',
    author='The Servo Project Developers',
    url='https://github.com/servo/intermittent-tracker',
    description='A service that tracks intermittents on the servo/servo repo',

    packages=['intermittent_tracker'],
    install_requires=[
        'github3.py',
        'flask',
        'Flask-HTTPAuth',
    ],
    entry_points={
        'console_scripts': [
            'intermittent_tracker=intermittent_tracker.flask_server:main',
        ],
    },
    zip_safe=False,
)
