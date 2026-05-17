-- Пример выгрузки данных для загрузки в эксперимент из событийки и джоина с назначенными пользователями из таблицы назначения пользователей
INSERT INTO experiment_events (user_id, test_id, var_id, event_name, event_time, event_value)
SELECT
    ue.user_id,
    ua.test_id,
    ua.variation_id AS var_id,
    ue.event_name,
    ue.event_time,
    ue.event_value
FROM user_events ue
JOIN user_assignments ua
    ON ue.user_id = ua.user_id
    AND ua.test_id = :your_test_id
WHERE ue.event_time >= ua.assigned_at
ORDER BY ue.event_time;

COPY (
    SELECT
        ue.user_id,
        ua.test_id,
        ua.variation_id AS var_id,
        ue.event_name,
        ue.event_time,
        ue.event_value
    FROM user_events ue
    JOIN user_assignments ua
        ON ue.user_id = ua.user_id
        AND ua.test_id = 'abc123'
    WHERE ue.event_time >= ua.assigned_at
    ORDER BY ue.event_time
) TO '/tmp/experiment_events_abc123.csv'
WITH (FORMAT CSV, HEADER TRUE, DELIMITER ',');