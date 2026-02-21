-- =========================================
-- 1️⃣  SCHEMA
-- =========================================
CREATE SCHEMA IF NOT EXISTS app_db;

-- =========================================
-- 2️⃣  EXTENSIONS
-- =========================================
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =========================================
-- 3️⃣  USERS TABLE
-- =========================================
CREATE TABLE IF NOT EXISTS app_db.users (
    user_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    email VARCHAR NOT NULL,
    password VARCHAR NOT NULL,
    role VARCHAR,

    user_created_on TIMESTAMP WITH TIME ZONE
        NOT NULL DEFAULT NOW(),

    last_modified_on TIMESTAMP WITH TIME ZONE,

    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    theme VARCHAR(10) NOT NULL DEFAULT 'system',

    file_permission VARCHAR(10) NOT NULL DEFAULT 'none',

    CONSTRAINT role_check
        CHECK (LOWER(role) IN ('admin', 'user') OR role IS NULL)
);

-- Case-insensitive unique email
CREATE UNIQUE INDEX IF NOT EXISTS unique_users_email_lower
ON app_db.users (LOWER(email));


-- =========================================
-- 4️⃣  SUPPORT TICKETS TABLE (legacy)
-- =========================================
CREATE TABLE IF NOT EXISTS app_db."SupportTicket" (
    id SERIAL PRIMARY KEY,
    user_id UUID NULL,
    email VARCHAR(255),
    subject VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    status VARCHAR(50) NOT NULL DEFAULT 'open',
    CONSTRAINT fk_ticket_user
        FOREIGN KEY (user_id)
        REFERENCES app_db.users(user_id)
        ON DELETE SET NULL
);

-- =========================================
-- 5️⃣  NOTIFICATIONS TABLE
-- =========================================
CREATE TABLE IF NOT EXISTS app_db.notifications (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    link VARCHAR(255),

    is_global BOOLEAN NOT NULL DEFAULT FALSE,

    created_at TIMESTAMP WITH TIME ZONE
        NOT NULL DEFAULT NOW()
);


-- =========================================
-- 5️⃣  USER_NOTIFICATIONS TABLE
-- =========================================
CREATE TABLE IF NOT EXISTS app_db.user_notifications (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    user_id UUID NOT NULL,
    notification_id INTEGER NOT NULL,

    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    read_at TIMESTAMP WITH TIME ZONE,

    CONSTRAINT fk_user
        FOREIGN KEY (user_id)
        REFERENCES app_db.users(user_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_notification
        FOREIGN KEY (notification_id)
        REFERENCES app_db.notifications(id)
        ON DELETE CASCADE,

    CONSTRAINT unique_user_notification
        UNIQUE (user_id, notification_id)
);

-- =========================================
-- 6️⃣  INDEXES FOR PERFORMANCE
-- =========================================

-- Fast lookup per user
CREATE INDEX IF NOT EXISTS idx_user_notifications_user
ON app_db.user_notifications(user_id);

-- Fast lookup per notification
CREATE INDEX IF NOT EXISTS idx_user_notifications_notification
ON app_db.user_notifications(notification_id);

-- Optimized unread count queries
CREATE INDEX IF NOT EXISTS idx_user_notifications_unread
ON app_db.user_notifications(user_id)
WHERE is_read = FALSE;
