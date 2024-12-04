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

GOOGLE_KEY=xxxxxxxxxx - ID приложения GOOGLE  
GOOGLE_SECRET=xxxxxxxxxx - SECRET приложения GOOGLE  

Так же нужно установить redis:  
sudo apt install redis

Для установки зависимостей, находясь в корне проекта выполнить:  
pip install -r requirements.txt

Далее команды выполнять относительно директории:  
/Netology_diplom/netology_diplom

Запуск тестов с получением метрики покрытия кода тестами:  
pytest --cov=.

Запуск celery:  
celery -A netology_diplom.celeryapp worker --loglevel=info 

Запуск приложения:  
python manage.py makemigrations  
python manage.py migrate  
python manage.py runserver

Конечные точки описаны в [документации сгенерированной в PostMan](https://documenter.getpostman.com/view/39161558/2sAY55adNw)

Документация сгенерированная в DRF Spectacular доступна по адресу api/docs/.  
Панель для анализа и отладки приложения через django-silk доступна по адресу silk/.  

Для авторизации через GOOGLE, в браузере, перейдите по ссылке:  
http://localhost:8000/api/v1/auth/o/google-oauth2/?redirect_uri=http://localhost:8000/api/v1/complete/google-oauth2/.  
В ответе вернется authorization_url. Нужно перейти по этой ссылке, и далее ввести свои данные GOOGLE-аккаунта.