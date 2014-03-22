#!/bin/bash

virtualenv pythonenv
source pythonenv/bin/activate

easy_install -U setuptools

pip install twisted
pip install Flask
pip install pyserial
pip install autobahn
