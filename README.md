<img width="871" height="870" alt="image" src="https://github.com/user-attachments/assets/fd45e0d7-b2e9-4ab3-877a-9e2dc8ad8077" />


### Описание работы
Объект исследования – процессы проверки бизнес-гипотез в цифровых продуктах с использованием A/B-тестирования.


Цель работы – разработка и реализация системы для получения данных и проведения статистических экспериментов (A/B-тестов), обеспечивающей снижение затрат на проверку гипотез, повышение достоверности результатов и интеграцию с существующей инфраструктурой обработки данных предприятия.


Методы исследования – системный анализ, проектирование распределённых систем, объектно-ориентированное программирование (Python), статистические методы (проверка гипотез, расчёт размера выборки, бутстрап), контейнеризация (Docker).


Результаты работы – разработана система, которая позволяет компаниям проводить A/B-тесты без затрат на дорогостоящие лицензии, автоматизирует полный цикл эксперимента от загрузки данных до формирования отчётов, обеспечивает достоверность выводов за счёт современных статистических методов.

### Эндпоинты 
<img width="1180" height="903" alt="image" src="https://github.com/user-attachments/assets/00f70c30-f34f-4a5e-857a-45c7461ce5a2" />
<img width="1180" height="222" alt="image" src="https://github.com/user-attachments/assets/b080e6a8-b0af-4e88-93f3-d8328ea8cd59" />

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


### Основные технологии

<img width="1440" height="809" alt="image" src="https://github.com/user-attachments/assets/2090761a-5f67-42d0-a6bb-7a27d12a27ac" />


### Пайплан обработки данных-логов

<img width="1495" height="846" alt="image" src="https://github.com/user-attachments/assets/99064e1f-805e-428a-bde7-6187967e8621" />


