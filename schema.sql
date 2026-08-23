-- CareMind AI
-- MySQL 8.x schema
-- Version: 2.1
-- English-only MVP foundation

CREATE DATABASE IF NOT EXISTS caremind_ai
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE caremind_ai;

CREATE TABLE roles (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE users (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NULL,
    phone VARCHAR(30) NULL,
    role_id BIGINT UNSIGNED NOT NULL,
    status ENUM('active','inactive','suspended','pending') NOT NULL DEFAULT 'active',
    last_login_at TIMESTAMP NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_users_role FOREIGN KEY (role_id) REFERENCES roles(id)
) ENGINE=InnoDB;

CREATE TABLE user_profiles (
    user_id BIGINT UNSIGNED PRIMARY KEY,
    date_of_birth DATE NULL,
    gender ENUM('male','female','other','prefer_not_to_say') NULL,
    avatar_url VARCHAR(500) NULL,
    timezone VARCHAR(100) NOT NULL DEFAULT 'UTC',
    emergency_notes TEXT NULL,
    allergies TEXT NULL,
    medical_history TEXT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_profiles_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE doctors (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT UNSIGNED NOT NULL UNIQUE,
    license_number VARCHAR(150) NULL,
    specialty VARCHAR(150) NULL,
    bio TEXT NULL,
    consultation_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_doctors_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE care_circles (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    owner_user_id BIGINT UNSIGNED NOT NULL,
    name VARCHAR(150) NOT NULL DEFAULT 'My Care Circle',
    status ENUM('active','archived') NOT NULL DEFAULT 'active',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_circles_owner FOREIGN KEY (owner_user_id) REFERENCES users(id)
) ENGINE=InnoDB;

CREATE TABLE care_circle_members (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    care_circle_id BIGINT UNSIGNED NOT NULL,
    user_id BIGINT UNSIGNED NOT NULL,
    relationship_type ENUM('patient','daughter','son','spouse','parent','sibling','relative','caregiver','doctor','other') NOT NULL,
    member_status ENUM('active','invited','removed') NOT NULL DEFAULT 'invited',
    joined_at TIMESTAMP NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_circle_user (care_circle_id, user_id),
    CONSTRAINT fk_circle_members_circle FOREIGN KEY (care_circle_id) REFERENCES care_circles(id) ON DELETE CASCADE,
    CONSTRAINT fk_circle_members_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE doctor_patient_relationships (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    doctor_id BIGINT UNSIGNED NOT NULL,
    patient_user_id BIGINT UNSIGNED NOT NULL,
    status ENUM('pending','active','revoked','ended') NOT NULL DEFAULT 'pending',
    started_at TIMESTAMP NULL,
    ended_at TIMESTAMP NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_doctor_patient (doctor_id, patient_user_id),
    CONSTRAINT fk_dpr_doctor FOREIGN KEY (doctor_id) REFERENCES doctors(id) ON DELETE CASCADE,
    CONSTRAINT fk_dpr_patient FOREIGN KEY (patient_user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE consents (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    patient_user_id BIGINT UNSIGNED NOT NULL,
    grantee_user_id BIGINT UNSIGNED NOT NULL,
    resource_type ENUM(
        'health_metrics','health_reports','medications','medication_adherence',
        'symptoms','activities','sleep','mood','appointments',
        'doctor_consultation','care_plan','posts','emergency_events'
    ) NOT NULL,
    permission ENUM('view','share','manage') NOT NULL DEFAULT 'view',
    status ENUM('granted','revoked','expired') NOT NULL DEFAULT 'granted',
    expires_at TIMESTAMP NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_consents_patient (patient_user_id),
    INDEX idx_consents_grantee (grantee_user_id),
    CONSTRAINT fk_consents_patient FOREIGN KEY (patient_user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_consents_grantee FOREIGN KEY (grantee_user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE health_metrics (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    patient_user_id BIGINT UNSIGNED NOT NULL,
    metric_type ENUM('blood_pressure','heart_rate','blood_glucose','spo2','temperature','weight') NOT NULL,
    recorded_at DATETIME NOT NULL,
    source ENUM('manual','device','imported','doctor') NOT NULL DEFAULT 'manual',
    notes VARCHAR(500) NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_health_metrics_patient_time (patient_user_id, recorded_at),
    CONSTRAINT fk_health_metrics_patient FOREIGN KEY (patient_user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE blood_pressure_records (
    health_metric_id BIGINT UNSIGNED PRIMARY KEY,
    systolic SMALLINT UNSIGNED NOT NULL,
    diastolic SMALLINT UNSIGNED NOT NULL,
    pulse SMALLINT UNSIGNED NULL,
    CONSTRAINT fk_bp_metric FOREIGN KEY (health_metric_id) REFERENCES health_metrics(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE heart_rate_records (
    health_metric_id BIGINT UNSIGNED PRIMARY KEY,
    bpm SMALLINT UNSIGNED NOT NULL,
    CONSTRAINT fk_hr_metric FOREIGN KEY (health_metric_id) REFERENCES health_metrics(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE glucose_records (
    health_metric_id BIGINT UNSIGNED PRIMARY KEY,
    value DECIMAL(7,2) NOT NULL,
    unit ENUM('mg_dL','mmol_L') NOT NULL,
    measurement_context ENUM('fasting','before_meal','after_meal','random','other') NULL,
    CONSTRAINT fk_glucose_metric FOREIGN KEY (health_metric_id) REFERENCES health_metrics(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE spo2_records (
    health_metric_id BIGINT UNSIGNED PRIMARY KEY,
    percentage DECIMAL(5,2) NOT NULL,
    CONSTRAINT fk_spo2_metric FOREIGN KEY (health_metric_id) REFERENCES health_metrics(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE temperature_records (
    health_metric_id BIGINT UNSIGNED PRIMARY KEY,
    value DECIMAL(5,2) NOT NULL,
    unit ENUM('celsius','fahrenheit') NOT NULL,
    CONSTRAINT fk_temp_metric FOREIGN KEY (health_metric_id) REFERENCES health_metrics(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE weight_records (
    health_metric_id BIGINT UNSIGNED PRIMARY KEY,
    value DECIMAL(7,2) NOT NULL,
    unit ENUM('kg','lb') NOT NULL,
    CONSTRAINT fk_weight_metric FOREIGN KEY (health_metric_id) REFERENCES health_metrics(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE medicines (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    patient_user_id BIGINT UNSIGNED NOT NULL,
    prescribed_by_doctor_id BIGINT UNSIGNED NULL,
    name VARCHAR(200) NOT NULL,
    dosage VARCHAR(100) NULL,
    instructions TEXT NULL,
    start_date DATE NULL,
    end_date DATE NULL,
    status ENUM('active','paused','completed','cancelled') NOT NULL DEFAULT 'active',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_medicines_patient_status (patient_user_id, status),
    CONSTRAINT fk_medicines_patient FOREIGN KEY (patient_user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_medicines_doctor FOREIGN KEY (prescribed_by_doctor_id) REFERENCES doctors(id) ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE medication_schedules (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    medicine_id BIGINT UNSIGNED NOT NULL,
    scheduled_time TIME NOT NULL,
    frequency ENUM('daily','weekly','custom') NOT NULL DEFAULT 'daily',
    days_of_week VARCHAR(20) NULL,
    reminder_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    grace_period_minutes INT UNSIGNED NOT NULL DEFAULT 60,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_med_schedule_medicine FOREIGN KEY (medicine_id) REFERENCES medicines(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE medication_logs (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    medication_schedule_id BIGINT UNSIGNED NOT NULL,
    scheduled_for DATETIME NOT NULL,
    status ENUM('pending','taken','missed','delayed','skipped') NOT NULL DEFAULT 'pending',
    confirmed_at DATETIME NULL,
    confirmed_by_user_id BIGINT UNSIGNED NULL,
    notes VARCHAR(500) NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_med_log_schedule_time (medication_schedule_id, scheduled_for),
    INDEX idx_med_logs_status_time (status, scheduled_for),
    CONSTRAINT fk_med_logs_schedule FOREIGN KEY (medication_schedule_id) REFERENCES medication_schedules(id) ON DELETE CASCADE,
    CONSTRAINT fk_med_logs_confirmed_by FOREIGN KEY (confirmed_by_user_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE health_reports (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    patient_user_id BIGINT UNSIGNED NOT NULL,
    uploaded_by_user_id BIGINT UNSIGNED NOT NULL,
    title VARCHAR(255) NOT NULL,
    file_url VARCHAR(1000) NOT NULL,
    file_type VARCHAR(100) NOT NULL,
    file_size_bytes BIGINT UNSIGNED NULL,
    report_date DATE NULL,
    processing_status ENUM('uploaded','processing','completed','failed') NOT NULL DEFAULT 'uploaded',
    ai_summary TEXT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_reports_patient_date (patient_user_id, report_date),
    CONSTRAINT fk_reports_patient FOREIGN KEY (patient_user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_reports_uploader FOREIGN KEY (uploaded_by_user_id) REFERENCES users(id)
) ENGINE=InnoDB;

CREATE TABLE report_results (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    health_report_id BIGINT UNSIGNED NOT NULL,
    test_name VARCHAR(255) NOT NULL,
    result_value VARCHAR(100) NULL,
    unit VARCHAR(50) NULL,
    reference_range VARCHAR(100) NULL,
    flag ENUM('normal','high','low','critical','unknown') NOT NULL DEFAULT 'unknown',
    confidence DECIMAL(5,4) NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_report_results_report (health_report_id),
    CONSTRAINT fk_report_results_report FOREIGN KEY (health_report_id) REFERENCES health_reports(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE symptoms (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    patient_user_id BIGINT UNSIGNED NOT NULL,
    symptom VARCHAR(255) NOT NULL,
    severity ENUM('mild','moderate','severe','unknown') NOT NULL DEFAULT 'unknown',
    description TEXT NULL,
    started_at DATETIME NULL,
    ended_at DATETIME NULL,
    reported_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    source ENUM('patient','caregiver','doctor','ai') NOT NULL DEFAULT 'patient',
    INDEX idx_symptoms_patient_time (patient_user_id, reported_at),
    CONSTRAINT fk_symptoms_patient FOREIGN KEY (patient_user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE activities (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    patient_user_id BIGINT UNSIGNED NOT NULL,
    activity_type ENUM('walking','running','gym','cycling','swimming','yoga','other') NOT NULL,
    duration_minutes INT UNSIGNED NULL,
    steps INT UNSIGNED NULL,
    calories INT UNSIGNED NULL,
    activity_date DATETIME NOT NULL,
    notes VARCHAR(500) NULL,
    source ENUM('manual','device','imported') NOT NULL DEFAULT 'manual',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_activities_patient_date (patient_user_id, activity_date),
    CONSTRAINT fk_activities_patient FOREIGN KEY (patient_user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE sleep_records (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    patient_user_id BIGINT UNSIGNED NOT NULL,
    sleep_start DATETIME NULL,
    sleep_end DATETIME NULL,
    duration_minutes INT UNSIGNED NULL,
    quality ENUM('poor','fair','good','excellent','unknown') NOT NULL DEFAULT 'unknown',
    source ENUM('manual','device','imported') NOT NULL DEFAULT 'manual',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_sleep_patient_start (patient_user_id, sleep_start),
    CONSTRAINT fk_sleep_patient FOREIGN KEY (patient_user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE mood_records (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    patient_user_id BIGINT UNSIGNED NOT NULL,
    mood ENUM('great','good','okay','not_great','bad') NOT NULL,
    note VARCHAR(500) NULL,
    recorded_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_mood_patient FOREIGN KEY (patient_user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE water_records (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    patient_user_id BIGINT UNSIGNED NOT NULL,
    amount_ml INT UNSIGNED NOT NULL,
    recorded_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_water_patient FOREIGN KEY (patient_user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE posts (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    author_user_id BIGINT UNSIGNED NOT NULL,
    care_circle_id BIGINT UNSIGNED NULL,
    content TEXT NOT NULL,
    media_url VARCHAR(1000) NULL,
    activity_id BIGINT UNSIGNED NULL,
    visibility ENUM('private','care_circle','selected_users') NOT NULL DEFAULT 'care_circle',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_posts_author_time (author_user_id, created_at),
    CONSTRAINT fk_posts_author FOREIGN KEY (author_user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_posts_circle FOREIGN KEY (care_circle_id) REFERENCES care_circles(id) ON DELETE SET NULL,
    CONSTRAINT fk_posts_activity FOREIGN KEY (activity_id) REFERENCES activities(id) ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE post_comments (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    post_id BIGINT UNSIGNED NOT NULL,
    author_user_id BIGINT UNSIGNED NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_comments_post FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE,
    CONSTRAINT fk_comments_author FOREIGN KEY (author_user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE post_reactions (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    post_id BIGINT UNSIGNED NOT NULL,
    user_id BIGINT UNSIGNED NOT NULL,
    reaction_type ENUM('like','love','care','celebrate') NOT NULL DEFAULT 'like',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_post_reaction (post_id, user_id),
    CONSTRAINT fk_reactions_post FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE,
    CONSTRAINT fk_reactions_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE conversations (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    type ENUM('family','doctor_patient','care_team','ai') NOT NULL,
    care_circle_id BIGINT UNSIGNED NULL,
    patient_user_id BIGINT UNSIGNED NULL,
    title VARCHAR(255) NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_conversations_circle FOREIGN KEY (care_circle_id) REFERENCES care_circles(id) ON DELETE SET NULL,
    CONSTRAINT fk_conversations_patient FOREIGN KEY (patient_user_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE conversation_members (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    conversation_id BIGINT UNSIGNED NOT NULL,
    user_id BIGINT UNSIGNED NOT NULL,
    joined_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_read_at DATETIME NULL,
    UNIQUE KEY uq_conversation_member (conversation_id, user_id),
    CONSTRAINT fk_conversation_members_conversation FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE,
    CONSTRAINT fk_conversation_members_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE messages (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    conversation_id BIGINT UNSIGNED NOT NULL,
    sender_user_id BIGINT UNSIGNED NULL,
    message_type ENUM('text','image','file','voice','system') NOT NULL DEFAULT 'text',
    content TEXT NULL,
    attachment_url VARCHAR(1000) NULL,
    sent_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    edited_at DATETIME NULL,
    deleted_at DATETIME NULL,
    INDEX idx_messages_conversation_time (conversation_id, sent_at),
    CONSTRAINT fk_messages_conversation FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE,
    CONSTRAINT fk_messages_sender FOREIGN KEY (sender_user_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE appointments (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    patient_user_id BIGINT UNSIGNED NOT NULL,
    doctor_id BIGINT UNSIGNED NOT NULL,
    appointment_type ENUM('chat','voice','video','in_person') NOT NULL,
    scheduled_start DATETIME NOT NULL,
    scheduled_end DATETIME NULL,
    status ENUM('requested','confirmed','completed','cancelled','no_show') NOT NULL DEFAULT 'requested',
    notes TEXT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_appointments_patient_time (patient_user_id, scheduled_start),
    INDEX idx_appointments_doctor_time (doctor_id, scheduled_start),
    CONSTRAINT fk_appointments_patient FOREIGN KEY (patient_user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_appointments_doctor FOREIGN KEY (doctor_id) REFERENCES doctors(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE doctor_care_plans (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    patient_user_id BIGINT UNSIGNED NOT NULL,
    doctor_id BIGINT UNSIGNED NOT NULL,
    title VARCHAR(255) NOT NULL,
    instructions TEXT NOT NULL,
    start_date DATE NULL,
    end_date DATE NULL,
    status ENUM('active','completed','cancelled') NOT NULL DEFAULT 'active',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_care_plans_patient FOREIGN KEY (patient_user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_care_plans_doctor FOREIGN KEY (doctor_id) REFERENCES doctors(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE emergency_contacts (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    patient_user_id BIGINT UNSIGNED NOT NULL,
    contact_user_id BIGINT UNSIGNED NULL,
    name VARCHAR(200) NOT NULL,
    phone VARCHAR(30) NOT NULL,
    relationship VARCHAR(100) NULL,
    priority TINYINT UNSIGNED NOT NULL DEFAULT 1,
    is_primary BOOLEAN NOT NULL DEFAULT FALSE,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_emergency_contacts_patient_priority (patient_user_id, priority),
    CONSTRAINT fk_emergency_contacts_patient FOREIGN KEY (patient_user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_emergency_contacts_user FOREIGN KEY (contact_user_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE emergency_events (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    patient_user_id BIGINT UNSIGNED NOT NULL,
    trigger_type ENUM('manual_sos','voice','symptom','system') NOT NULL,
    severity ENUM('unknown','low','moderate','high','critical') NOT NULL DEFAULT 'unknown',
    status ENUM('initiated','confirmed','escalated','resolved','cancelled') NOT NULL DEFAULT 'initiated',
    latitude DECIMAL(10,7) NULL,
    longitude DECIMAL(10,7) NULL,
    location_accuracy_m DECIMAL(8,2) NULL,
    description TEXT NULL,
    initiated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    resolved_at DATETIME NULL,
    INDEX idx_emergency_patient_time (patient_user_id, initiated_at),
    INDEX idx_emergency_status (status),
    CONSTRAINT fk_emergency_events_patient FOREIGN KEY (patient_user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE emergency_logs (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    emergency_event_id BIGINT UNSIGNED NOT NULL,
    action_type ENUM('location_captured','contact_notified','call_started','hospital_viewed','directions_opened','event_cancelled','event_resolved') NOT NULL,
    target_user_id BIGINT UNSIGNED NULL,
    metadata JSON NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_emergency_logs_event_time (emergency_event_id, created_at),
    CONSTRAINT fk_emergency_logs_event FOREIGN KEY (emergency_event_id) REFERENCES emergency_events(id) ON DELETE CASCADE,
    CONSTRAINT fk_emergency_logs_target FOREIGN KEY (target_user_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE ai_conversations (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT UNSIGNED NOT NULL,
    title VARCHAR(255) NULL,
    status ENUM('active','archived') NOT NULL DEFAULT 'active',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_ai_conversations_user_time (user_id, updated_at),
    CONSTRAINT fk_ai_conversations_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE ai_messages (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    conversation_id BIGINT UNSIGNED NOT NULL,
    sender_type ENUM('user','assistant','system') NOT NULL,
    content LONGTEXT NOT NULL,
    model VARCHAR(100) NULL,
    tokens_used INT UNSIGNED NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_ai_messages_conversation_time (conversation_id, created_at),
    CONSTRAINT fk_ai_messages_conversation FOREIGN KEY (conversation_id) REFERENCES ai_conversations(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE ai_insights (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    patient_user_id BIGINT UNSIGNED NOT NULL,
    insight_type ENUM('trend','medication','activity','wellbeing','report','safety','general') NOT NULL,
    severity ENUM('info','attention','urgent') NOT NULL DEFAULT 'info',
    title VARCHAR(255) NOT NULL,
    summary TEXT NOT NULL,
    source_context JSON NULL,
    status ENUM('new','seen','dismissed','resolved') NOT NULL DEFAULT 'new',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_ai_insights_patient_status (patient_user_id, status, created_at),
    CONSTRAINT fk_ai_insights_patient FOREIGN KEY (patient_user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE risk_scores (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    patient_user_id BIGINT UNSIGNED NOT NULL,
    score DECIMAL(6,2) NULL,
    level ENUM('stable','needs_attention','urgent') NOT NULL,
    factors JSON NULL,
    calculated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_risk_scores_patient_time (patient_user_id, calculated_at),
    CONSTRAINT fk_risk_scores_patient FOREIGN KEY (patient_user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE notifications (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    recipient_user_id BIGINT UNSIGNED NOT NULL,
    type ENUM('medicine','health','message','doctor','activity','emergency','system') NOT NULL,
    title VARCHAR(255) NOT NULL,
    body TEXT NOT NULL,
    related_entity_type VARCHAR(100) NULL,
    related_entity_id BIGINT UNSIGNED NULL,
    priority ENUM('low','normal','high','critical') NOT NULL DEFAULT 'normal',
    status ENUM('unread','read','dismissed') NOT NULL DEFAULT 'unread',
    sent_at DATETIME NULL,
    read_at DATETIME NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_notifications_recipient_status (recipient_user_id, status, created_at),
    CONSTRAINT fk_notifications_recipient FOREIGN KEY (recipient_user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE audit_logs (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    actor_user_id BIGINT UNSIGNED NULL,
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(100) NOT NULL,
    entity_id BIGINT UNSIGNED NULL,
    metadata JSON NULL,
    ip_address VARCHAR(45) NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_audit_entity (entity_type, entity_id),
    INDEX idx_audit_actor_time (actor_user_id, created_at),
    CONSTRAINT fk_audit_actor FOREIGN KEY (actor_user_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB;

INSERT INTO roles (name) VALUES
('elder'),
('family'),
('caregiver'),
('doctor'),
('admin')
ON DUPLICATE KEY UPDATE name = VALUES(name);

-- End of schema.
