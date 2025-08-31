#!/bin/bash

echo "Тестирование api для lab1"

export PYTHONPATH=.
python -m pytest lab1/test_lab1_app.py 

echo "Тестирование api для lab2"
python -m pytest lab2/test_lab2_app.py 