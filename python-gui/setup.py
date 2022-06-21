from setuptools import setup, find_packages

setup(
    name="Charter-cp",
    version="0.1",
    packages=find_packages(),
    include_package_data=True,
    py_modules=["app_c"],
    install_requires=[
        "nidaqmx==0.5.7",
        "numpy==1.22.0",
        "PyQt5==5.13.1",
        "PyQt5-sip==12.7.0",
        "pyqtgraph==0.10.0",
        "pyserial==3.4",
        "Rx==3.0.1",
        "six==1.12.0",
    ],
    entry_points="""
        [console_scripts]
        Charter-cp=app_c:app
        """,
)
