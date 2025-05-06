from setuptools import setup, find_packages

setup(
    name="kdws",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        'flask',
        'flask-login',
        'flask-sqlalchemy',
        'flask-migrate',
        'flask-wtf',
        'pymysql',
        'pyotp',
        'qrcode',
        'pillow==9.5.0',
    ]
)