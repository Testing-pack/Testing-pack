import React, { useState, useEffect, useCallback } from 'react';
import './App.css';

// ==================== КОМПОНЕНТЫ ====================

// Компонент загрузки CSV с выбором маппинга (обязательный)
function CSVUploaderWithMapping({ onFileUploaded, experimentId, availableMappings }) {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState(null);
  const [error, setError] = useState('');
  const [selectedMappingId, setSelectedMappingId] = useState('');
  const [showMappingInfo, setShowMappingInfo] = useState(false);

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      setFile(selectedFile);
      setUploadResult(null);
      setError('');
    }
  };

  const handleUploadWithMapping = async () => {
    if (!file) {
      setError('Выберите CSV файл для загрузки');
      return;
    }

    if (!selectedMappingId) {
      setError('Выберите схему маппинга');
      return;
    }

    setUploading(true);
    setError('');

    const formData = new FormData();
    formData.append('file', file);
    formData.append('experiment_id', experimentId);
    formData.append('mapping_id', selectedMappingId);

    try {
      const response = await fetch('http://localhost:8000/mapping/upload_csv_with_mapping', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Ошибка загрузки: ${response.status}`);
      }

      const result = await response.json();
      setUploadResult(result);

      if (onFileUploaded) {
        onFileUploaded(result);
      }

      console.log('CSV файл с маппингом успешно загружен:', result);
    } catch (err) {
      console.error('Ошибка при загрузке файла с маппингом:', err);
      setError(`Ошибка при загрузке файла: ${err.message}`);
    } finally {
      setUploading(false);
    }
  };

  const selectedMapping = availableMappings.find(m => m.mapping_id == selectedMappingId);

  return (
    <div className="csv-uploader-with-mapping">
      <div className="form-section">
        <div className="form-group">
          <label>Выберите схему маппинга *</label>
          <select
            value={selectedMappingId}
            onChange={(e) => setSelectedMappingId(e.target.value)}
            required
          >
            <option value="">-- Выберите схему маппинга --</option>
            {availableMappings
              .filter(m => m.is_active)
              .map(mapping => (
                <option key={mapping.mapping_id} value={mapping.mapping_id}>
                  {mapping.mapping_name} ({mapping.fields?.length || 0} полей)
                </option>
              ))
            }
          </select>
          <small>Схема маппинга определяет как преобразуются данные из вашего файла</small>
        </div>

        {selectedMapping && (
          <div className="form-group">
            <div className="mapping-preview-toggle">
              <label>Предпросмотр схемы:</label>
              <button
                type="button"
                className="toggle-button"
                onClick={() => setShowMappingInfo(!showMappingInfo)}
              >
                {showMappingInfo ? 'Скрыть' : 'Показать'}
              </button>
            </div>

            {showMappingInfo && (
              <div className="mapping-preview">
                <h5>Соответствия полей:</h5>
                <div className="mapping-fields-list">
                  {selectedMapping.fields?.map((field, idx) => (
                    <div key={idx} className="mapping-field-item">
                      <span className="source-field">
                        <strong>{field.input_field_name}</strong>
                        <span className="field-type">({field.input_field_type})</span>
                      </span>
                      <span className="mapping-arrow">→</span>
                      <span className="target-field">
                        <strong>{field.target_field}</strong>
                      </span>
                    </div>
                  ))}
                </div>
                {selectedMapping.description && (
                  <p className="mapping-description">
                    <strong>Описание:</strong> {selectedMapping.description}
                  </p>
                )}
              </div>
            )}
          </div>
        )}
      </div>

      <div className="form-section">
        <div className="form-group">
          <label>Выберите CSV файл *</label>
          <input
            type="file"
            accept=".csv,.txt"
            onChange={handleFileChange}
            required
          />
          {file && (
            <div className="file-info">
              <p><strong>Файл:</strong> {file.name}</p>
              <p><strong>Размер:</strong> {(file.size / 1024).toFixed(2)} KB</p>
              <p><strong>Тип:</strong> {file.type || 'CSV'}</p>
            </div>
          )}
          <small>Файл будет автоматически преобразован в соответствии с выбранной схемой маппинга</small>
        </div>
      </div>

      <div className="form-actions">
        <button
          type="button"
          className="primary-button"
          onClick={handleUploadWithMapping}
          disabled={!file || !selectedMappingId || uploading}
        >
          {uploading ? '⏳ Загрузка...' : '📤 Загрузить данные с маппингом'}
        </button>
      </div>

      {error && (
        <div className="error-message">
          ⚠️ {error}
        </div>
      )}

      {uploadResult && (
        <div className="success-message">
          <div className="success-header">
            <span className="success-icon">✅</span>
            <h4>Данные успешно загружены!</h4>
          </div>
          <div className="success-details">
            <p><strong>Файл:</strong> {uploadResult.filename}</p>
            <p><strong>Строк загружено:</strong> {uploadResult.row_count}</p>
            <p><strong>Схема маппинга:</strong> {uploadResult.mapping_applied ? 'Применена' : 'Не применена'}</p>
            {uploadResult.mapping_id && (
              <p><strong>ID схемы:</strong> {uploadResult.mapping_id}</p>
            )}
            <p><strong>Статус:</strong> Загружено в S3 и обработано</p>
          </div>
        </div>
      )}
    </div>
  );
}

// Компонент загрузки CSV файла с experiment_id и маппингом (упрощённый, без анализа)
function CSVUploader({ onFileUploaded, initialExperimentId = '', availableMappings = [] }) {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState(null);
  const [error, setError] = useState('');
  const [experimentId, setExperimentId] = useState(initialExperimentId);
  const [selectedMappingId, setSelectedMappingId] = useState('');

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      setFile(selectedFile);
      setUploadResult(null);
      setError('');
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setError('Выберите файл для загрузки');
      return;
    }

    setUploading(true);
    setError('');

    const formData = new FormData();
    formData.append('file', file);

    if (experimentId && experimentId.trim() !== '') {
      formData.append('experiment_id', experimentId.trim());
    }

    if (selectedMappingId && selectedMappingId.trim() !== '') {
      formData.append('mapping_id', selectedMappingId.trim());
    }

    try {
      const endpoint = selectedMappingId
        ? 'http://localhost:8000/mapping/upload_csv_with_mapping'
        : 'http://localhost:8000/files/upload_csv';

      const response = await fetch(endpoint, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Ошибка загрузки: ${response.status}`);
      }

      const result = await response.json();
      setUploadResult(result);

      if (onFileUploaded) {
        onFileUploaded(result);
      }

      console.log('CSV файл успешно загружен:', result);
    } catch (err) {
      console.error('Ошибка при загрузке файла:', err);
      setError(`Ошибка при загрузке файла: ${err.message}`);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="csv-uploader">
      <h3>📁 Загрузка CSV файла для эксперимента</h3>

      <div className="form-section">
        <div className="form-group">
          <label>Введите Experiment ID (опционально)</label>
          <input
            type="text"
            value={experimentId}
            onChange={(e) => setExperimentId(e.target.value)}
            placeholder="ID эксперимента для привязки файла"
          />
          <small>Оставьте пустым, если не хотите привязывать файл к эксперименту</small>
        </div>

        {availableMappings && availableMappings.length > 0 && (
          <div className="form-group">
            <label>Выберите схему маппинга (опционально)</label>
            <select
              value={selectedMappingId}
              onChange={(e) => setSelectedMappingId(e.target.value)}
            >
              <option value="">-- Без маппинга --</option>
              {availableMappings
                .filter(m => m.is_active)
                .map(mapping => (
                  <option key={mapping.mapping_id} value={mapping.mapping_id}>
                    {mapping.mapping_name}
                  </option>
                ))
              }
            </select>
            <small>Если выбрана схема маппинга, данные будут преобразованы в соответствии с ней</small>
          </div>
        )}

        <div className="form-group">
          <label>Выберите CSV файл *</label>
          <input
            type="file"
            accept=".csv,.txt"
            onChange={handleFileChange}
          />
          {file && (
            <div className="file-info">
              <p><strong>Выбран файл:</strong> {file.name}</p>
              <p><strong>Размер:</strong> {(file.size / 1024).toFixed(2)} KB</p>
              <p><strong>Тип:</strong> {file.type || 'Не определен'}</p>
              {experimentId && (
                <p><strong>Experiment ID:</strong> {experimentId}</p>
              )}
              {selectedMappingId && (
                <p><strong>Схема маппинга:</strong> {
                  availableMappings.find(m => m.mapping_id == selectedMappingId)?.mapping_name || selectedMappingId
                }</p>
              )}
            </div>
          )}
        </div>

        <div className="form-actions-horizontal">
          <button
            type="button"
            className="secondary-button"
            onClick={handleUpload}
            disabled={!file || uploading}
          >
            {uploading ? '⏳ Загрузка...' : '📤 Загрузить файл'}
          </button>
        </div>

        {error && (
          <div className="error-message">
            ⚠️ {error}
          </div>
        )}

        {uploadResult && (
          <div className="success-message">
            ✅ Файл успешно загружен!
            <div className="upload-details">
              <p><strong>Имя файла:</strong> {uploadResult.filename}</p>
              <p><strong>Размер:</strong> {uploadResult.size} байт</p>
              <p><strong>Строк:</strong> {uploadResult.row_count}</p>
              <p><strong>Колонок:</strong> {uploadResult.headers.length}</p>
              {uploadResult.experiment_id && (
                <p><strong>Experiment ID:</strong> {uploadResult.experiment_id}</p>
              )}
              {uploadResult.mapping_applied && (
                <p><strong>Маппинг:</strong> Применен</p>
              )}
              {uploadResult.mapping_id && (
                <p><strong>ID схемы маппинга:</strong> {uploadResult.mapping_id}</p>
              )}
              {uploadResult.s3_upload && (
                <p><strong>Upload ID:</strong> {uploadResult.s3_upload.upload_id}</p>
              )}
              <p><strong>Сообщение:</strong> {uploadResult.message}</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function HomePage({ onNavigateToCreateTest, createdTests, onOpenExperiment, onDeleteExperiment}) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(null);
  const [statusFilter, setStatusFilter] = useState('all');

  const handleDeleteClick = (testId, testName) => {
    setShowDeleteConfirm({ testId, testName });
  };

  const handleDeleteConfirm = async () => {
    if (!showDeleteConfirm) return;

    setLoading(true);
    try {
      const response = await fetch(`http://localhost:8000/experiments/${showDeleteConfirm.testId}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        throw new Error(`Ошибка удаления: ${response.status}`);
      }

      const result = await response.json();
      console.log('Эксперимент удален:', result);

      onDeleteExperiment(showDeleteConfirm.testId);

      setShowDeleteConfirm(null);
    } catch (err) {
      console.error('Ошибка при удалении эксперимента:', err);
      setError(`Ошибка при удалении: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteCancel = () => {
    setShowDeleteConfirm(null);
  };

  const handleUpdateStatus = async (testId, newStatus) => {
    setLoading(true);
    try {
      const response = await fetch(`http://localhost:8000/experiments/${testId}/status`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ status: newStatus }),
      });

      if (!response.ok) {
        throw new Error(`Ошибка обновления статуса: ${response.status}`);
      }

      const result = await response.json();
      console.log('Статус обновлен:', result);

      onDeleteExperiment(testId);
    } catch (err) {
      console.error('Ошибка при обновлении статуса:', err);
      setError(`Ошибка: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = (status) => {
    const badges = {
      'draft': { class: 'status-draft', label: 'Черновик' },
      'active': { class: 'status-active', label: 'Активен' },
      'paused': { class: 'status-paused', label: 'На паузе' },
      'completed': { class: 'status-completed', label: 'Завершен' },
      'archived': { class: 'status-archived', label: 'В архиве' }
    };
    const badge = badges[status] || badges.draft;
    return <span className={`status-badge ${badge.class}`}>{badge.label}</span>;
  };

  const filteredTests = statusFilter === 'all'
    ? createdTests
    : createdTests.filter(test => test.status === statusFilter);

  return (
    <div className="home-page">
      <div className="hero-section">
        <h1>🧪 A/B Testing Platform</h1>
        <p className="hero-subtitle">
          Профессиональная платформа для настройки и управления A/B тестами
          со статистическими расчетами и рекомендациями тестов
        </p>
        <div className="hero-actions">
          <button
            className="cta-button"
            onClick={onNavigateToCreateTest}
          >
            🚀 Создать новый тест
          </button>
        </div>
      </div>

      <div className="features-grid">
        <div className="feature-card">
          <div className="feature-icon">📊</div>
          <h3>Статистические расчеты</h3>
          <p>Автоматический расчет размера выборки, мощности теста и MDE</p>
        </div>
        <div className="feature-card">
          <div className="feature-icon">⚡</div>
          <h3>Рекомендации тестов</h3>
          <p>Интеллектуальная рекомендация статистических тестов для каждого типа метрик</p>
        </div>
        <div className="feature-card">
          <div className="feature-icon">📁</div>
          <h3>Анализ данных</h3>
          <p>Загружайте CSV файлы для анализа данных в рамках экспериментов</p>
        </div>
        <div className="feature-card">
          <div className="feature-icon">🔒</div>
          <h3>Классификация метрик</h3>
          <p>Целевые, заградительные, прокси и информационные метрики</p>
        </div>
        <div className="feature-card">
          <div className="feature-icon">📈</div>
          <h3>Анализ гипотез</h3>
          <p>Структурированная формулировка и проверка статистических гипотез</p>
        </div>
        <div className="feature-card">
          <div className="feature-icon">🔍</div>
          <h3>Управление тестами</h3>
          <p>Просматривайте и управляйте всеми созданными экспериментами</p>
        </div>
      </div>

      <div className="recent-tests">
        <div className="tests-header">
          <h2>Мои эксперименты</h2>
          <div className="filters">
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="status-filter"
            >
              <option value="all">Все статусы</option>
              <option value="draft">Черновики</option>
              <option value="active">Активные</option>
              <option value="paused">На паузе</option>
              <option value="completed">Завершенные</option>
              <option value="archived">В архиве</option>
            </select>
          </div>
        </div>

        {error && (
          <div className="error-message">
            ⚠️ {error}
          </div>
        )}

        {filteredTests.length === 0 ? (
          <div className="empty-state">
            <p>У вас пока нет созданных тестов</p>
            <button
              className="secondary-button"
              onClick={onNavigateToCreateTest}
            >
              Создать первый тест
            </button>
          </div>
        ) : (
          <div className="tests-list">
            {filteredTests.map((test, index) => {
              const mainParams = test.test_configuration?.["Основные параметры"] || {};
              const launchParams = test.test_configuration?.["Параметры запуска"] || {};
              const variations = test.test_configuration?.["Варианты теста"] || [];
              const metrics = test.test_configuration?.Метрики || [];
              const dataSource = test.test_configuration?.["Источник данных"] || {};
              const status = test.status || 'draft';

              return (
                <div key={index} className="test-card">
                  <div className="test-header">
                    <div className="test-title-section">
                      <h3>{mainParams["Название теста"] || "Без названия"}</h3>
                      <div className="test-status-info">
                        {getStatusBadge(status)}
                        <span className="test-id">ID: {test.test_id || "N/A"}</span>
                      </div>
                    </div>
                    <div className="test-actions-header">

                      <button
                        className="delete-btn"
                        onClick={() => handleDeleteClick(test.test_id, mainParams["Название теста"])}
                        title="Удалить"
                        disabled={loading}
                      >
                        🗑️
                      </button>
                    </div>
                  </div>
                  <div className="test-details">
                    <p><strong>Владелец:</strong> {mainParams["Владелец"] || "Не указан"}</p>
                    <p><strong>Варианты:</strong> {variations.length}</p>
                    <p><strong>Метрики:</strong> {metrics.length}</p>
                    <p><strong>Источник:</strong> {dataSource.source_type === 'internal_splitting' ? 'Наша система' : 'Сторонний'}</p>
                    <p><strong>Длительность:</strong> {launchParams["Длительность (дни)"] || 0} дней</p>
                    <p><strong>Создан:</strong> {new Date(test.created_at).toLocaleDateString()}</p>
                  </div>
                  <div className="test-actions">
                    <div className="action-buttons">
                      <button
                        className="secondary-button"
                        onClick={() => onOpenExperiment(test)}
                      >
                        📂 Открыть эксперимент
                      </button>
                      {status === 'draft' && (
                        <button
                          className="primary-button-small"
                          onClick={() => handleUpdateStatus(test.test_id, 'active')}
                          disabled={loading}
                        >
                          ▶️ Запустить
                        </button>
                      )}
                      {status === 'active' && (
                        <button
                          className="warning-button"
                          onClick={() => handleUpdateStatus(test.test_id, 'paused')}
                          disabled={loading}
                        >
                          ⏸️ Пауза
                        </button>
                      )}
                      {status === 'paused' && (
                        <>
                          <button
                            className="primary-button-small"
                            onClick={() => handleUpdateStatus(test.test_id, 'active')}
                            disabled={loading}
                          >
                            ▶️ Возобновить
                          </button>
                          <button
                            className="success-button"
                            onClick={() => handleUpdateStatus(test.test_id, 'completed')}
                            disabled={loading}
                          >
                            ✅ Завершить
                          </button>
                        </>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Модальное окно подтверждения удаления */}
      {showDeleteConfirm && (
        <div className="modal-overlay">
          <div className="modal-content">
            <div className="modal-header">
              <h3>Подтверждение удаления</h3>
              <button className="close-btn" onClick={handleDeleteCancel}>×</button>
            </div>
            <div className="modal-body">
              <p>Вы уверены, что хотите удалить эксперимент?</p>
              <p><strong>{showDeleteConfirm.testName}</strong></p>
              <p className="warning-text">Это действие невозможно отменить!</p>
            </div>
            <div className="modal-actions">
              <button
                className="secondary-button"
                onClick={handleDeleteCancel}
                disabled={loading}
              >
                Отмена
              </button>
              <button
                className="danger-button"
                onClick={handleDeleteConfirm}
                disabled={loading}
              >
                {loading ? 'Удаление...' : 'Удалить'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// Компонент страницы эксперимента с привязкой файлов к эксперименту
function ExperimentPage({ experiment, onNavigateToHome, onUpdateExperiment, onDeleteExperiment }) {
  const [activeTab, setActiveTab] = useState('overview');
  const [showAddMetricModal, setShowAddMetricModal] = useState(false);
  const [newMetric, setNewMetric] = useState({
    custom_metric: {
      statistical_type: 'proportion',
      description: '',
      sql_query: `SELECT
    user_id,
    test_id,
    var_id,
    COUNT(*) as event_count
FROM events
WHERE event_name = 'YOUR_EVENT_NAME'
    AND test_id IS NOT NULL
    AND event_time >= NOW() - INTERVAL '30 дней'
GROUP BY user_id, test_id, var_id`,
      baseline_value: 0.0,
      variance_estimate: 0.0,
      distribution: 'unknown',
      variance_assumption: 'unknown',
      outliers: 'insignificant'
    },
    purpose: 'primary',
    is_primary: false
  });
  const [availableMetrics, setAvailableMetrics] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [mappings, setMappings] = useState([]);

  useEffect(() => {
    fetchAvailableMetrics();
    fetchMappings();
  }, []);

  const fetchAvailableMetrics = async () => {
    try {
      const response = await fetch('http://localhost:8000/metrics/available');
      const data = await response.json();
      setAvailableMetrics(data);
    } catch (err) {
      console.error('Ошибка загрузки метрик:', err);
    }
  };

  const fetchMappings = async () => {
    try {
      const response = await fetch(`http://localhost:8000/mapping/experiment/${experiment.test_id}`);
      if (response.ok) {
        const data = await response.json();
        setMappings(data.mappings || []);
      }
    } catch (err) {
      console.error('Ошибка загрузки схем маппинга:', err);
    }
  };

  const handleFileUploaded = (uploadResult) => {
    console.log('Файл загружен:', uploadResult);
  };

  const mainParams = experiment.test_configuration?.["Основные параметры"] || {};
  const hypothesis = mainParams["Гипотеза"] || {};
  const variations = experiment.test_configuration?.["Варианты теста"] || [];
  const metrics = experiment.test_configuration?.Метрики || [];
  const dataSource = experiment.test_configuration?.["Источник данных"] || {};
  const launchParams = experiment.test_configuration?.["Параметры запуска"] || {};
  const statistics = experiment.test_configuration?.["Статистические расчеты"] || {};

  const getPurposeBadge = (purpose) => {
    const badges = {
      'primary': { class: 'purpose-primary', label: 'Целевая' },
      'guardrail': { class: 'purpose-guardrail', label: 'Заградительная' },
      'proxy': { class: 'purpose-proxy', label: 'Прокси' },
      'info': { class: 'purpose-info', label: 'Информационная' }
    };
    const badge = badges[purpose] || badges.info;
    return <span className={`metric-purpose-badge ${badge.class}`}>{badge.label}</span>;
  };

  const getStatusBadge = (status) => {
    const badges = {
      'draft': { class: 'status-draft', label: 'Черновик' },
      'active': { class: 'status-active', label: 'Активен' },
      'paused': { class: 'status-paused', label: 'На паузе' },
      'completed': { class: 'status-completed', label: 'Завершен' },
      'archived': { class: 'status-archived', label: 'В архиве' }
    };
    const badge = badges[status] || badges.draft;
    return <span className={`status-badge ${badge.class}`}>{badge.label}</span>;
  };

  const handleAddMetric = async () => {
    if (!newMetric.custom_metric.description.trim()) {
      setError('Введите описание метрики');
      return;
    }
    if (!newMetric.custom_metric.sql_query.trim()) {
      setError('Введите SQL запрос');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await fetch(`http://localhost:8000/experiments/${experiment.test_id}/metric`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(newMetric),
      });

      if (!response.ok) {
        throw new Error(`Ошибка добавления метрики: ${response.status}`);
      }

      const result = await response.json();
      console.log('Метрика добавлена:', result);

      const updatedResponse = await fetch(`http://localhost:8000/experiments/${experiment.test_id}`);
      const updatedExperiment = await updatedResponse.json();

      onUpdateExperiment(updatedExperiment);
      setShowAddMetricModal(false);
      setNewMetric({
        custom_metric: {
          metric_type: '',
          statistical_type: 'proportion',
          description: '',
          sql_query: `SELECT
    user_id,
    test_id,
    var_id,
    COUNT(*) as event_count
FROM events
WHERE event_name = 'YOUR_EVENT_NAME'
    AND test_id IS NOT NULL
    AND event_time >= NOW() - INTERVAL '30 дней'
GROUP BY user_id, test_id, var_id`,
          baseline_value: 0.0,
          variance_estimate: 0.0,
          distribution: 'unknown',
          variance_assumption: 'unknown',
          outliers: 'insignificant'
        },
        purpose: 'primary',
        is_primary: false
      });
    } catch (err) {
      console.error('Ошибка при добавлении метрики:', err);
      setError(`Ошибка: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleRemoveMetric = async (metricIndex) => {
    if (!window.confirm('Вы уверены, что хотите удалить эту метрику?')) {
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(`http://localhost:8000/experiments/${experiment.test_id}/metric/${metricIndex}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        throw new Error(`Ошибка удаления метрики: ${response.status}`);
      }

      const result = await response.json();
      console.log('Метрика удалена:', result);

      const updatedResponse = await fetch(`http://localhost:8000/experiments/${experiment.test_id}`);
      const updatedExperiment = await updatedResponse.json();

      onUpdateExperiment(updatedExperiment);
    } catch (err) {
      console.error('Ошибка при удалении метрики:', err);
      setError(`Ошибка: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateStatus = async (newStatus) => {
    setLoading(true);
    try {
      const response = await fetch(`http://localhost:8000/experiments/${experiment.test_id}/status`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ status: newStatus }),
      });

      if (!response.ok) {
        throw new Error(`Ошибка обновления статуса: ${response.status}`);
      }

      const result = await response.json();
      console.log('Статус обновлен:', result);

      const updatedResponse = await fetch(`http://localhost:8000/experiments/${experiment.test_id}`);
      const updatedExperiment = await updatedResponse.json();

      onUpdateExperiment(updatedExperiment);
    } catch (err) {
      console.error('Ошибка при обновлении статуса:', err);
      setError(`Ошибка: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteExperiment = async () => {
    if (!window.confirm('Вы уверены, что хотите удалить этот эксперимент?')) {
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(`http://localhost:8000/experiments/${experiment.test_id}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        throw new Error(`Ошибка удаления: ${response.status}`);
      }

      const result = await response.json();
      console.log('Эксперимент удален:', result);

      onDeleteExperiment(experiment.test_id);
      onNavigateToHome();
    } catch (err) {
      console.error('Ошибка при удалении эксперимента:', err);
      setError(`Ошибка: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const renderAddMetricModal = () => {
    if (!showAddMetricModal) return null;

    return (
      <div className="modal-overlay">
        <div className="modal-content">
          <div className="modal-header">
            <h3>Добавить метрику</h3>
            <button className="close-btn" onClick={() => setShowAddMetricModal(false)}>×</button>
          </div>
          <div className="modal-body">
            {error && (
              <div className="error-message">
                ⚠️ {error}
              </div>
            )}

            <div className="form-group">
              <label>Описание *</label>
              <input
                type="text"
                value={newMetric.custom_metric.description}
                onChange={(e) => setNewMetric(prev => ({
                  ...prev,
                  custom_metric: { ...prev.custom_metric, description: e.target.value }
                }))}
                placeholder="Конверсия в покупку"
                required
              />
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>Тип метрики</label>
                <select
                  value={newMetric.custom_metric.metric_type}
                  onChange={(e) => setNewMetric(prev => ({
                    ...prev,
                    custom_metric: { ...prev.custom_metric, metric_type: e.target.value }
                  }))}
                >
                  <option value="">-- Не выбрано --</option>
                  <option value="Conversion Rate">Conversion Rate</option>
                  <option value="Count per User">Count per User</option>
                  <option value="Average Value per User">Average Value per User</option>
                  <option value="Total Revenue">Total Revenue</option>
                </select>
              </div>

              <div className="form-group">
                <label>Статистический тип *</label>
                <select
                  value={newMetric.custom_metric.statistical_type}
                  onChange={(e) => setNewMetric(prev => ({
                    ...prev,
                    custom_metric: { ...prev.custom_metric, statistical_type: e.target.value }
                  }))}
                  required
                >
                  <option value="proportion">Пропорция (конверсия)</option>
                  <option value="ratio">Отношение</option>
                  <option value="continuous_mean">Непрерывное среднее</option>
                  <option value="non_standard">Нестандартная</option>
                </select>
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>Базовое значение</label>
                <input
                  type="number"
                  step="0.001"
                  min="0"
                  value={newMetric.custom_metric.baseline_value}
                  onChange={(e) => setNewMetric(prev => ({
                    ...prev,
                    custom_metric: { ...prev.custom_metric, baseline_value: parseFloat(e.target.value) || 0 }
                  }))}
                />
              </div>

              <div className="form-group">
                <label>Дисперсия</label>
                <input
                  type="number"
                  step="0.0001"
                  min="0"
                  value={newMetric.custom_metric.variance_estimate}
                  onChange={(e) => setNewMetric(prev => ({
                    ...prev,
                    custom_metric: { ...prev.custom_metric, variance_estimate: parseFloat(e.target.value) || 0 }
                  }))}
                />
              </div>
            </div>

            <div className="form-group">
              <label>SQL запрос *</label>
              <div className="sql-info">
                <small><strong>📊 Доступные поля таблицы events:</strong></small>
                <small>• <code>id</code> - уникальный идентификатор события</small>
                <small>• <code>user_id</code> - идентификатор пользователя</small>
                <small>• <code>test_id</code> - идентификатор теста (заполняется системой)</small>
                <small>• <code>var_id</code> - идентификатор варианта (A, B, C...)</small>
                <small>• <code>event_name</code> - название события</small>
                <small>• <code>event_value</code> - числовое значение события</small>
                <small>• <code>event_time</code> - timestamp события</small>
              </div>
              <textarea
                className="sql-editor"
                value={newMetric.custom_metric.sql_query}
                onChange={(e) => setNewMetric(prev => ({
                  ...prev,
                  custom_metric: { ...prev.custom_metric, sql_query: e.target.value }
                }))}
                rows="10"
                required
              />
            </div>

            <div className="form-section" style={{ marginTop: '20px', background: '#f1f5f9' }}>
              <h4>📊 Характеристики данных (предварительная оценка)</h4>
              <div className="form-row">
                <div className="form-group">
                  <label>Распределение</label>
                  <select
                    value={newMetric.custom_metric.distribution}
                    onChange={(e) => setNewMetric(prev => ({
                      ...prev,
                      custom_metric: { ...prev.custom_metric, distribution: e.target.value }
                    }))}
                  >
                    <option value="normal">Нормальное</option>
                    <option value="non_normal">Ненормальное (асимметричное, тяжёлые хвосты)</option>
                    <option value="unknown">Неизвестно</option>
                  </select>
                </div>

                <div className="form-group">
                  <label>Дисперсии в группах</label>
                  <select
                    value={newMetric.custom_metric.variance_assumption}
                    onChange={(e) => setNewMetric(prev => ({
                      ...prev,
                      custom_metric: { ...prev.custom_metric, variance_assumption: e.target.value }
                    }))}
                  >
                    <option value="equal">Равные</option>
                    <option value="unequal">Неравные</option>
                    <option value="unknown">Неизвестно</option>
                  </select>
                </div>
              </div>

              <div className="form-group">
                <label>Выбросы</label>
                <select
                  value={newMetric.custom_metric.outliers}
                  onChange={(e) => setNewMetric(prev => ({
                    ...prev,
                    custom_metric: { ...prev.custom_metric, outliers: e.target.value }
                  }))}
                >
                  <option value="significant">Ожидаются значительные выбросы</option>
                  <option value="insignificant">Выбросы редки или незначительны</option>
                </select>
              </div>
            </div>

            <div className="form-group">
              <label>Назначение метрики</label>
              <select
                value={newMetric.purpose}
                onChange={(e) => {
                  const newPurpose = e.target.value;
                  setNewMetric(prev => ({
                    ...prev,
                    purpose: newPurpose,
                    is_primary: newPurpose === 'primary' && prev.is_primary
                  }));
                }}
              >
                <option value="primary">Целевая (Primary)</option>
                <option value="guardrail">Заградительная (Guardrail)</option>
                <option value="proxy">Прокси (Proxy)</option>
                <option value="info">Информационная (Info)</option>
              </select>
            </div>

            {newMetric.purpose === 'primary' && (
              <div className="checkbox-group">
                <input
                  type="checkbox"
                  id="is-primary-modal"
                  checked={newMetric.is_primary}
                  onChange={(e) => setNewMetric(prev => ({ ...prev, is_primary: e.target.checked }))}
                />
                <label htmlFor="is-primary-modal">Сделать основной метрикой теста</label>
              </div>
            )}
          </div>
          <div className="modal-actions">
            <button
              className="secondary-button"
              onClick={() => setShowAddMetricModal(false)}
              disabled={loading}
            >
              Отмена
            </button>
            <button
              className="primary-button"
              onClick={handleAddMetric}
              disabled={loading}
            >
              {loading ? 'Добавление...' : 'Добавить метрику'}
            </button>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="experiment-page">
      <div className="page-header">
        <button
          className="back-button"
          onClick={onNavigateToHome}
          disabled={loading}
        >
          ← На главную
        </button>
        <div className="experiment-title">
          <h1>Эксперимент: {mainParams["Название теста"] || "Без названия"}</h1>
          <div className="experiment-status-controls">
            {getStatusBadge(experiment.status)}
            {experiment.status === 'draft' && (
              <button
                className="primary-button-small"
                onClick={() => handleUpdateStatus('active')}
                disabled={loading}
              >
                ▶️ Запустить
              </button>
            )}
            {experiment.status === 'active' && (
              <button
                className="warning-button"
                onClick={() => handleUpdateStatus('paused')}
                disabled={loading}
              >
                ⏸️ Пауза
              </button>
            )}
            {experiment.status === 'paused' && (
              <>
                <button
                  className="primary-button-small"
                  onClick={() => handleUpdateStatus('active')}
                  disabled={loading}
                >
                  ▶️ Возобновить
                </button>
                <button
                  className="success-button"
                  onClick={() => handleUpdateStatus('completed')}
                  disabled={loading}
                >
                  ✅ Завершить
                </button>
              </>
            )}
            {(experiment.status === 'completed' || experiment.status === 'archived') && (
              <button
                className="secondary-button"
                onClick={() => handleUpdateStatus('draft')}
                disabled={loading}
              >
                📝 Вернуть в черновик
              </button>
            )}
            <button
              className="danger-button"
              onClick={handleDeleteExperiment}
              disabled={loading}
              title="Удалить эксперимент"
            >
              🗑️ Удалить
            </button>
          </div>
        </div>
      </div>

      {error && (
        <div className="error-message">
          ⚠️ {error}
        </div>
      )}

      <div className="experiment-tabs">
        <div className="tabs-header">
          <button
            className={`tab-btn ${activeTab === 'overview' ? 'active' : ''}`}
            onClick={() => setActiveTab('overview')}
          >
            📋 Обзор
          </button>
          <button
            className={`tab-btn ${activeTab === 'data' ? 'active' : ''}`}
            onClick={() => setActiveTab('data')}
          >
            📁 Данные
          </button>
          <button
            className={`tab-btn ${activeTab === 'mapping' ? 'active' : ''}`}
            onClick={() => setActiveTab('mapping')}
          >
            🗺️ Маппинг
          </button>
          <button
            className={`tab-btn ${activeTab === 'metrics' ? 'active' : ''}`}
            onClick={() => setActiveTab('metrics')}
          >
            📊 Метрики
          </button>
          <button
            className={`tab-btn ${activeTab === 'settings' ? 'active' : ''}`}
            onClick={() => setActiveTab('settings')}
          >
            ⚙️ Настройки
          </button>
        </div>

        <div className="tab-content">
          {activeTab === 'overview' && (
            <div className="overview-tab">
              <div className="experiment-summary">
                <h3>📋 Сводка эксперимента</h3>
                <div className="summary-grid">
                  <div className="summary-card">
                    <div className="summary-icon">🆔</div>
                    <div className="summary-content">
                      <h4>ID эксперимента</h4>
                      <p className="summary-value">{experiment.test_id}</p>
                    </div>
                  </div>
                  <div className="summary-card">
                    <div className="summary-icon">👤</div>
                    <div className="summary-content">
                      <h4>Владелец</h4>
                      <p className="summary-value">{mainParams["Владелец"] || "Не указан"}</p>
                    </div>
                  </div>
                  <div className="summary-card">
                    <div className="summary-icon">🎯</div>
                    <div className="summary-content">
                      <h4>Вариантов</h4>
                      <p className="summary-value">{variations.length}</p>
                    </div>
                  </div>
                  <div className="summary-card">
                    <div className="summary-icon">📊</div>
                    <div className="summary-content">
                      <h4>Метрик</h4>
                      <p className="summary-value">{metrics.length}</p>
                    </div>
                  </div>
                  <div className="summary-card">
                    <div className="summary-icon">⏱️</div>
                    <div className="summary-content">
                      <h4>Длительность</h4>
                      <p className="summary-value">{launchParams["Длительность (дни)"] || 0} дней</p>
                    </div>
                  </div>
                  <div className="summary-card">
                    <div className="summary-icon">📅</div>
                    <div className="summary-content">
                      <h4>Создан</h4>
                      <p className="summary-value">{new Date(experiment.created_at).toLocaleDateString()}</p>
                    </div>
                  </div>
                </div>
              </div>

              {hypothesis && hypothesis.change_description && (
                <div className="hypothesis-section">
                  <h3>🧪 Гипотеза теста</h3>
                  <div className="hypothesis-card">
                    <p><strong>Что меняем:</strong> {hypothesis.change_description}</p>
                    <p><strong>Ожидаемый эффект:</strong> {hypothesis.expected_impact}</p>
                    <p><strong>Метод измерения:</strong> {hypothesis.measurement_method}</p>
                    <div className="hypothesis-tests">
                      <p className="h0"><strong>H₀ (нулевая):</strong> {hypothesis.h0}</p>
                      <p className="h1"><strong>H₁ (альтернативная):</strong> {hypothesis.h1}</p>
                    </div>
                  </div>
                </div>
              )}

              <div className="variations-section">
                <h3>🎯 Варианты теста</h3>
                <div className="variations-list">
                  {variations.map((variation, index) => (
                    <div key={index} className="variation-card">
                      <div className="variation-header">
                        <span className="variation-id">{variation.var_test_id || `Вариант ${index + 1}`}</span>
                        <span className="variation-traffic">{variation["Процент трафика"] || 0}%</span>
                      </div>
                      <div className="variation-name">{variation.Название || `Вариант ${index + 1}`}</div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {activeTab === 'data' && (
            <div className="data-tab">
              <div className="upload-container">
                {mappings.length === 0 ? (
                  <div className="no-mappings-message">
                    <h3>🚫 Загрузка данных недоступна</h3>
                    <div className="mapping-required">
                      <div className="warning-icon">⚠️</div>
                      <div className="message-content">
                        <h4>Для загрузки данных требуется создать схему маппинга</h4>
                        <p>
                          Маппинг необходим для сопоставления полей ваших данных со стандартной схемой A/B тестов.
                          Без маппинга система не сможет правильно обработать ваши данные.
                        </p>
                        <ul>
                          <li>Создайте схему маппинга на вкладке "🗺️ Маппинг"</li>
                          <li>Укажите соответствия между полями ваших данных и нашей системой</li>
                          <li>После создания схемы вы сможете загружать данные</li>
                        </ul>
                        <button
                          className="primary-button"
                          onClick={() => setActiveTab('mapping')}
                        >
                          🗺️ Перейти к созданию маппинга
                        </button>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="upload-with-mapping">
                    <h3>📁 Загрузка данных с маппингом</h3>
                    <p className="upload-description">
                      Выберите схему маппинга и CSV файл для загрузки данных в эксперимент
                    </p>

                    <CSVUploaderWithMapping
                      onFileUploaded={handleFileUploaded}
                      experimentId={experiment.test_id}
                      availableMappings={mappings}
                    />
                  </div>
                )}
              </div>
            </div>
          )}

          {activeTab === 'metrics' && (
            <div className="metrics-tab">
              <div className="metrics-header">
                <h3>📊 Метрики эксперимента ({metrics.length})</h3>

              </div>

              {statistics.results && statistics.results.length > 0 && (
                <div className="statistics-section">
                  <h4>Статистические расчеты</h4>
                  <div className="calculations-table-container">
                    <table className="calculations-table">
                      <thead>
                        <tr>
                          <th>Метрика</th>
                          <th>Контроль</th>
                          <th>Тест</th>
                          <th>Всего</th>
                          <th>Дней нужно</th>
                          <th>Статус</th>
                        </tr>
                      </thead>
                      <tbody>
                        {statistics.results.map((calc, idx) => (
                          <tr key={idx} className={calc.sufficient ? 'status-good-row' : 'status-warning-row'}>
                            <td>
                              {calc.metric_name}
                              {calc.is_primary && <span className="primary-indicator">⭐</span>}
                            </td>
                            <td>{calc.sample_size?.control || '—'}</td>
                            <td>{calc.sample_size?.treatment || '—'}</td>
                            <td>{calc.sample_size?.total || '—'}</td>
                            <td>{calc.days_needed || '—'}</td>
                            <td>
                              <span className={`status-indicator ${calc.sufficient ? 'status-good' : 'status-warning'}`}></span>
                              {calc.sufficient ? 'Достаточно' : 'Недостаточно'}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              <div className="metrics-grid">
                {metrics.map((metric, index) => (
                  <div key={index} className="metric-card">
                    <div className="metric-header">
                      <div className="metric-title">
                        <h4>{metric.description || `Метрика ${index + 1}`}</h4>
                        {metric.is_primary && <span className="primary-badge">⭐ Основная</span>}
                      </div>
                      <div className="metric-actions">

                      </div>
                    </div>
                    <div className="metric-details">
                      <p><strong>Статистический тип:</strong> {metric.statistical_type}</p>
                      <p><strong>Назначение:</strong> {getPurposeBadge(metric.purpose)}</p>
                      <p><strong>Базовое значение:</strong> {metric.baseline_value || 0}</p>
                      <p><strong>Хар-ки:</strong> распр. {metric.distribution || 'unknown'}, дисп. {metric.variance_assumption || 'unknown'}, выбросы {metric.outliers || 'insignificant'}</p>
                      {metric.statistical_test && (
                        <p><strong>Тест:</strong> {metric.statistical_test.test_type || 'Автоматически рекомендованный'}</p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeTab === 'mapping' && (
            <MappingTab
              experimentId={experiment.test_id}
              onNavigateBack={() => setActiveTab('overview')}
            />
          )}

          {activeTab === 'settings' && (
            <div className="settings-tab">
              <h3>⚙️ Настройки эксперимента</h3>
              <div className="settings-grid">
                <div className="setting-card">
                  <h4>Основные параметры</h4>
                  <p><strong>Название:</strong> {mainParams["Название теста"] || "Не указано"}</p>
                  <p><strong>Описание:</strong> {mainParams["Описание"] || "Не указано"}</p>
                  <p><strong>Владелец:</strong> {mainParams["Владелец"] || "Не указан"}</p>
                  <p><strong>Статус:</strong> {getStatusBadge(experiment.status)}</p>
                  <p><strong>Создан:</strong> {new Date(experiment.created_at).toLocaleString()}</p>
                  <p><strong>Обновлен:</strong> {new Date(experiment.updated_at).toLocaleString()}</p>
                </div>

                <div className="setting-card">
                  <h4>Cплитование</h4>
                  <p><strong>Тип:</strong> {dataSource.source_type === 'internal_splitting' ? 'Наше сплитование' : 'Стороннее сплитование'}</p>
                  <p><strong>Название:</strong> {dataSource.name || "Не указано"}</p>
                  <p><strong>Описание:</strong> {dataSource.description || "Не указано"}</p>
                </div>

                <div className="setting-card">
                  <h4>Параметры запуска</h4>
                  <p><strong>Дата старта:</strong> {launchParams["Дата старта"] ? new Date(launchParams["Дата старта"]).toLocaleDateString() : "Не указана"}</p>
                  <p><strong>Дата окончания:</strong> {launchParams["Дата окончания"] ? new Date(launchParams["Дата окончания"]).toLocaleDateString() : "Не указана"}</p>
                  <p><strong>Длительность:</strong> {launchParams["Длительность (дни)"] || 0} дней</p>
                  {launchParams["Фактическая длительность (дни)"] && (
                    <p><strong>Фактическая длительность:</strong> {launchParams["Фактическая длительность (дни)"]} дней</p>
                  )}
                  <p><strong>Уровень значимости:</strong> {launchParams["Уровень значимости"] || 0.05}</p>
                  <p><strong>MDE:</strong> {(launchParams["MDE"] * 100 || 0).toFixed(1)}%</p>
                  <p><strong>Мощность теста:</strong> {launchParams["Мощность теста"] || 0.8}</p>
                  <p><strong>Ожидаемое кол-во пользователей в день:</strong> {launchParams["Ожидаемое кол-во пользователей в день"] || 1000}</p>
                </div>

                <div className="setting-card">
                  <h4>Управление экспериментом</h4>
                  <p>Изменить статус эксперимента:</p>
                  <div className="status-controls">
                    {experiment.status === 'draft' && (
                      <button
                        className="primary-button-small"
                        onClick={() => handleUpdateStatus('active')}
                        disabled={loading}
                      >
                        ▶️ Запустить
                      </button>
                    )}
                    {experiment.status === 'active' && (
                      <button
                        className="warning-button"
                        onClick={() => handleUpdateStatus('paused')}
                        disabled={loading}
                      >
                        ⏸️ Пауза
                      </button>
                    )}
                    {experiment.status === 'paused' && (
                      <>
                        <button
                          className="primary-button-small"
                          onClick={() => handleUpdateStatus('active')}
                          disabled={loading}
                        >
                          ▶️ Возобновить
                        </button>
                        <button
                          className="success-button"
                          onClick={() => handleUpdateStatus('completed')}
                          disabled={loading}
                        >
                          ✅ Завершить
                        </button>
                      </>
                    )}
                    {(experiment.status === 'completed' || experiment.status === 'archived') && (
                      <button
                        className="secondary-button"
                        onClick={() => handleUpdateStatus('draft')}
                        disabled={loading}
                      >
                        📝 Вернуть в черновик
                      </button>
                    )}
                  </div>

                  <div className="danger-zone">
                    <h5>Опасная зона</h5>
                    <button
                      className="danger-button"
                      onClick={handleDeleteExperiment}
                      disabled={loading}
                    >
                      🗑️ Удалить эксперимент
                    </button>
                    <p className="warning-text">Это действие невозможно отменить!</p>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {renderAddMetricModal()}
    </div>
  );
}

// Компонент для формулировки гипотезы
function HypothesisForm({ hypothesis, onChange }) {
  const [formData, setFormData] = useState(hypothesis || {
    change_description: '',
    expected_impact: '',
    measurement_method: '',
    h0: '',
    h1: ''
  });

  const handleChange = (field, value) => {
    const newData = { ...formData, [field]: value };
    setFormData(newData);
    if (onChange) {
      onChange(newData);
    }
  };

  return (
    <div className="form-section">
      <h2>Формулировка гипотезы</h2>

      <div className="form-group">
        <label>Что меняем? *</label>
        <input
          type="text"
          value={formData.change_description}
          onChange={(e) => handleChange('change_description', e.target.value)}
          placeholder="Изменение цвета кнопки с синего на зеленый"
          required
        />
        <small>Описание изменений, которые тестируем</small>
      </div>

      <div className="form-group">
        <label>На что это повлияет? *</label>
        <input
          type="text"
          value={formData.expected_impact}
          onChange={(e) => handleChange('expected_impact', e.target.value)}
          placeholder="Увеличение конверсии в покупку"
          required
        />
        <small>Ожидаемый эффект от изменений</small>
      </div>

      <div className="form-group">
        <label>Как измеряем? *</label>
        <input
          type="text"
          value={formData.measurement_method}
          onChange={(e) => handleChange('measurement_method', e.target.value)}
          placeholder="Сравнение конверсии между контрольной и тестовой группами"
          required
        />
        <small>Метод измерения эффекта</small>
      </div>

      <div className="form-row">
        <div className="form-group">
          <label>Нулевая гипотеза (H₀) *</label>
          <input
            type="text"
            value={formData.h0}
            onChange={(e) => handleChange('h0', e.target.value)}
            placeholder="Нет различий в конверсии между группами"
            required
          />
          <small>Гипотеза об отсутствии эффекта</small>
        </div>

        <div className="form-group">
          <label>Альтернативная гипотеза (H₁) *</label>
          <input
            type="text"
            value={formData.h1}
            onChange={(e) => handleChange('h1', e.target.value)}
            placeholder="Конверсия в тестовой группе выше"
            required
          />
          <small>Гипотеза о наличии эффекта</small>
        </div>
      </div>
    </div>
  );
}

// Компонент отображения рекомендованного статистического теста (без выбора)
function StatisticalTestSelector({ statisticalType }) {
  const [recommendedTest, setRecommendedTest] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const getRecommendedTest = async () => {
      if (!statisticalType) return;

      setLoading(true);
      try {
        const response = await fetch('http://localhost:8000/metrics/recommend_test', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            statistical_type: statisticalType
          }),
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        setRecommendedTest(data);
      } catch (error) {
        console.error('Error getting recommended test:', error);
      } finally {
        setLoading(false);
      }
    };

    getRecommendedTest();
  }, [statisticalType]);

  return (
    <div className="statistical-test-selector">
      <div className="form-group">
        <label>Статистический тест (определяется автоматически)</label>

        {loading ? (
          <div className="loading-message">⏳ Определение оптимального статистического теста...</div>
        ) : (
          <>
            {recommendedTest && (
              <div className="recommended-test-info">
                <div className="recommended-badge">
                  ✅ Рекомендованный тест: <strong>{recommendedTest.recommended_test}</strong>
                </div>
                <div className="test-explanation">
                  {recommendedTest.explanation}
                </div>
              </div>
            )}

            {!recommendedTest && !loading && (
              <div className="selected-test-info">
                <p>Тест будет автоматически выбран на сервере на основе типа метрики и характеристик данных.</p>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}

// Компонент расчета размера выборки
function SampleSizeCalculatorForm({ metric, testParams, onCalculate }) {
  const [baseline, setBaseline] = useState(metric.baseline_value || 0.03);
  const [variance, setVariance] = useState(metric.variance_estimate || 0.0001);
  const [mde, setMde] = useState(testParams?.mde || 0.05);
  const [significance, setSignificance] = useState(testParams?.significance_level || 0.05);
  const [power, setPower] = useState(testParams?.power || 0.8);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const calculateSampleSize = async () => {
    if (!metric.statistical_type) {
      alert('Сначала выберите статистический тип метрики');
      return;
    }

    let ratio = 1.0;
    if (testParams?.variations && testParams.variations.length === 2) {
      const controlTraffic = testParams.variations[0].traffic_percentage;
      const treatmentTraffic = testParams.variations[1].traffic_percentage;
      if (controlTraffic > 0) {
        ratio = treatmentTraffic / controlTraffic;
      }
    }

    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/metrics/calculate_sample_size', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          metric_id: `custom_${Date.now()}`,
          statistical_type: metric.statistical_type,
          baseline_value: baseline,
          mde: mde,
          significance_level: significance,
          power: power,
          variance_estimate: variance,
          ratio: ratio,
          expected_daily_users: testParams?.expected_daily_users || 1000
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setResult(data);
      if (onCalculate) {
        onCalculate(data);
      }
    } catch (error) {
      console.error('Error calculating sample size:', error);
      alert(`Ошибка расчета размера выборки: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="sample-size-calculator-form">
      <h4>🧮 Калькулятор размера выборки</h4>

      <div className="calculator-content">
        <div className="form-row">
          <div className="form-group">
            <label>Базовое значение</label>
            <input
              type="number"
              step="0.001"
              min="0"
              max="1"
              value={baseline}
              onChange={(e) => setBaseline(parseFloat(e.target.value) || 0)}
            />
            <small>Текущее значение метрики (например, конверсия 0.03 = 3%)</small>
          </div>

          <div className="form-group">
            <label>MDE (Minimum Detectable Effect)</label>
            <input
              type="number"
              step="0.01"
              min="0.01"
              max="1"
              value={mde}
              onChange={(e) => setMde(parseFloat(e.target.value) || 0.05)}
            />
            <small>Минимальный обнаруживаемый эффект: {(mde * 100).toFixed(1)}%</small>
          </div>
        </div>

        <div className="form-row">
          <div className="form-group">
            <label>Дисперсия (опционально)</label>
            <input
              type="number"
              step="0.0001"
              min="0"
              value={variance}
              onChange={(e) => setVariance(parseFloat(e.target.value) || 0)}
            />
            <small>Оценка дисперсии метрики</small>
          </div>

          <div className="form-group">
            <label>Ожидаемое кол-во пользователей в день</label>
            <input
              type="number"
              min="10"
              value={testParams?.expected_daily_users || 1000}
              onChange={(e) => {
                if (onCalculate) {
                  onCalculate({
                    ...testParams,
                    expected_daily_users: parseInt(e.target.value) || 1000
                  });
                }
              }}
            />
            <small>Сколько пользователей будет видеть тест ежедневно</small>
          </div>
        </div>

        <div className="form-row">
  <div className="form-group">
    <label>Уровень значимости (α)</label>
    <input
      type="number"
      min="0"
      max="0.5"
      step="0.01"
      value={significance}
      onChange={(e) => setSignificance(parseFloat(e.target.value) || 0.05)}
    />
  </div>

  <div className="form-group">
    <label>Статистическая мощность (1-β)</label>
    <input
      type="number"
      min="0"
      max="1"
      step="0.01"
      value={power}
      onChange={(e) => setPower(parseFloat(e.target.value) || 0.8)}
    />
  </div>
</div>

        <button
          className="primary-button"
          onClick={calculateSampleSize}
          disabled={loading}
          style={{ width: '100%', marginTop: '20px' }}
        >
          {loading ? '⏳ Расчет...' : '🧮 Рассчитать размер выборки'}
        </button>

        {result && (
          <div className="sample-size-result">
            <h5>Результаты расчета:</h5>
            <div className="results-grid">
              <div className="result-card">
                <div className="result-label">Контрольная группа</div>
                <div className="result-value">{result.sample_size.control}</div>
                <div className="result-unit">пользователей</div>
              </div>
              <div className="result-card">
                <div className="result-label">Тестовая группа</div>
                <div className="result-value">{result.sample_size.treatment}</div>
                <div className="result-unit">пользователей</div>
              </div>
              <div className="result-card">
                <div className="result-label">Всего</div>
                <div className="result-value">{result.sample_size.total}</div>
                <div className="result-unit">пользователей</div>
              </div>
              <div className="result-card">
                <div className="result-label">Необходимо дней</div>
                <div className="result-value">{result.days_needed}</div>
                <div className="result-unit">дней</div>
              </div>
            </div>

            {result.days_needed > 30 && (
              <div className="warning-message">
                ⚠️ Тест потребует более 30 дней. Рекомендуется увеличить трафик или изменить MDE.
              </div>
            )}

            {result.days_needed <= 7 && (
              <div className="success-message">
                ✅ Отличный результат! Тест будет достаточно мощным за короткое время.
              </div>
            )}

            {result.days_needed > testParams?.planned_duration_days && (
              <div className="warning-message">
                ⚠️ Запланированной длительности ({testParams?.planned_duration_days} дней) недостаточно.
                Требуется {result.days_needed} дней.
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}



// Компонент формы создания теста
function CreateTestPage({ onNavigateToHome, onTestCreated }) {
  const [formData, setFormData] = useState({
    test_name: '',
    description: '',
    owner: '',
    hypothesis: null,
    variations: [{ name: 'Контрольная группа', traffic_percentage: 50 }],
    metrics: [],
    data_source: {
      source_type: 'internal_splitting',
      source_id: 'internal_default',
      external_source_info: null
    },
    start_date: new Date().toISOString().split('T')[0],
    planned_duration_days: 14,
    significance_level: 0.05,
    mde: 0.05,
    power: 0.8,
    expected_daily_users: 1000
  });

  const [availableMetrics, setAvailableMetrics] = useState({});
  const [availableDataSources, setAvailableDataSources] = useState({});
  const [loading, setLoading] = useState(false);
  const [testResult, setTestResult] = useState(null);
  const [error, setError] = useState('');
  const [debugInfo, setDebugInfo] = useState('');

  const [showExampleModal, setShowExampleModal] = useState(false);
  const [showCalculator, setShowCalculator] = useState(false);
  const [metricSelection, setMetricSelection] = useState({
    custom_metric: {
      metric_type: '',
      statistical_type: 'proportion',
      description: '',
      sql_query: `SELECT
    user_id,
    test_id,
    var_id,
    COUNT(*) as event_count
FROM events
WHERE event_name = 'YOUR_EVENT_NAME'
    AND test_id IS NOT NULL
    AND event_time >= NOW() - INTERVAL '30 дней'
GROUP BY user_id, test_id, var_id`,
      baseline_value: 0.0,
      variance_estimate: 0.0,
      distribution: 'unknown',
      variance_assumption: 'unknown',
      outliers: 'insignificant'
    },
    purpose: 'primary',
    is_primary: false
  });

  useEffect(() => {
    fetchAvailableOptions();
  }, []);

  const fetchAvailableOptions = async () => {
    try {
      const [metricsResponse, dataSourcesResponse] = await Promise.all([
        fetch('http://localhost:8000/metrics/available'),
        fetch('http://localhost:8000/available_data_sources')
      ]);

      const metricsData = await metricsResponse.json();
      const dataSourcesData = await dataSourcesResponse.json();

      setAvailableMetrics(metricsData);
      setAvailableDataSources(dataSourcesData);
    } catch (err) {
      console.error('Ошибка загрузки опций:', err);
      setDebugInfo(`Ошибка загрузки опций: ${err.message}`);
    }
  };

  const loadExampleMetric = async (metricId) => {
    try {
      const response = await fetch(`http://localhost:8000/metrics/sql_template/${metricId}`);
      if (response.ok) {
        const data = await response.json();
        setMetricSelection(prev => ({
          ...prev,
          custom_metric: {
            ...prev.custom_metric,
            description: data.description,
            sql_query: data.sql_template,
            statistical_type: data.statistical_type || 'proportion',
            baseline_value: data.baseline_value || 0.0,
            variance_estimate: data.variance_estimate || 0.0,
          },
          purpose: data.purpose || 'primary'
        }));
        setShowExampleModal(false);
      }
    } catch (err) {
      console.error('Error loading example metric:', err);
    }
  };

  const handleInputChange = useCallback((field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  }, []);

  const handleVariationChange = useCallback((index, field, value) => {
    const updatedVariations = [...formData.variations];
    updatedVariations[index][field] = field === 'traffic_percentage' ? parseFloat(value) : value;
    setFormData(prev => ({ ...prev, variations: updatedVariations }));
  }, [formData.variations]);

  const addVariation = useCallback(() => {
  if (formData.variations.length >= 2) {
    alert('Максимальное количество вариаций - 2 (контрольная и тестовая)');
    return;
  }
    setFormData(prev => ({
      ...prev,
      variations: [...prev.variations, { name: '', traffic_percentage: 0 }]
    }));
  }, []);

  const removeVariation = useCallback((index) => {
    if (formData.variations.length > 1) {
      const updatedVariations = formData.variations.filter((_, i) => i !== index);
      setFormData(prev => ({ ...prev, variations: updatedVariations }));
    }
  }, [formData.variations]);

  const addMetric = useCallback(() => {
    if (!metricSelection.custom_metric.description.trim()) {
      alert('Введите описание метрики');
      return;
    }
    if (!metricSelection.custom_metric.sql_query.trim()) {
      alert('Введите SQL запрос');
      return;
    }

    const newMetric = {
      custom_metric: metricSelection.custom_metric,
      purpose: metricSelection.purpose,
      is_primary: metricSelection.is_primary
    };

    setFormData(prev => ({
      ...prev,
      metrics: [...prev.metrics, newMetric]
    }));

    setMetricSelection({
      custom_metric: {
        metric_type: '',
        statistical_type: 'proportion',
        description: '',
        sql_query: `SELECT
    user_id,
    test_id,
    var_id,
    COUNT(*) as event_count
FROM events
WHERE event_name = 'YOUR_EVENT_NAME'
    AND test_id IS NOT NULL
    AND event_time >= NOW() - INTERVAL '30 дней'
GROUP BY user_id, test_id, var_id`,
        baseline_value: 0.0,
        variance_estimate: 0.0,
        distribution: 'unknown',
        variance_assumption: 'unknown',
        outliers: 'insignificant'
      },
      purpose: 'primary',
      is_primary: false
    });
  }, [metricSelection, formData.metrics]);

  const removeMetric = useCallback((index) => {
    const updatedMetrics = formData.metrics.filter((_, i) => i !== index);
    setFormData(prev => ({ ...prev, metrics: updatedMetrics }));
  }, [formData.metrics]);

  const setPrimaryMetric = useCallback((index) => {
    const updatedMetrics = formData.metrics.map((metric, i) => ({
      ...metric,
      is_primary: i === index && metric.purpose === 'primary'
    }));
    setFormData(prev => ({ ...prev, metrics: updatedMetrics }));
  }, [formData.metrics]);

  const handleDataSourceChange = useCallback((field, value) => {
    setFormData(prev => ({
      ...prev,
      data_source: {
        ...prev.data_source,
        [field]: value
      }
    }));
  }, []);

  const handleExternalSourceChange = useCallback((field, value) => {
    setFormData(prev => ({
      ...prev,
      data_source: {
        ...prev.data_source,
        external_source_info: {
          ...(prev.data_source.external_source_info || {}),
          [field]: value
        }
      }
    }));
  }, []);

  const validateForm = useCallback(() => {
    if (!formData.test_name.trim()) return 'Введите название теста';
    if (!formData.description.trim()) return 'Введите описание теста';
    if (!formData.owner.trim()) return 'Введите владельца теста';
    if (formData.variations.some(v => !v.name.trim())) return 'Все вариации должны иметь название';
    const totalTraffic = formData.variations.reduce((sum, v) => sum + (v.traffic_percentage || 0), 0);
    if (Math.abs(totalTraffic - 100) > 0.01) return `Сумма трафика должна быть 100% (сейчас: ${totalTraffic.toFixed(2)}%)`;
    if (formData.variations.length !== 2) return 'Должно быть ровно две вариации (контрольная и тестовая)';
    if (formData.metrics.length === 0) return 'Добавьте хотя бы одну метрику';
    const primaryMetrics = formData.metrics.filter(m => m.purpose === 'primary');
    if (primaryMetrics.length === 0) return 'Добавьте хотя бы одну целевую (primary) метрику';
    const primaryMainMetrics = formData.metrics.filter(m => m.is_primary);
    if (primaryMainMetrics.length !== 1) return 'Должна быть ровно одна основная метрика (отмечена звёздочкой)';
    if (formData.data_source.source_type === 'internal_splitting' && !formData.data_source.source_id) {
      return 'Выберите слой сплитования';
    }
    if (formData.data_source.source_type === 'external_splitting') {
      const ext = formData.data_source.external_source_info || {};
      if (!ext.name || !ext.description) return 'Заполните обязательные поля для стороннего сплитования';
    }
    return null;
  }, [formData]);

  const handleSubmit = useCallback(async (e) => {
    e.preventDefault();

    const validationError = validateForm();
    if (validationError) {
      setError(validationError);
      return;
    }

    setLoading(true);
    setError('');
    setDebugInfo('');

    try {
      const payload = {
        ...formData,
        start_date: new Date(formData.start_date).toISOString()
      };

      console.log('Отправляем запрос с данными:', JSON.stringify(payload, null, 2));
      setDebugInfo(`Отправка запроса на сервер...`);

      const response = await fetch('http://localhost:8000/experiments/setup_test', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        let errorDetail = `HTTP error! status: ${response.status}`;
        try {
          const errorData = await response.json();
          errorDetail = errorData.detail || errorDetail;
        } catch (e) {}
        throw new Error(errorDetail);
      }

      const result = await response.json();
      console.log('Получен ответ от бэкенда:', result);
      setDebugInfo(`Тест успешно создан! ID: ${result.test_id}`);
      setTestResult(result);
      if (onTestCreated) {
        onTestCreated(result);
      }
    } catch (err) {
      console.error('Ошибка при создании теста:', err);
      setError(`Ошибка при создании теста: ${err.message}`);
      setDebugInfo(`Ошибка: ${err.message}`);
    } finally {
      setLoading(false);
    }
  }, [formData, validateForm, onTestCreated]);

  const getPurposeBadge = (purpose) => {
    const badges = {
      'primary': { class: 'purpose-primary', label: 'Целевая' },
      'guardrail': { class: 'purpose-guardrail', label: 'Заградительная' },
      'proxy': { class: 'purpose-proxy', label: 'Прокси' },
      'info': { class: 'purpose-info', label: 'Информационная' }
    };
    const badge = badges[purpose] || badges.info;
    return <span className={`metric-purpose-badge ${badge.class}`}>{badge.label}</span>;
  };

  const getStatisticalTypeLabel = (type) => {
    const labels = {
      'proportion': 'Пропорция',
      'ratio': 'Отношение',
      'continuous_mean': 'Непрерывное среднее',
      'non_standard': 'Нестандартная'
    };
    return labels[type] || type;
  };

  const renderTestResult = useCallback(() => {
    if (!testResult) return null;

    const config = testResult.test_configuration || {};
    const mainParams = config["Основные параметры"] || {};
    const launchParams = config["Параметры запуска"] || {};
    const variations = config["Варианты теста"] || [];
    const metrics = config["Метрики"] || [];
    const dataSource = config["Источник данных"] || {};
    const statistics = config["Статистические расчеты"] || {};

    return (
      <div className="test-result-overlay">
        <div className="test-result-modal">
          <h3>✅ A/B тест успешно создан!</h3>
          <div className="result-details">
            <div className="result-summary">
              <p><strong>ID теста:</strong> <code>{testResult.test_id || 'Не указан'}</code></p>
              <p><strong>Название:</strong> {mainParams["Название теста"] || 'Не указано'}</p>
              <p><strong>Владелец:</strong> {mainParams["Владелец"] || 'Не указан'}</p>
              <p><strong>Источник данных:</strong> {dataSource.name || 'Не указан'} ({dataSource.source_type === 'internal_splitting' ? 'Наше сплитование' : 'Стороннее сплитование'})</p>
            </div>

            {mainParams["Гипотеза"] && (
              <div className="hypothesis-section">
                <h4>Гипотеза теста</h4>
                <p><strong>Что меняем:</strong> {mainParams["Гипотеза"].change_description}</p>
                <p><strong>Ожидаемый эффект:</strong> {mainParams["Гипотеза"].expected_impact}</p>
                <p><strong>Нулевая гипотеза (H₀):</strong> {mainParams["Гипотеза"].h0}</p>
                <p><strong>Альтернативная гипотеза (H₁):</strong> {mainParams["Гипотеза"].h1}</p>
              </div>
            )}

            <div className="statistics-section">
              <h4>Статистические расчеты</h4>
              {statistics.results && statistics.results.length > 0 && (
                <div className="calculations-table-container">
                  <table className="calculations-table">
                    <thead>
                      <tr>
                        <th>Метрика</th>
                        <th>Контроль</th>
                        <th>Тест</th>
                        <th>Всего</th>
                        <th>Дней нужно</th>
                        <th>Статус</th>
                      </tr>
                    </thead>
                    <tbody>
                      {statistics.results.map((calc, idx) => (
                        <tr key={idx} className={calc.sufficient ? 'status-good-row' : 'status-warning-row'}>
                          <td>
                            {calc.metric_name}
                            {calc.is_primary && <span className="primary-indicator">⭐</span>}
                          </td>
                          <td>{calc.sample_size?.control || '—'}</td>
                          <td>{calc.sample_size?.treatment || '—'}</td>
                          <td>{calc.sample_size?.total || '—'}</td>
                          <td>{calc.days_needed || '—'}</td>
                          <td>
                            <span className={`status-indicator ${calc.sufficient ? 'status-good' : 'status-warning'}`}></span>
                            {calc.sufficient ? 'Достаточно' : 'Недостаточно'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              <div className="statistics-parameters">
                <h5>Параметры расчета:</h5>
                <div className="params-grid">
                  <div className="param-item"><span className="param-label">MDE:</span><span className="param-value">{(statistics.parameters?.mde * 100).toFixed(1)}%</span></div>
                  <div className="param-item"><span className="param-label">Уровень значимости:</span><span className="param-value">{statistics.parameters?.significance_level}</span></div>
                  <div className="param-item"><span className="param-label">Мощность:</span><span className="param-value">{statistics.parameters?.power}</span></div>
                  <div className="param-item"><span className="param-label">Пользователей в день:</span><span className="param-value">{statistics.parameters?.expected_daily_users}</span></div>
                </div>
              </div>
            </div>

            <div className="variations-section">
              <h4>Варианты теста ({variations.length})</h4>
              <div className="variations-list">
                {variations.map((variation, index) => (
                  <div key={index} className="variation-item"><strong>{variation.var_test_id}:</strong> {variation.Название || 'Без названия'} ({variation["Процент трафика"] || 0}%)</div>
                ))}
              </div>
            </div>

            <div className="metrics-section">
              <h4>Метрики ({metrics.length})</h4>
              <div className="metrics-list-details">
                {metrics.map((metric, index) => (
                  <div key={index} className="metric-item-detail">
                    <div className="metric-header">
                      <strong>{metric.description || `Метрика ${index + 1}`}</strong>
                      {getPurposeBadge(metric.purpose)}
                      {metric.is_primary && <span className="primary-badge">Основная</span>}
                    </div>
                    <div className="metric-info">
                      <small>Тип: {getStatisticalTypeLabel(metric.statistical_type)} | Распр: {metric.distribution} | Дисп: {metric.variance_assumption} | Выбросы: {metric.outliers}</small>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="launch-params">
              <h4>Параметры запуска</h4>
              <div className="launch-grid">
                <div className="launch-item"><span className="launch-label">Дата старта:</span><span className="launch-value">{launchParams["Дата старта"] ? new Date(launchParams["Дата старта"]).toLocaleDateString() : 'Не указана'}</span></div>
                <div className="launch-item"><span className="launch-label">Дата окончания:</span><span className="launch-value">{launchParams["Дата окончания"] ? new Date(launchParams["Дата окончания"]).toLocaleDateString() : 'Не указана'}</span></div>
                <div className="launch-item"><span className="launch-label">Длительность:</span><span className="launch-value">{launchParams["Длительность (дни)"] || 0} дней</span></div>
              </div>
            </div>
          </div>
          <div className="modal-actions">
            <button className="secondary-button" onClick={() => { setTestResult(null); onNavigateToHome(); }}>← На главную</button>
            <button className="primary-button" onClick={() => { setTestResult(null); setDebugInfo(''); }}>📊 Создать еще тест</button>
          </div>
        </div>
      </div>
    );
  }, [testResult, onNavigateToHome]);

  return (
    <div className="create-test-page">
      <div className="page-header">
        <button className="back-button" onClick={onNavigateToHome}>← На главную</button>
        <h1>Создание нового A/B теста</h1>
      </div>

      {debugInfo && <div className="debug-info"><strong>Отладка:</strong> {debugInfo}</div>}
      {error && <div className="error-message">⚠️ {error}</div>}

      <form onSubmit={handleSubmit} className="test-form">
        <div className="form-section">
          <h2>Основные параметры</h2>
          <div className="form-group">
            <label>Название теста *</label>
            <input type="text" value={formData.test_name} onChange={(e) => handleInputChange('test_name', e.target.value)} placeholder="Увеличиваем конверсию в покупку — тест нового дизайна кнопки" required />
          </div>
          <div className="form-group">
            <label>Описание *</label>
            <textarea value={formData.description} onChange={(e) => handleInputChange('description', e.target.value)} placeholder="Тестируем новую цветную кнопку для увеличения конверсии" rows="3" required />
          </div>
          <div className="form-group">
            <label>Владелец теста *</label>
            <input type="email" value={formData.owner} onChange={(e) => handleInputChange('owner', e.target.value)} placeholder="user@company.com" required />
          </div>
        </div>

        <HypothesisForm hypothesis={formData.hypothesis} onChange={(hypothesis) => handleInputChange('hypothesis', hypothesis)} />

        <div className="form-section">
          <h2>Варианты теста</h2>
          {formData.variations.map((variation, index) => (
            <div key={index} className="variation-row">
              <div className="form-group">
                <label>Название варианта</label>
                <input type="text" value={variation.name} onChange={(e) => handleVariationChange(index, 'name', e.target.value)} placeholder={index === 0 ? "Контрольная группа" : `Вариант ${index + 1}`} />
              </div>
              <div className="form-group">
                <label>Трафик (%)</label>
                <input type="number" min="0" max="100" step="0.1" value={variation.traffic_percentage} onChange={(e) => handleVariationChange(index, 'traffic_percentage', e.target.value)} />
              </div>
              {formData.variations.length > 1 && (
                <button type="button" className="remove-btn" onClick={() => removeVariation(index)}>✕</button>
              )}
            </div>
          ))}
          <button type="button" className="add-btn" onClick={addVariation}>+ Добавить вариант</button>
          <div className="traffic-summary">Сумма трафика: {formData.variations.reduce((sum, v) => sum + (v.traffic_percentage || 0), 0).toFixed(1)}%</div>
        </div>

                <div className="form-section">
          <h2>Параметры запуска</h2>
          <div className="form-row">
            <div className="form-group">
              <label>Дата старта</label>
              <input
                type="date"
                value={formData.start_date}
                onChange={(e) => handleInputChange('start_date', e.target.value)}
              />
            </div>
            <div className="form-group">
              <label>Длительность (дни)</label>
              <input
                type="number"
                min="1"
                max="365"
                value={formData.planned_duration_days}
                onChange={(e) => handleInputChange('planned_duration_days', parseInt(e.target.value) || 14)}
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>MDE (Minimum Detectable Effect)</label>
              <input
                type="number"
                min="0.01"
                max="1.0"
                step="0.01"
                value={formData.mde}
                onChange={(e) => handleInputChange('mde', parseFloat(e.target.value) || 0.05)}
              />
              <small>Минимальный обнаруживаемый эффект: {(formData.mde * 100).toFixed(1)}%</small>
            </div>

            <div className="form-group">
              <label>Ожидаемое кол-во пользователей в день</label>
              <input
                type="number"
                min="10"
                max="1000000"
                value={formData.expected_daily_users}
                onChange={(e) => handleInputChange('expected_daily_users', parseInt(e.target.value) || 1000)}
              />
              <small>Сколько пользователей будет видеть тест ежедневно</small>
            </div>
          </div>

            <div className="form-row">
  <div className="form-group">
    <label>Уровень значимости (α)</label>
    <input
      type="number"
      min="0"
      max="0.5"
      step="0.01"
      value={formData.significance_level}
      onChange={(e) => handleInputChange('significance_level', parseFloat(e.target.value) || 0.05)}
    />
    <small>Вероятность ложноположительного результата (от 0 до 0.5)</small>
  </div>

  <div className="form-group">
    <label>Статистическая мощность (1-β)</label>
    <input
      type="number"
      min="0"
      max="1"
      step="0.01"
      value={formData.power}
      onChange={(e) => handleInputChange('power', parseFloat(e.target.value) || 0.8)}
    />
    <small>Вероятность обнаружения эффекта, если он существует (от 0 до 1)</small>
  </div>
</div>
        </div>




        <div className="form-section">
          <h2>Метрики</h2>
          <div className="form-actions-horizontal">
            <button type="button" className="secondary-button" onClick={() => setShowExampleModal(true)}>📋 Загрузить пример метрики</button>
          </div>

          <div className="metric-selection">
            <div className="form-group">
              <label>Описание *</label>
              <input type="text" value={metricSelection.custom_metric.description} onChange={(e) => setMetricSelection(prev => ({ ...prev, custom_metric: { ...prev.custom_metric, description: e.target.value } }))} placeholder="Конверсия в покупку"  />
            </div>

            <div className="form-row">

              <div className="form-group">
                <label>Статистический тип *</label>
                <select
                  value={metricSelection.custom_metric.statistical_type}
                  onChange={(e) => setMetricSelection(prev => ({
                    ...prev,
                    custom_metric: { ...prev.custom_metric, statistical_type: e.target.value }
                  }))}
                  required
                >
                  <option value="proportion">Пропорция (конверсия)</option>
                  <option value="ratio">Отношение</option>
                  <option value="continuous_mean">Непрерывное среднее</option>
                  <option value="non_standard">Нестандартная</option>
                </select>
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>Базовое значение</label>
                <input
                  type="number"
                  step="0.001"
                  min="0"
                  value={metricSelection.custom_metric.baseline_value}
                  onChange={(e) => setMetricSelection(prev => ({
                    ...prev,
                    custom_metric: { ...prev.custom_metric, baseline_value: parseFloat(e.target.value) || 0 }
                  }))}
                />
              </div>

              <div className="form-group">
                <label>Дисперсия</label>
                <input
                  type="number"
                  step="0.0001"
                  min="0"
                  value={metricSelection.custom_metric.variance_estimate}
                  onChange={(e) => setMetricSelection(prev => ({
                    ...prev,
                    custom_metric: { ...prev.custom_metric, variance_estimate: parseFloat(e.target.value) || 0 }
                  }))}
                />
              </div>
            </div>

            <div className="form-group">
              <label>SQL запрос *</label>
              <div className="sql-info">
                <small><strong>📊 Доступные поля таблицы events:</strong></small>
                <small>• <code>id</code> - уникальный идентификатор события</small>
                <small>• <code>user_id</code> - идентификатор пользователя</small>
                <small>• <code>test_id</code> - идентификатор теста (заполняется системой)</small>
                <small>• <code>var_id</code> - идентификатор варианта (A, B, C...)</small>
                <small>• <code>event_name</code> - название события</small>
                <small>• <code>event_value</code> - числовое значение события</small>
                <small>• <code>event_time</code> - timestamp события</small>
              </div>
              <textarea
                className="sql-editor"
                value={metricSelection.custom_metric.sql_query}
                onChange={(e) => setMetricSelection(prev => ({
                  ...prev,
                  custom_metric: { ...prev.custom_metric, sql_query: e.target.value }
                }))}
                rows="15"
                placeholder="-- Введите ваш SQL запрос"

              />

            </div>

            {/* Блок характеристик данных */}
            <div className="form-section" style={{ marginTop: '20px', background: '#f1f5f9' }}>
              <h4>📊 Характеристики данных (предварительная оценка)</h4>
              <div className="form-row">
                <div className="form-group">
                  <label>Распределение</label>
                  <select
                    value={metricSelection.custom_metric.distribution}
                    onChange={(e) => setMetricSelection(prev => ({
                      ...prev,
                      custom_metric: { ...prev.custom_metric, distribution: e.target.value }
                    }))}
                  >
                    <option value="normal">Нормальное</option>
                    <option value="non_normal">Ненормальное (асимметричное, тяжёлые хвосты)</option>
                    <option value="unknown">Неизвестно</option>
                  </select>
                </div>

                <div className="form-group">
                  <label>Дисперсии в группах</label>
                  <select
                    value={metricSelection.custom_metric.variance_assumption}
                    onChange={(e) => setMetricSelection(prev => ({
                      ...prev,
                      custom_metric: { ...prev.custom_metric, variance_assumption: e.target.value }
                    }))}
                  >
                    <option value="equal">Равные</option>
                    <option value="unequal">Неравные</option>
                    <option value="unknown">Неизвестно</option>
                  </select>
                </div>
              </div>

              <div className="form-group">
                <label>Выбросы</label>
                <select
                  value={metricSelection.custom_metric.outliers}
                  onChange={(e) => setMetricSelection(prev => ({
                    ...prev,
                    custom_metric: { ...prev.custom_metric, outliers: e.target.value }
                  }))}
                >
                  <option value="significant">Ожидаются значительные выбросы</option>
                  <option value="insignificant">Выбросы редки или незначительны</option>
                </select>
              </div>
            </div>

            <div className="statistical-test-section">
              <StatisticalTestSelector
                statisticalType={metricSelection.custom_metric.statistical_type}
              />
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>Назначение метрики</label>
                <select
                  value={metricSelection.purpose}
                  onChange={(e) => {
                    const newPurpose = e.target.value;
                    setMetricSelection(prev => ({
                      ...prev,
                      purpose: newPurpose,
                      is_primary: newPurpose === 'primary' && prev.is_primary
                    }));
                  }}
                >
                  <option value="primary">Целевая (Primary)</option>
                  <option value="guardrail">Заградительная (Guardrail)</option>
                  <option value="proxy">Прокси (Proxy)</option>
                  <option value="info">Информационная (Info)</option>
                </select>
              </div>

              {metricSelection.purpose === 'primary' && (
                <div className="form-group">
                  <div className="checkbox-group">
                    <input
                      type="checkbox"
                      id="is-primary-checkbox"
                      checked={metricSelection.is_primary}
                      onChange={(e) => setMetricSelection(prev => ({ ...prev, is_primary: e.target.checked }))}
                    />
                    <label htmlFor="is-primary-checkbox">Сделать основной метрикой теста</label>
                  </div>
                </div>
              )}
            </div>

            <div className="sample-size-section">
  <div
    style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', cursor: 'pointer' }}
    onClick={() => setShowCalculator(!showCalculator)}
  >
    <h4>🧮 Калькулятор размера выборки для этой метрики</h4>
    <span style={{ fontSize: '1.2rem' }}>{showCalculator ? '▼' : '▶'}</span>
  </div>
  {showCalculator && (
    <SampleSizeCalculatorForm
      metric={metricSelection.custom_metric}
      testParams={formData}
      onCalculate={(result) => {
        console.log('Sample size calculated:', result);
      }}
    />
  )}
</div>

            <div className="form-actions-horizontal">
              <button type="button" className="add-btn" onClick={addMetric}>
                + Добавить метрику
              </button>
            </div>
          </div>

          <div className="metrics-list">
            <h4>Добавленные метрики:</h4>
            {formData.metrics.length === 0 ? (
              <p className="no-items">Нет добавленных метрик</p>
            ) : (
              formData.metrics.map((metric, index) => {
                return (
                  <div key={index} className="metric-item">
                    <div className="metric-info">
                      <div className="metric-header">
                        <span>{metric.custom_metric.description}</span>
                        {getPurposeBadge(metric.purpose)}
                        {metric.is_primary && <span className="primary-indicator-small">⭐</span>}
                      </div>
                      <small className="metric-type">
                        {getStatisticalTypeLabel(metric.custom_metric.statistical_type)} |
                        Распр: {metric.custom_metric.distribution} |
                        Дисп: {metric.custom_metric.variance_assumption} |
                        Выбросы: {metric.custom_metric.outliers}
                      </small>
                    </div>
                    <div className="metric-actions">
                      {metric.purpose === 'primary' && !metric.is_primary && (
                        <button
                          type="button"
                          className="set-primary-btn"
                          onClick={() => setPrimaryMetric(index)}
                          title="Сделать основной метрикой"
                        >
                          ⭐
                        </button>
                      )}
                      {metric.is_primary && <span className="primary-badge-small">Основная</span>}
                      <button
                        type="button"
                        className="remove-btn"
                        onClick={() => removeMetric(index)}
                      >
                        ✕
                      </button>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>

        <div className="form-section">
          <h2>Cплитование</h2>
          <div className="form-group">
            <label>Способы сплитования *</label>
            <select
              value={formData.data_source.source_type}
              onChange={(e) => handleDataSourceChange('source_type', e.target.value)}
            >
              <option value="internal_splitting">Сплитование нашей системой</option>
              <option value="external_splitting">Стороннее сплитование</option>
            </select>
          </div>

          {formData.data_source.source_type === 'internal_splitting' ? (
            <div className="form-group">
              <label>Выберите слой сплитования, который ближе к типу эксперимента *</label>
              <select
                value={formData.data_source.source_id}
                onChange={(e) => handleDataSourceChange('source_id', e.target.value)}
              >
                {Object.entries(availableDataSources.predefined_data_sources || {}).map(([id, source]) => (
                  <option key={id} value={id}>
                    {source.name} - {source.description}
                  </option>
                ))}
              </select>
            </div>
          ) : (
            <div className="external-source-form">
              <div className="form-group">
                <label>Название внешней системы *</label>
                <input
                  type="text"
                  value={formData.data_source.external_source_info?.name || ''}
                  onChange={(e) => handleExternalSourceChange('name', e.target.value)}
                  placeholder="Например: Google Optimize, Optimizely"
                  required
                />
              </div>
              <div className="form-group">
                <label>Описание *</label>
                <input
                  type="text"
                  value={formData.data_source.external_source_info?.description || ''}
                  onChange={(e) => handleExternalSourceChange('description', e.target.value)}
                  placeholder="Краткое описание как организовано сплитование"
                  required
                />
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label>Платформа (опционально)</label>
                  <input
                    type="text"
                    value={formData.data_source.external_source_info?.platform || ''}
                    onChange={(e) => handleExternalSourceChange('platform', e.target.value)}
                    placeholder="Например: Web, iOS, Android"
                  />
                </div>
                <div className="form-group">
                  <label>Контактное лицо (опционально)</label>
                  <input
                    type="text"
                    value={formData.data_source.external_source_info?.contact_person || ''}
                    onChange={(e) => handleExternalSourceChange('contact_person', e.target.value)}
                    placeholder="Имя ответственного"
                  />
                </div>
              </div>
              <div className="form-group">
                <label>Дополнительная информация (опционально)</label>
                <textarea
                  value={formData.data_source.external_source_info?.additional_info || ''}
                  onChange={(e) => handleExternalSourceChange('additional_info', e.target.value)}
                  placeholder="Любая дополнительная информация о сплитовании"
                  rows="3"
                />
              </div>
            </div>
          )}
        </div>


        <div className="form-actions">
          <button type="button" className="secondary-button" onClick={onNavigateToHome}>Отмена</button>
          <button type="submit" className="primary-button" disabled={loading}>
            {loading ? '⏳ Создание теста...' : '🎯 Создать A/B тест'}
          </button>
        </div>
      </form>

      {/* Модальное окно с примерами метрик */}
      {showExampleModal && (
        <div className="modal-overlay">
          <div className="modal-content" style={{ maxWidth: '600px' }}>
            <div className="modal-header">
              <h3>Выберите пример метрики</h3>
              <button className="close-btn" onClick={() => setShowExampleModal(false)}>×</button>
            </div>
            <div className="modal-body">
              <div className="metrics-list" style={{ maxHeight: '400px', overflowY: 'auto' }}>
                {Object.entries(availableMetrics.predefined_metrics || {}).map(([id, metric]) => (
                  <div
                    key={id}
                    className="metric-item"
                    onClick={() => loadExampleMetric(id)}
                    style={{ cursor: 'pointer' }}
                  >
                    <div className="metric-info">
                      <strong>{metric.description}</strong>
                      <small>Тип: {metric.metric_type} | Стат. тип: {metric.statistical_type}</small>
                    </div>
                  </div>
                ))}
              </div>
            </div>
            <div className="modal-actions">
              <button className="secondary-button" onClick={() => setShowExampleModal(false)}>
                Отмена
              </button>
            </div>
          </div>
        </div>
      )}

      {renderTestResult()}
    </div>
  );
}

// Компонент вкладки маппинга (без загрузки файлов)
function MappingTab({ experimentId, onNavigateBack }) {
  const [mappings, setMappings] = useState([]);
  const [showMappingModal, setShowMappingModal] = useState(false);
  const [editingMapping, setEditingMapping] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(null);

  const [newMapping, setNewMapping] = useState({
    experiment_id: experimentId,
    mapping_name: '',
    file_format: '',
    description: '',
    fields: [],
    is_active: true
  });

  const [newMappingField, setNewMappingField] = useState({
    input_field_name: '',
    input_field_type: 'string',
    target_field: 'user_id',
    transformation_rules: {}
  });

  const targetFields = [
    { value: 'id', label: 'ID (уникальный идентификатор)' },
    { value: 'user_id', label: 'User ID (идентификатор пользователя)' },
    { value: 'test_id', label: 'Test ID (идентификатор теста)' },
    { value: 'var_id', label: 'Var ID (идентификатор варианта)' },
    { value: 'event_name', label: 'Event Name (название события)' },
    { value: 'event_time', label: 'Event Time (время события)' },
    { value: 'event_value', label: 'Event Value (значение события)' }
  ];

  const dataTypes = [
    { value: 'string', label: 'Строка (String)' },
    { value: 'integer', label: 'Целое число (Integer)' },
    { value: 'float', label: 'Десятичное число (Float)' },
    { value: 'datetime', label: 'Дата и время (DateTime)' },
    { value: 'boolean', label: 'Булево значение (Boolean)' },
    { value: 'json', label: 'JSON объект' }
  ];

  const fetchMappings = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await fetch(`http://localhost:8000/mapping/experiment/${experimentId}`);
      if (!response.ok) {
        throw new Error(`Ошибка загрузки: ${response.status}`);
      }
      const data = await response.json();
      setMappings(data.mappings || []);
    } catch (err) {
      console.error('Ошибка загрузки схем маппинга:', err);
      setError(`Ошибка загрузки схем маппинга: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (experimentId) {
      fetchMappings();
    }
  }, [experimentId]);

  const addMappingField = () => {
    if (!newMappingField.input_field_name.trim()) {
      alert('Введите название поля входных данных');
      return;
    }

    setNewMapping(prev => ({
      ...prev,
      fields: [...prev.fields, { ...newMappingField }]
    }));

    setNewMappingField({
      input_field_name: '',
      input_field_type: 'string',
      target_field: 'user_id',
      transformation_rules: {}
    });
  };

  const removeMappingField = (index) => {
    setNewMapping(prev => ({
      ...prev,
      fields: prev.fields.filter((_, i) => i !== index)
    }));
  };

  const handleCreateMapping = async () => {
    if (!newMapping.mapping_name.trim()) {
      setError('Введите название схемы маппинга');
      return;
    }

    if (newMapping.fields.length === 0) {
      setError('Добавьте хотя бы одно поле для маппинга');
      return;
    }

    setLoading(true);
    setError('');
    setSuccess('');

    try {
      const response = await fetch('http://localhost:8000/mapping/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(newMapping),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `Ошибка: ${response.status}`);
      }

      const result = await response.json();
      setSuccess('Схема маппинга успешно создана!');

      await fetchMappings();

      setNewMapping({
        experiment_id: experimentId,
        mapping_name: '',
        file_format: '',
        description: '',
        fields: [],
        is_active: true
      });

      setShowMappingModal(false);

    } catch (err) {
      console.error('Ошибка создания схемы маппинга:', err);
      setError(`Ошибка создания схемы маппинга: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateMapping = async () => {
    if (!editingMapping) return;

    setLoading(true);
    setError('');
    setSuccess('');

    try {
      const response = await fetch(`http://localhost:8000/mapping/${editingMapping.mapping_id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          mapping_name: newMapping.mapping_name,
          file_format: newMapping.file_format,
          description: newMapping.description,
          fields: newMapping.fields,
          is_active: newMapping.is_active
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `Ошибка: ${response.status}`);
      }

      setSuccess('Схема маппинга успешно обновлена!');
      await fetchMappings();
      setShowMappingModal(false);
      setEditingMapping(null);

    } catch (err) {
      console.error('Ошибка обновления схемы маппинга:', err);
      setError(`Ошибка обновления схемы маппинга: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteMapping = async (mappingId) => {
    setLoading(true);
    try {
      const response = await fetch(`http://localhost:8000/mapping/${mappingId}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        throw new Error(`Ошибка удаления: ${response.status}`);
      }

      setSuccess('Схема маппинга успешно удалена!');
      await fetchMappings();
      setShowDeleteConfirm(null);

    } catch (err) {
      console.error('Ошибка удаления схемы маппинга:', err);
      setError(`Ошибка удаления схемы маппинга: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleEditMapping = (mapping) => {
    setEditingMapping(mapping);
    setNewMapping({
      experiment_id: experimentId,
      mapping_name: mapping.mapping_name,
      file_format: mapping.file_format || '',
      description: mapping.description || '',
      fields: mapping.fields || [],
      is_active: mapping.is_active
    });
    setShowMappingModal(true);
  };

  const renderDeleteConfirmModal = () => {
    if (!showDeleteConfirm) return null;

    return (
      <div className="modal-overlay">
        <div className="modal-content">
          <div className="modal-header">
            <h3>Подтверждение удаления</h3>
            <button className="close-btn" onClick={() => setShowDeleteConfirm(null)}>×</button>
          </div>
          <div className="modal-body">
            <p>Вы уверены, что хотите удалить схему маппинга?</p>
            <p><strong>{showDeleteConfirm.mapping_name}</strong></p>
            <p className="warning-text">Это действие невозможно отменить!</p>
          </div>
          <div className="modal-actions">
            <button
              className="secondary-button"
              onClick={() => setShowDeleteConfirm(null)}
              disabled={loading}
            >
              Отмена
            </button>
            <button
              className="danger-button"
              onClick={() => handleDeleteMapping(showDeleteConfirm.mapping_id)}
              disabled={loading}
            >
              {loading ? 'Удаление...' : 'Удалить'}
            </button>
          </div>
        </div>
      </div>
    );
  };

  const renderMappingModal = () => {
    if (!showMappingModal) return null;

    return (
      <div className="modal-overlay">
        <div className="modal-content" style={{ maxWidth: '800px' }}>
          <div className="modal-header">
            <h3>{editingMapping ? 'Редактирование схемы маппинга' : 'Создание схемы маппинга'}</h3>
            <button className="close-btn" onClick={() => { setShowMappingModal(false); setEditingMapping(null); }}>×</button>
          </div>

          <div className="modal-body">
            {error && <div className="error-message">⚠️ {error}</div>}
            {success && <div className="success-message">✅ {success}</div>}

            <div className="form-section">
              <h4>Основные параметры</h4>
              <div className="form-group">
                <label>Название схемы *</label>
                <input type="text" value={newMapping.mapping_name} onChange={(e) => setNewMapping(prev => ({ ...prev, mapping_name: e.target.value }))} placeholder="Например: Маппинг для данных Google Analytics" required />
              </div>
              <div className="form-group">
                <label>Формат файла</label>
                <input type="text" value={newMapping.file_format} onChange={(e) => setNewMapping(prev => ({ ...prev, file_format: e.target.value }))} placeholder="Например: csv, json, jsonl" />
              </div>
              <div className="form-group">
                <label>Описание</label>
                <textarea value={newMapping.description} onChange={(e) => setNewMapping(prev => ({ ...prev, description: e.target.value }))} placeholder="Описание схемы маппинга и особенностей данных" rows="3" />
              </div>
              <div className="checkbox-group">
                <input type="checkbox" id="is-active" checked={newMapping.is_active} onChange={(e) => setNewMapping(prev => ({ ...prev, is_active: e.target.checked }))} />
                <label htmlFor="is-active">Активная схема</label>
              </div>
            </div>

            <div className="form-section">
              <h4>Настройка маппинга полей</h4>
              <div className="form-row">
                <div className="form-group">
                  <label>Поле во входных данных *</label>
                  <input type="text" value={newMappingField.input_field_name} onChange={(e) => setNewMappingField(prev => ({ ...prev, input_field_name: e.target.value }))} placeholder="Например: userID, timestamp, event_type" />
                </div>
                <div className="form-group">
                  <label>Тип данных</label>
                  <select value={newMappingField.input_field_type} onChange={(e) => setNewMappingField(prev => ({ ...prev, input_field_type: e.target.value }))}>
                    {dataTypes.map(type => <option key={type.value} value={type.value}>{type.label}</option>)}
                  </select>
                </div>
                <div className="form-group">
                  <label>Целевое поле *</label>
                  <select value={newMappingField.target_field} onChange={(e) => setNewMappingField(prev => ({ ...prev, target_field: e.target.value }))}>
                    {targetFields.map(field => <option key={field.value} value={field.value}>{field.label}</option>)}
                  </select>
                </div>
              </div>
              <button type="button" className="primary-button" onClick={addMappingField} style={{ marginTop: '10px' }}>+ Добавить поле</button>
            </div>

            {newMapping.fields.length > 0 && (
              <div className="form-section">
                <h5>Добавленные поля ({newMapping.fields.length})</h5>
                <div className="mapping-fields-list">
                  {newMapping.fields.map((field, index) => (
                    <div key={index} className="mapping-field-item">
                      <div className="mapping-field-info">
                        <strong>{field.input_field_name}</strong>
                        <span className="mapping-field-type">({field.input_field_type})</span>
                        <span className="mapping-arrow">→</span>
                        <strong>{field.target_field}</strong>
                      </div>
                      <button type="button" className="remove-btn" onClick={() => removeMappingField(index)} title="Удалить поле">✕</button>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="form-section">
              <h5>Стандартная схема данных</h5>
              <div className="standard-schema-info">
                <p>Наша система использует следующую схему данных:</p>
                <ul>
                  <li><code>id</code> - уникальный идентификатор события (генерируется автоматически)</li>
                  <li><code>user_id</code> - идентификатор пользователя</li>
                  <li><code>test_id</code> - идентификатор теста (заполняется системой)</li>
                  <li><code>var_id</code> - идентификатор варианта (A, B, C...)</li>
                  <li><code>event_name</code> - название события</li>
                  <li><code>event_time</code> - время события (формат: ISO 8601)</li>
                  <li><code>event_value</code> - числовое значение события</li>
                </ul>
              </div>
            </div>
          </div>

          <div className="modal-actions">
            <button className="secondary-button" onClick={() => { setShowMappingModal(false); setEditingMapping(null); }} disabled={loading}>Отмена</button>
            <button className="primary-button" onClick={editingMapping ? handleUpdateMapping : handleCreateMapping} disabled={loading}>
              {loading ? 'Сохранение...' : (editingMapping ? 'Сохранить изменения' : 'Создать схему')}
            </button>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="mapping-tab">
      <div className="page-header">
        <button className="back-button" onClick={onNavigateBack}>← Назад к эксперименту</button>
        <h1>🗺️ Маппинг данных для эксперимента</h1>
      </div>

      {error && <div className="error-message">⚠️ {error}</div>}
      {success && <div className="success-message">✅ {success}</div>}

      <div className="mapping-content">
        <div className="mapping-header">
          <h3>Схемы маппинга ({mappings.length})</h3>
          <button className="primary-button" onClick={() => { setEditingMapping(null); setNewMapping({ experiment_id: experimentId, mapping_name: '', file_format: '', description: '', fields: [], is_active: true }); setShowMappingModal(true); }} disabled={loading}>+ Создать схему маппинга</button>
        </div>

        {loading && mappings.length === 0 ? (
          <div className="loading-message">⏳ Загрузка схем маппинга...</div>
        ) : mappings.length === 0 ? (
          <div className="empty-state">
            <p>Нет созданных схем маппинга</p>
            <p>Создайте схему маппинга, чтобы сопоставить поля ваших данных с нашей системой</p>
          </div>
        ) : (
          <div className="mappings-list">
            {mappings.map(mapping => (
              <div key={mapping.mapping_id} className="mapping-card">
                <div className="mapping-card-header">
                  <div className="mapping-title">
                    <h4>{mapping.mapping_name}</h4>
                    <span className={`status-badge ${mapping.is_active ? 'status-active' : 'status-draft'}`}>{mapping.is_active ? 'Активна' : 'Неактивна'}</span>
                  </div>
                  <div className="mapping-actions">
                    <button className="edit-btn" onClick={() => handleEditMapping(mapping)} title="Редактировать">✏️</button>
                    <button className="delete-btn" onClick={() => setShowDeleteConfirm({ mapping_id: mapping.mapping_id, mapping_name: mapping.mapping_name })} title="Удалить">🗑️</button>
                  </div>
                </div>

                <div className="mapping-details">
                  <p><strong>Формат файла:</strong> {mapping.file_format || 'Не указан'}</p>
                  <p><strong>Описание:</strong> {mapping.description || 'Не указано'}</p>
                  <p><strong>Количество полей:</strong> {mapping.fields?.length || 0}</p>
                  <p><strong>Создана:</strong> {new Date(mapping.created_at).toLocaleDateString()}</p>
                </div>

                {mapping.fields && mapping.fields.length > 0 && (
                  <div className="mapping-fields-preview">
                    <h5>Соответствия полей:</h5>
                    <div className="mapping-fields-grid">
                      {mapping.fields.map((field, idx) => (
                        <div key={idx} className="mapping-field-preview">
                          <span className="input-field">{field.input_field_name}</span>
                          <span className="arrow">→</span>
                          <span className="target-field">{field.target_field}</span>
                          <span className="field-type">({field.input_field_type})</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        <div className="mapping-help">
          <h4>ℹ️ Как работает маппинг данных?</h4>
          <div className="help-content">
            <p><strong>Маппинг данных</strong> позволяет сопоставить поля из ваших входных данных с нашей стандартной схемой для A/B тестов.</p>
            <p>Стандартная схема включает следующие поля:</p>
            <ul>
              <li><code>id</code> - уникальный идентификатор события (генерируется автоматически)</li>
              <li><code>user_id</code> - идентификатор пользователя</li>
              <li><code>test_id</code> - идентификатор теста (заполняется системой)</li>
              <li><code>var_id</code> - идентификатор варианта теста (A, B, C...)</li>
              <li><code>event_name</code> - название события (например, "purchase", "click")</li>
              <li><code>event_time</code> - время события в формате ISO 8601</li>
              <li><code>event_value</code> - числовое значение события (например, сумма покупки)</li>
            </ul>
            <p>Создайте схему маппинга, указав какие поля из ваших данных соответствуют каждому из этих стандартных полей.</p>
            <p><strong>Как использовать:</strong></p>
            <ol>
              <li>Создайте схему маппинга, указав соответствия полей</li>
              <li>На вкладке "Данные" используйте кнопку "Загрузить данные с маппингом"</li>
              <li>Выберите созданную схему маппинга при загрузке файла</li>
              <li>Система автоматически преобразует данные в соответствии с выбранной схемой</li>
            </ol>
          </div>
        </div>
      </div>

      {renderMappingModal()}
      {renderDeleteConfirmModal()}
    </div>
  );
}

// Главный компонент App
function App() {
  const [currentPage, setCurrentPage] = useState('home');
  const [createdTests, setCreatedTests] = useState([]);
  const [selectedExperiment, setSelectedExperiment] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchExperiments();
  }, []);

  const fetchExperiments = async () => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/experiments/');
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      if (data.experiments && Array.isArray(data.experiments)) {
        const experimentsWithDetails = [];
        for (const expSummary of data.experiments) {
          try {
            const detailResponse = await fetch(`http://localhost:8000/experiments/${expSummary.test_id}`);
            if (detailResponse.ok) {
              const experimentDetail = await detailResponse.json();
              experimentsWithDetails.push(experimentDetail);
            }
          } catch (err) {
            console.error(`Ошибка загрузки эксперимента ${expSummary.test_id}:`, err);
          }
        }
        setCreatedTests(experimentsWithDetails);
      }
    } catch (err) {
      console.error('Ошибка загрузки экспериментов:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleTestCreated = useCallback((test) => {
    console.log('New test created:', test);
    setCreatedTests(prev => [test, ...prev]);
    setCurrentPage('home');
    fetchExperiments();
  }, []);

  const handleOpenExperiment = useCallback((experiment) => {
    setSelectedExperiment(experiment);
    setCurrentPage('experiment');
  }, []);



  const handleDeleteExperiment = useCallback((testId) => {
    setCreatedTests(prev => prev.filter(test => test.test_id !== testId));
    fetchExperiments();
  }, []);

  const handleUpdateExperiment = useCallback((updatedExperiment) => {
    setCreatedTests(prev => prev.map(test => test.test_id === updatedExperiment.test_id ? updatedExperiment : test));
    setSelectedExperiment(updatedExperiment);
  }, []);

  const renderPage = useCallback(() => {
    switch (currentPage) {
      case 'create_test':
        return <CreateTestPage onNavigateToHome={() => setCurrentPage('home')} onTestCreated={handleTestCreated} />;

      case 'experiment':
        return <ExperimentPage experiment={selectedExperiment} onNavigateToHome={() => setCurrentPage('home')} onUpdateExperiment={handleUpdateExperiment} onDeleteExperiment={handleDeleteExperiment} />;
      case 'home':
      default:
        return <HomePage
  onNavigateToCreateTest={() => setCurrentPage('create_test')}
  onOpenExperiment={handleOpenExperiment}
  onDeleteExperiment={handleDeleteExperiment}
  createdTests={createdTests}
/>;
    }
  }, [currentPage, createdTests, selectedExperiment, handleTestCreated, handleOpenExperiment, handleDeleteExperiment, handleUpdateExperiment]);

  return (
    <div className="App">
      <div className="app-container">
        {loading && currentPage === 'home' ? (
          <div className="loading-overlay"><div className="loading-message">⏳ Загрузка экспериментов...</div></div>
        ) : (
          renderPage()
        )}
      </div>
    </div>
  );
}

export default App;