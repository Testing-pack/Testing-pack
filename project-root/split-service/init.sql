CREATE TABLE IF NOT EXISTS user_assignments (
    id              SERIAL PRIMARY KEY,
    test_id         VARCHAR NOT NULL,
    user_id         VARCHAR(255) NOT NULL,
    variation_id    VARCHAR(50) NOT NULL,
    assigned_at     TIMESTAMP NOT NULL DEFAULT NOW()
);