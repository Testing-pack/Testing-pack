-- init.sql
-- Инициализация таблицы для загрузки файлов
CREATE TABLE IF NOT EXISTS file_uploads (
    upload_id SERIAL PRIMARY KEY,
    file_name VARCHAR(500) NOT NULL,
    file_format VARCHAR(20) NOT NULL,
    s3_path VARCHAR(1000) NOT NULL,
    original_hash_sha256 VARCHAR(64) NOT NULL,
    verified_hash_sha256 VARCHAR(64),
    file_size_bytes BIGINT NOT NULL,
    upload_status VARCHAR(30) NOT NULL DEFAULT 'uploading',
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description TEXT,

    CHECK (upload_status IN ('uploading', 'verified', 'failed', 'write_in_silver_layer', 'processed'))
);

-- Только необходимые индексы
CREATE INDEX IF NOT EXISTS idx_uploads_status ON file_uploads(upload_status);
CREATE INDEX IF NOT EXISTS idx_uploads_date ON file_uploads(uploaded_at);


-- init.sql
-- ... (ваш существующий код) ...

-- Таблицы для работы Iceberg Catalog (JDBC)
CREATE TABLE IF NOT EXISTS iceberg_tables (
    catalog_name VARCHAR(255) NOT NULL,
    table_namespace VARCHAR(255) NOT NULL,
    table_name VARCHAR(255) NOT NULL,
    metadata_location VARCHAR(1000),
    previous_metadata_location VARCHAR(1000),
    PRIMARY KEY (catalog_name, table_namespace, table_name)
);

CREATE TABLE IF NOT EXISTS iceberg_namespace_properties (
    catalog_name VARCHAR(255) NOT NULL,
    namespace VARCHAR(255) NOT NULL,
    property_key VARCHAR(255) NOT NULL,
    property_value VARCHAR(1000),
    PRIMARY KEY (catalog_name, namespace, property_key)
);

CREATE TABLE IF NOT EXISTS experiments (
    test_id VARCHAR(50) PRIMARY KEY,
    test_name VARCHAR(255) NOT NULL,
    description TEXT,
    owner VARCHAR(255) NOT NULL,
    status VARCHAR(50) DEFAULT 'draft',
    start_date TIMESTAMP,
    end_date TIMESTAMP,
    planned_duration_days INTEGER,
    significance_level DOUBLE PRECISION DEFAULT 0.05,
    mde DOUBLE PRECISION DEFAULT 0.1,
    power DOUBLE PRECISION DEFAULT 0.8,
    expected_daily_users INTEGER DEFAULT 1000,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    hypothesis_change_description TEXT,
    hypothesis_expected_impact TEXT,
    hypothesis_measurement_method TEXT,
    hypothesis_h0 TEXT,
    hypothesis_h1 TEXT,
    source_type VARCHAR,
    source_id VARCHAR,
    source_name VARCHAR,
    source_description TEXT,
    source_platform VARCHAR,
    source_contact_person VARCHAR,
    source_additional_info TEXT,
    sample_size_control INTEGER,
    sample_size_treatment INTEGER,
    sample_size_total INTEGER,
    days_needed INTEGER
);
CREATE INDEX IF NOT EXISTS idx_exp_owner ON experiments(owner);
CREATE INDEX IF NOT EXISTS idx_exp_status ON experiments(status);

-- Вариации
CREATE TABLE IF NOT EXISTS experiment_variations (
    id SERIAL PRIMARY KEY,
    test_id VARCHAR(50) NOT NULL REFERENCES experiments(test_id) ON DELETE CASCADE,
    variation_id VARCHAR(10),
    name VARCHAR(255),
    traffic_percentage DOUBLE PRECISION,
    CONSTRAINT experiment_variations_test_id_fkey FOREIGN KEY (test_id) REFERENCES experiments(test_id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_var_test ON experiment_variations(test_id);

-- Метрики
CREATE TABLE IF NOT EXISTS experiment_metrics (
    id SERIAL PRIMARY KEY,
    test_id VARCHAR(50) REFERENCES experiments(test_id) ON DELETE CASCADE,
    metric_id VARCHAR(100),
    purpose VARCHAR(50),
    is_primary BOOLEAN DEFAULT false,
    description TEXT,
    baseline_value DOUBLE PRECISION DEFAULT 0.0,
    sql_query TEXT,
    distribution VARCHAR DEFAULT 'unknown',
    variance_assumption VARCHAR DEFAULT 'unknown',
    outliers VARCHAR DEFAULT 'insignificant',
    statistical_type VARCHAR DEFAULT 'proportion' NOT NULL,
    variance_estimate DOUBLE PRECISION DEFAULT 0.0 NOT NULL,
    recommended_test VARCHAR(50),
    CONSTRAINT experiment_metrics_test_id_fkey FOREIGN KEY (test_id) REFERENCES experiments(test_id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_met_test ON experiment_metrics(test_id);

-- Схемы маппинга
CREATE TABLE IF NOT EXISTS mapping_schemas (
    mapping_id SERIAL PRIMARY KEY,
    experiment_id VARCHAR(50) NOT NULL REFERENCES experiments(test_id) ON DELETE CASCADE,
    mapping_name VARCHAR(255) NOT NULL,
    file_format VARCHAR(50),
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    CONSTRAINT mapping_schemas_experiment_id_fkey FOREIGN KEY (experiment_id) REFERENCES experiments(test_id) ON DELETE CASCADE
);

-- Поля маппинга
CREATE TABLE IF NOT EXISTS mapping_fields (
    mapping_field_id SERIAL PRIMARY KEY,
    mapping_id INTEGER NOT NULL REFERENCES mapping_schemas(mapping_id) ON DELETE CASCADE,
    input_field_name VARCHAR(255) NOT NULL,
    input_field_type VARCHAR(50) NOT NULL,
    target_field VARCHAR(50) NOT NULL,
    transformation_rules JSONB,
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now(),
    CONSTRAINT mapping_fields_mapping_id_fkey FOREIGN KEY (mapping_id) REFERENCES mapping_schemas(mapping_id) ON DELETE CASCADE
);

-- Загрузки файлов (зависит от experiments и mapping_schemas)
CREATE TABLE IF NOT EXISTS file_uploads (
    upload_id SERIAL PRIMARY KEY,
    file_name VARCHAR(500) NOT NULL,
    file_format VARCHAR(20) NOT NULL,
    s3_path VARCHAR(1000) NOT NULL,
    original_hash_sha256 VARCHAR(64) NOT NULL,
    verified_hash_sha256 VARCHAR(64),
    file_size_bytes BIGINT NOT NULL,
    upload_status VARCHAR(30) DEFAULT 'uploading' NOT NULL,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    experiment_id VARCHAR(50) REFERENCES experiments(test_id),
    mapping_id INTEGER REFERENCES mapping_schemas(mapping_id) ON DELETE SET NULL
);