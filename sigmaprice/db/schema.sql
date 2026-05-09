-- SigmaPrice Database Schema
-- PostgreSQL 15+
-- Version 1.0 - May 2026

-- Enable UUID extension for embeddings if needed
-- CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable pgvector extension for embeddings
CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================
-- ENUMS
-- ============================================

CREATE TYPE availability_status AS ENUM (
    'in_stock',
    'reserved',
    'on_order',
    'in_transit',
    'unavailable'
);

CREATE TYPE user_role AS ENUM (
    'admin',
    'trusted_user',
    'user'
);

CREATE TYPE feedback_status AS ENUM (
    'pending',
    'resolved',
    'rejected'
);

CREATE TYPE rule_type AS ENUM (
    'exclude_sheet',
    'exclude_category',
    'exclude_keyword',
    'price_range'
);

CREATE TYPE knowledge_base_rule_type AS ENUM (
    'suffix',
    'synonym',
    'exclusion'
);

CREATE TYPE knowledge_base_source AS ENUM (
    'ai',
    'admin',
    'user'
);

-- ============================================
-- SUPPLIERS
-- ============================================

CREATE TABLE suppliers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    country VARCHAR(100) NOT NULL,
    currency VARCHAR(3) NOT NULL,
    vat_included BOOLEAN DEFAULT FALSE,
    price_formula VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_suppliers_name ON suppliers(name);

-- ============================================
-- SUPPLIER RULES
-- ============================================

CREATE TABLE supplier_rules (
    id SERIAL PRIMARY KEY,
    supplier_id INTEGER NOT NULL REFERENCES suppliers(id) ON DELETE CASCADE,
    rule_type rule_type NOT NULL,
    rule_value VARCHAR(500) NOT NULL
);

CREATE INDEX idx_supplier_rules_supplier ON supplier_rules(supplier_id);

-- ============================================
-- SUPPLIER COLUMN MAPPING
-- ============================================

CREATE TABLE supplier_column_map (
    id SERIAL PRIMARY KEY,
    supplier_id INTEGER NOT NULL REFERENCES suppliers(id) ON DELETE CASCADE,
    our_field VARCHAR(50) NOT NULL,
    supplier_column VARCHAR(100) NOT NULL
);

CREATE INDEX idx_supplier_column_map_supplier ON supplier_column_map(supplier_id);

-- ============================================
-- CATEGORIES
-- ============================================

CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    parent_id INTEGER REFERENCES categories(id) ON DELETE SET NULL,
    sort_field VARCHAR(20) DEFAULT 'price',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_categories_parent ON categories(parent_id);
CREATE INDEX idx_categories_name ON categories(name);

-- ============================================
-- CATALOG ITEMS
-- ============================================

