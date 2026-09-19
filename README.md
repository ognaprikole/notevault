# NoteVault

Учебное веб-приложение: регистрация, вход и личные заметки.

## Стек
Python, FastAPI, SQLite, SQLAlchemy, HTML/CSS/JS

## Возможности
- регистрация и логин
- пароли хранятся как bcrypt-хэш
- каждый пользователь видит только свои заметки
- создание, редактирование, удаление

## Запуск

Нужен Python 3.11+.

## Живая версия

https://notesvault-6eg9.onrender.com/login

```bash
git clone https://github.com/ognaprikole/notevault.git
cd notevault
pip install -r requirements.txt
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000