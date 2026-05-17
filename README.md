<img width="871" height="870" alt="image" src="https://github.com/user-attachments/assets/fd45e0d7-b2e9-4ab3-877a-9e2dc8ad8077" />







### Установка
1. Клонируем репозиторий
2. Установить Node.js (версия 14 или выше)
3. Актиаируем среды для сервисов
4. Скачиваем зависимосити
5. Запускаем докер docker-compose -f docker-compose.simple.yml up -d minio spark-master spark-worker-1 postgres airflow-webserver airflow-scheduler airflow-worker airflow-init init-airflow-connections clickhouse superset-init superset trino (для main-service)
6. Там же python main.py
7. docker-compose up -d (для split-service)
8. Там же python main.py
9. В директории frontend вводим npm start 