CREATE TABLE catalog_items (
    id SERIAL PRIMARY KEY,
    code VARCHAR(8) NOT NULL UNIQUE,
    name VARCHAR(500) NOT NULL,
    description TEXT,
    our_price DECIMAL(12, 2),
    rrp DECIMAL(12, 2),
    warranty_months INTEGER,
    manufacturer VARCHAR(200),
    article VARCHAR(100),
    ean VARCHAR(20),
    category_id INTEGER REFERENCES categories(id) ON DELETE SET NULL,
    product_url VARCHAR(500),
    country_origin VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX idx_catalog_items_code ON catalog_items(code);
CREATE INDEX idx_catalog_items_article ON catalog_items(article);
CREATE INDEX idx_catalog_items_ean ON catalog_items(ean);
CREATE INDEX idx_catalog_items_category ON catalog_items(category_id);
CREATE INDEX idx_catalog_items_name ON catalog_items(name);

-- ============================================
-- SUPPLIER ITEMS
-- ============================================

CREATE TABLE supplier_items (
    id SERIAL PRIMARY KEY,
    supplier_id INTEGER NOT NULL REFERENCES suppliers(id) ON DELETE CASCADE,
    supplier_code VARCHAR(100) NOT NULL,
    catalog_item_id INTEGER REFERENCES catalog_items(id) ON DELETE SET NULL,
    price_original DECIMAL(12, 2) NOT NULL,
    price_calculated DECIMAL(12, 2) NOT NULL,
    availability availability_status NOT NULL,
    quantity INTEGER,
    warranty_months INTEGER,
    last_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_supplier_items_supplier_code ON supplier_items(supplier_code);
CREATE INDEX idx_supplier_items_catalog_item ON supplier_items(catalog_item_id);
CREATE INDEX idx_supplier_items_supplier ON supplier_items(supplier_id);

-- ============================================
-- SUPPLIER ITEM MAPPING
-- ============================================

CREATE TABLE supplier_item_mapping (
    id SERIAL PRIMARY KEY,
    catalog_item_id INTEGER NOT NULL REFERENCES catalog_items(id) ON DELETE CASCADE,
    supplier_id INTEGER NOT NULL REFERENCES suppliers(id) ON DELETE CASCADE,
    supplier_code VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(catalog_item_id, supplier_id, supplier_code)
);

CREATE INDEX idx_supplier_item_mapping_lookup ON supplier_item_mapping(supplier_id, supplier_code);

-- ============================================
-- PRICE HISTORY
-- ============================================

CREATE TABLE price_history (
    id SERIAL PRIMARY KEY,
    supplier_item_id INTEGER NOT NULL REFERENCES supplier_items(id) ON DELETE CASCADE,
    price DECIMAL(12, 2) NOT NULL,
    availability availability_status NOT NULL,
    quantity INTEGER,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    upload_number INTEGER NOT NULL
);

CREATE INDEX idx_price_history_supplier_upload ON price_history(supplier_item_id, upload_number);
CREATE INDEX idx_price_history_recorded ON price_history(recorded_at);

-- ============================================
-- ITEM EMBEDDINGS (for AI matching)
-- ============================================

CREATE TABLE item_embeddings (
    id SERIAL PRIMARY KEY,
    catalog_item_id INTEGER NOT NULL REFERENCES catalog_items(id) ON DELETE CASCADE UNIQUE,
    embedding TEXT NOT NULL,
    model_version VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_item_embeddings_catalog ON item_embeddings(catalog_item_id);

-- ============================================
-- USERS
-- ============================================

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(200) NOT NULL,
    role user_role NOT NULL,
    is_trusted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

CREATE INDEX idx_users_username ON users(username);

-- ============================================
-- USER PERMISSIONS
-- ============================================

CREATE TABLE user_permissions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    category_id INTEGER REFERENCES categories(id) ON DELETE CASCADE,
    supplier_id INTEGER REFERENCES suppliers(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_user_permissions_user ON user_permissions(user_id);
CREATE INDEX idx_user_permissions_category ON user_permissions(category_id);
CREATE INDEX idx_user_permissions_supplier ON user_permissions(supplier_id);

-- ============================================
-- FEEDBACK ITEMS
-- ============================================

CREATE TABLE feedback_items (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    catalog_item_id INTEGER REFERENCES catalog_items(id) ON DELETE SET NULL,
    comment TEXT NOT NULL,
    status feedback_status DEFAULT 'pending',
    ai_resolution TEXT,
    admin_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP
);

CREATE INDEX idx_feedback_items_status ON feedback_items(status);
CREATE INDEX idx_feedback_items_user ON feedback_items(user_id);
CREATE INDEX idx_feedback_items_catalog ON feedback_items(catalog_item_id);

-- ============================================
-- KNOWLEDGE BASE
-- ============================================

CREATE TABLE knowledge_base (
    id SERIAL PRIMARY KEY,
    rule_type knowledge_base_rule_type NOT NULL,
    pattern VARCHAR(200) NOT NULL,
    resolution VARCHAR(500) NOT NULL,
    source knowledge_base_source NOT NULL,
    confidence DECIMAL(5, 2) DEFAULT 1.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_knowledge_base_pattern ON knowledge_base(pattern);
CREATE INDEX idx_knowledge_base_rule_type ON knowledge_base(rule_type);

-- ============================================
-- FUNCTIONS
-- ============================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for suppliers
CREATE TRIGGER suppliers_updated_at
    BEFORE UPDATE ON suppliers
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

-- Trigger for catalog_items
CREATE TRIGGER catalog_items_updated_at
    BEFORE UPDATE ON catalog_items
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();