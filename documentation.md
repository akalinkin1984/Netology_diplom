## Документация по работе с API

Проект настроен для работы с PostgreSQL. Можете использовать другую БД, изменив в настройках.
В корне проекта необходимо создать файл .env, примерно с таким содержимым:

PG_NAME=db - имя базы данных  
PG_USER=postgres - имя пользователя базы данных  
PG_PASSWORD=postgres - пароль пользователя базы данных  
PG_HOST=127.0.0.1 - адрес хоста базы данных  
PG_PORT=5432 - порт базы данных  

EMAIL_HOST=smtp.yandex.ru - хост SMTP-сервера  
EMAIL_PORT=465 - порт SMTP-сервера  
EMAIL_HOST_USER=xxxxx@xxxxx.xx - имя пользователя SMTP-сервера  
EMAIL_HOST_PASSWORD=xxxxxxxxxxx - пароль SMTP-сервера  

Для запуска выполните команды:  
python manage.py makemigrations  
python manage.py migrate  
python manage.py runserver

Запуск celery:  
celery -A netology_diplom.celeryapp worker

Конечные точки описаны в [документации сгенерированной в PostMan](https://documenter.getpostman.com/view/39161558/2sAY55adNw)

