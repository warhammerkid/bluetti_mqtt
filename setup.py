from setuptools import setup


setup(
    name='bluetti_mqtt',
    version='0.1',
    description='MQTT interface to Bluetti power stations',
    url='http://github.com/warhammerkid/bluetti_mqtt',
    author='Stephen Augenstein',
    author_email='perl.programmer@gmail.com',
    license='MIT',
    packages=['bluetti_mqtt'],
    install_requires=[
        'bleak',
        'crcmod',
    ],
    entry_points={
        'console_scripts': ['bluetti-logger=bluetti_mqtt.logger_cli:main']
    },
    zip_safe=False)
