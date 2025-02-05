@echo off
rem use this an easy way to fire up the app in a windows environment.
rem first activates the virtual environment
rem then checks that the required modules / packages are available.
color a
title Running Kettle
call .venv\Scripts\activate.bat
pip install -r requirements.txt
cls
py main.py