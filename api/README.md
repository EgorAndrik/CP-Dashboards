# API проекта
Работает как под докером, так и под обычным фласком. Может запускаться командами 
`flask --app flaskr run --debug` (как сервер для разработки).

Продакшн сервер работает на uwsgi. Запускается через докер.
`docker build -t api --target prod .` и
`docker run api`

Рекоммендуется запускать через Docker compose 
`docker compose up --build nginx api_uwsgi`

