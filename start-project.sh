#!/bin/bash

#Проверка и сборка образа lab1
if [[ "$(docker images -q lab1 2> /dev/null)" == "" ]]; then
  echo "Образ lab1 не найден, собираем..."
  docker build . -t lab1 -f ./lab1/Dockerfile
else
  echo "Образ lab1 уже существует"
fi

#Проверка и сборка образа lab2
if [[ "$(docker images -q lab2 2> /dev/null)" == "" ]]; then
  echo "Образ lab2 не найден, собираем..."
  docker build . -t lab2 -f ./lab2/Dockerfile
else
  echo "Образ lab2 уже существует"
fi

# Проверка и сборка образа gateway
if [[ "$(docker images -q gateway 2> /dev/null)" == "" ]]; then
  echo "Образ gateway не найден, собираем..."
  docker build . -t gateway -f ./gateway/Dockerfile
else
  echo "Образ gateway уже существует"
fi

# Поднятие контейнеров с помощью Docker Compose
echo "Запускаем контейнеры..."
docker compose up -d

sleep 75s

# Старт проекта
echo "Запускаем проект..."
python setup_project.py