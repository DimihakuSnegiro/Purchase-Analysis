```
docker network create my_shared_network
```
```
cd api_auth
docker-compose up -d --build 
cd ..
cd batch_clickhouse_analytics
docker-compose up -d --build 
```

дальше выполняем эндпоинты в swagger по localhost:8000 и localhost:8000