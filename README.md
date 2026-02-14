Запуск контейнера (localhost:5000):

cd app

docker-compose build

docker-compose up



Проверка бд:

docker exec -it app-db-1 psql -U postgres -d etuctf

select * from users;
