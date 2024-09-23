FROM python:3.12

# Определение рабочей директории
WORKDIR /language_learning_bot

# Копирование всех файлов проекта в контейнер
COPY . .

# Установка Node.js v18.19.1 и npm v10.2.4
RUN apt-get update && \
    apt-get install -y curl && \
    curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && \
    apt-get install -y nodejs=18.19.1* && \
    npm install -g npm@10.2.4

# Установка зависимостей
RUN pip install --upgrade pip && pip install -r requirements.txt
RUN npm install google-translate-extended-api

# Переменные окружения
ENV PYTHONUNBUFFERED=1

# Запуск приложения
CMD ["python", "main.py"]