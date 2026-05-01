-- ElectaVerse Database Schema
-- All master data lives here. Nothing hardcoded in the application.

CREATE DATABASE IF NOT EXISTS electaverse;
USE electaverse;

-- ─────────────────────────────────────────────
-- AUTHENTICATION & USERS
-- ─────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('voter', 'official', 'observer') DEFAULT 'voter',
    constituency_id VARCHAR(10),
    last_login DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sessions (
    token VARCHAR(64) PRIMARY KEY,
    user_id INT NOT NULL,
    expires_at DATETIME NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- ─────────────────────────────────────────────
-- MASTER DATA
-- ─────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS constituencies (
    id VARCHAR(10) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    state VARCHAR(50) NOT NULL,
    lat DECIMAL(10,4) NOT NULL,
    lng DECIMAL(10,4) NOT NULL,
    total_registered_voters INT DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS booths (
    id VARCHAR(20) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    constituency_id VARCHAR(10) NOT NULL,
    lat DECIMAL(10,4) NOT NULL,
    lng DECIMAL(10,4) NOT NULL,
    registered_voters INT DEFAULT 1200,
    base_throughput DECIMAL(5,1) DEFAULT 25.0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (constituency_id) REFERENCES constituencies(id)
);

-- ─────────────────────────────────────────────
-- REAL-TIME / TRANSACTIONAL DATA
-- ─────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS incidents (
    id VARCHAR(20) PRIMARY KEY,
    booth_id VARCHAR(20) NOT NULL,
    incident_type VARCHAR(30) NOT NULL,
    severity ENUM('critical','high','medium','low') NOT NULL,
    description TEXT NOT NULL,
    status ENUM('open','triaging','resolved') DEFAULT 'open',
    ai_recommendation TEXT,
    ai_severity_override VARCHAR(10),
    reported_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    resolved_at DATETIME NULL,
    resolution_notes TEXT,
    estimated_resolution_minutes INT DEFAULT 0,
    FOREIGN KEY (booth_id) REFERENCES booths(id)
);

CREATE TABLE IF NOT EXISTS turnout_snapshots (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tick INT NOT NULL,
    sim_time VARCHAR(10) NOT NULL,
    phase VARCHAR(20) NOT NULL,
    total_votes INT NOT NULL,
    total_registered INT NOT NULL,
    turnout_percent DECIMAL(5,2) NOT NULL,
    avg_queue_length DECIMAL(5,1) NOT NULL,
    open_incidents INT DEFAULT 0,
    recorded_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS agent_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    agent_name VARCHAR(30) NOT NULL,
    action_type VARCHAR(30) NOT NULL,
    input_summary TEXT,
    output_summary TEXT,
    booth_id VARCHAR(20) NULL,
    confidence DECIMAL(3,2) DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (booth_id) REFERENCES booths(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS chat_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    user_message TEXT NOT NULL,
    agent_used VARCHAR(30),
    ai_response TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS fact_checks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    claim TEXT NOT NULL,
    verdict ENUM('True','Misleading','False','Unverifiable') NOT NULL,
    confidence INT DEFAULT 0,
    reasoning TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS battle_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    topic VARCHAR(255) NOT NULL,
    persona_a VARCHAR(100) NOT NULL,
    persona_b VARCHAR(100) NOT NULL,
    debate_transcript TEXT,
    winner VARCHAR(100),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ─────────────────────────────────────────────
-- CONTENT (serves Timeline + Voter Guide — zero hardcoded UI text)
-- ─────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS election_phases (
    id INT AUTO_INCREMENT PRIMARY KEY,
    phase_key VARCHAR(30) NOT NULL UNIQUE,
    title VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    icon VARCHAR(10) NOT NULL DEFAULT '📋',
    start_label VARCHAR(50) NOT NULL,
    end_label VARCHAR(50) NOT NULL,
    duration_info VARCHAR(100) NOT NULL,
    key_activities JSON NOT NULL,
    role_actions JSON NOT NULL COMMENT '{"voter":[],"official":[],"observer":[]}',
    display_order INT NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS voter_guide_steps (
    id INT AUTO_INCREMENT PRIMARY KEY,
    step_number INT NOT NULL,
    title VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    icon VARCHAR(10) NOT NULL DEFAULT '📋',
    documents_required JSON COMMENT '["Voter ID","Aadhaar"]',
    tips JSON COMMENT '["Arrive early","Carry pen"]',
    role_specific_notes JSON NOT NULL COMMENT '{"voter":"...","official":"...","observer":"..."}',
    sim_phase_link VARCHAR(30) DEFAULT NULL COMMENT 'Links to simulation phase for real-time highlight',
    display_order INT NOT NULL DEFAULT 0
);

-- ─────────────────────────────────────────────
-- CONFIGURATION (replaces hardcoded values)
-- ─────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS simulation_config (
    config_key VARCHAR(50) PRIMARY KEY,
    config_value VARCHAR(255) NOT NULL,
    description VARCHAR(255)
);

INSERT INTO simulation_config (config_key, config_value, description) VALUES
('tick_interval_seconds', '3', 'How often the simulation updates (real seconds)'),
('simulated_minutes_per_tick', '2', 'How many simulated minutes pass per tick'),
('election_start_hour', '7', 'Polling starts at this hour'),
('election_end_hour', '18', 'Polling ends at this hour'),
('base_arrival_rate', '3.0', 'Average voters arriving per 10-min window'),
('base_throughput', '25', 'Voters processed per hour per booth'),
('throughput_variance', '5', 'Plus/minus variance in throughput')
ON DUPLICATE KEY UPDATE config_value = VALUES(config_value);

CREATE TABLE IF NOT EXISTS incident_config (
    incident_type VARCHAR(30) PRIMARY KEY,
    base_probability DECIMAL(8,5) NOT NULL,
    default_severity ENUM('critical','high','medium','low') NOT NULL,
    description_templates JSON NOT NULL
);

INSERT INTO incident_config (incident_type, base_probability, default_severity, description_templates) VALUES
('EVM_MALFUNCTION', 0.00080, 'critical', '["EVM unit not responding to button presses","EVM display showing error code E-402","EVM ballot unit disconnected from control unit","EVM producing beeping sound, votes not registering"]'),
('VVPAT_JAM', 0.00050, 'high', '["VVPAT paper slip not printing after vote cast","VVPAT paper jam — machine halted","VVPAT showing incorrect candidate name on slip"]'),
('VOTER_ID_DISPUTE', 0.00400, 'medium', '["Voter name on roll does not match ID card spelling","Voter claims to be registered but not found in electoral roll","Photo mismatch between voter ID and person at booth","Voter presenting expired identification document"]'),
('CROWD_CONTROL', 0.00100, 'high', '["Queue exceeding booth premises, blocking road access","Verbal altercation between voters in queue","Unauthorized persons attempting to enter booth area"]'),
('ACCESSIBILITY_ISSUE', 0.00150, 'medium', '["Wheelchair-bound voter unable to access booth entrance","Elderly voter requesting assistance not available","Visually impaired voter — Braille ballot not available"]'),
('POWER_OUTAGE', 0.00030, 'critical', '["Complete power failure at booth — no backup generator","Intermittent power supply causing EVM resets","Generator fuel running low — estimated 30 minutes remaining"]')
ON DUPLICATE KEY UPDATE base_probability = VALUES(base_probability);

CREATE TABLE IF NOT EXISTS peak_multipliers (
    hour INT PRIMARY KEY,
    multiplier DECIMAL(3,1) NOT NULL
);

INSERT INTO peak_multipliers (hour, multiplier) VALUES
(7, 1.2), (8, 2.0), (9, 2.5), (10, 2.2),
(11, 1.5), (12, 1.0), (13, 0.8), (14, 1.0),
(15, 1.5), (16, 2.0), (17, 2.5), (18, 1.0)
ON DUPLICATE KEY UPDATE multiplier = VALUES(multiplier);

CREATE TABLE IF NOT EXISTS fact_check_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    claim TEXT NOT NULL,
    verdict VARCHAR(50) NOT NULL,
    confidence_score INT NOT NULL,
    reasoning TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS voter_iq_scores (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    score INT NOT NULL,
    total_questions INT NOT NULL,
    rank_title VARCHAR(100) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);
