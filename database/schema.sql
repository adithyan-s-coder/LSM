-- Last-Safe-Moment Engine — MySQL Schema
CREATE DATABASE IF NOT EXISTS last_safe_moment CHARACTER SET utf8mb4;
USE last_safe_moment;

-- ============ USERS ============
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    email VARCHAR(160) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ============ ASSETS ============
CREATE TABLE IF NOT EXISTS assets (
    id INT AUTO_INCREMENT PRIMARY KEY,
    machine_id VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(150) NOT NULL,
    type VARCHAR(80) NOT NULL,
    location VARCHAR(150),
    installation_date DATE,
    operating_hours FLOAT DEFAULT 0,
    status VARCHAR(30) DEFAULT 'Normal',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ============ ASSET THRESHOLDS ============
CREATE TABLE IF NOT EXISTS asset_thresholds (
    id INT AUTO_INCREMENT PRIMARY KEY,
    asset_id INT NOT NULL,
    temperature_limit FLOAT DEFAULT 90,
    vibration_limit FLOAT DEFAULT 10,
    current_limit FLOAT DEFAULT 18,
    load_limit FLOAT DEFAULT 100,
    critical_health_threshold FLOAT DEFAULT 45,
    FOREIGN KEY (asset_id) REFERENCES assets(id) ON DELETE CASCADE
);

-- ============ SENSOR READINGS ============
CREATE TABLE IF NOT EXISTS sensor_readings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    asset_id INT NOT NULL,
    timestamp DATETIME NOT NULL,
    temperature FLOAT,
    vibration FLOAT,
    current_amp FLOAT,
    load_pct FLOAT,
    operating_hours FLOAT,
    is_anomaly TINYINT(1) DEFAULT 0,
    anomaly_score FLOAT DEFAULT 0,
    FOREIGN KEY (asset_id) REFERENCES assets(id) ON DELETE CASCADE,
    INDEX idx_asset_time (asset_id, timestamp)
);

-- ============ MAINTENANCE RECORDS ============
CREATE TABLE IF NOT EXISTS maintenance_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    asset_id INT NOT NULL,
    maintenance_type VARCHAR(100),
    scheduled_at DATETIME,
    completed_at DATETIME NULL,
    cost FLOAT DEFAULT 0,
    downtime_hours FLOAT DEFAULT 0,
    notes TEXT,
    status VARCHAR(30) DEFAULT 'Recommended',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (asset_id) REFERENCES assets(id) ON DELETE CASCADE
);

-- ============ FAILURE RECORDS ============
CREATE TABLE IF NOT EXISTS failure_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    asset_id INT NOT NULL,
    failure_date DATETIME,
    description TEXT,
    repair_cost FLOAT DEFAULT 0,
    production_loss FLOAT DEFAULT 0,
    FOREIGN KEY (asset_id) REFERENCES assets(id) ON DELETE CASCADE
);

-- ============ PREDICTIONS ============
CREATE TABLE IF NOT EXISTS predictions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    asset_id INT NOT NULL,
    health_score FLOAT,
    risk_level VARCHAR(20),
    critical_time_hours FLOAT,
    confidence FLOAT,
    deterioration_rate FLOAT,
    reasons TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (asset_id) REFERENCES assets(id) ON DELETE CASCADE,
    INDEX idx_asset_created (asset_id, created_at)
);

-- ============ INTERVENTION WINDOWS ============
CREATE TABLE IF NOT EXISTS intervention_windows (
    id INT AUTO_INCREMENT PRIMARY KEY,
    asset_id INT NOT NULL,
    prediction_id INT,
    window_start_hours FLOAT,
    window_end_hours FLOAT,
    confidence FLOAT,
    reason TEXT,
    recommendation VARCHAR(255),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (asset_id) REFERENCES assets(id) ON DELETE CASCADE,
    FOREIGN KEY (prediction_id) REFERENCES predictions(id) ON DELETE SET NULL
);

-- ============ ALERTS ============
CREATE TABLE IF NOT EXISTS alerts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    asset_id INT NOT NULL,
    severity VARCHAR(20),
    title VARCHAR(200),
    message TEXT,
    is_read TINYINT(1) DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (asset_id) REFERENCES assets(id) ON DELETE CASCADE
);

-- ============ COST MODELS ============
CREATE TABLE IF NOT EXISTS cost_models (
    id INT AUTO_INCREMENT PRIMARY KEY,
    asset_id INT NULL,
    hourly_downtime_cost FLOAT DEFAULT 2500,
    emergency_repair_cost FLOAT DEFAULT 280000,
    production_loss_per_incident FLOAT DEFAULT 520000,
    routine_maintenance_cost FLOAT DEFAULT 5000,
    delayed_maintenance_cost FLOAT DEFAULT 48000,
    FOREIGN KEY (asset_id) REFERENCES assets(id) ON DELETE CASCADE
);
