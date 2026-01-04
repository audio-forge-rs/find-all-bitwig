-- bwctl database schema
-- PostgreSQL 16+ with pg_trgm for fuzzy search

-- Extensions
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS unaccent;

-- Content Types
CREATE TYPE content_type AS ENUM (
    'preset',
    'clip',
    'sample',
    'multisample',
    'impulse',
    'curve',
    'wavetable',
    'device',
    'plugin',
    'template',
    'project'
);

-- Device Types
CREATE TYPE device_type AS ENUM (
    'instrument',
    'audio_fx',
    'note_fx',
    'modulator',
    'container',
    'utility'
);

-- Packages (Sound Packs)
CREATE TABLE packages (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(255) NOT NULL,
    vendor          VARCHAR(255) NOT NULL,
    version         VARCHAR(50),
    path            TEXT NOT NULL UNIQUE,
    installed_at    TIMESTAMP DEFAULT NOW(),
    is_factory      BOOLEAN DEFAULT FALSE,

    search_vector   TSVECTOR GENERATED ALWAYS AS (
        setweight(to_tsvector('english', coalesce(name, '')), 'A') ||
        setweight(to_tsvector('english', coalesce(vendor, '')), 'B')
    ) STORED
);

-- Main Content Table
CREATE TABLE content (
    id              SERIAL PRIMARY KEY,

    -- Identity
    name            VARCHAR(500) NOT NULL,
    file_path       TEXT NOT NULL UNIQUE,
    content_type    content_type NOT NULL,

    -- Relationships
    package_id      INTEGER REFERENCES packages(id) ON DELETE SET NULL,
    parent_device   VARCHAR(255),

    -- Metadata
    description     TEXT,
    category        VARCHAR(255),
    subcategory     VARCHAR(255),
    tags            TEXT[],
    creator         VARCHAR(255),

    -- Technical Details
    device_type     device_type,
    device_uuid     UUID,
    plugin_id       VARCHAR(255),

    -- Audio Properties (for samples)
    sample_rate     INTEGER,
    channels        SMALLINT,
    duration_ms     INTEGER,
    bpm             DECIMAL(6,2),
    key_signature   VARCHAR(10),

    -- File Info
    file_size       BIGINT,
    file_hash       VARCHAR(64),
    modified_at     TIMESTAMP,
    indexed_at      TIMESTAMP DEFAULT NOW(),

    -- Full-text Search (populated by trigger)
    search_vector   TSVECTOR
);

-- Trigger function to update search_vector
CREATE OR REPLACE FUNCTION content_search_vector_update() RETURNS trigger AS $$
BEGIN
    NEW.search_vector :=
        setweight(to_tsvector('english', coalesce(NEW.name, '')), 'A') ||
        setweight(to_tsvector('english', coalesce(NEW.description, '')), 'B') ||
        setweight(to_tsvector('english', coalesce(NEW.category, '')), 'C') ||
        setweight(to_tsvector('english', coalesce(array_to_string(NEW.tags, ' '), '')), 'C') ||
        setweight(to_tsvector('english', coalesce(NEW.creator, '')), 'D') ||
        setweight(to_tsvector('english', coalesce(NEW.parent_device, '')), 'B');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER content_search_vector_trigger
    BEFORE INSERT OR UPDATE ON content
    FOR EACH ROW EXECUTE FUNCTION content_search_vector_update();

-- Collections
CREATE TABLE collections (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(255) NOT NULL UNIQUE,
    description     TEXT,
    is_smart        BOOLEAN DEFAULT FALSE,
    query           JSONB,
    created_at      TIMESTAMP DEFAULT NOW()
);

CREATE TABLE collection_items (
    collection_id   INTEGER REFERENCES collections(id) ON DELETE CASCADE,
    content_id      INTEGER REFERENCES content(id) ON DELETE CASCADE,
    added_at        TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (collection_id, content_id)
);

-- Usage History
CREATE TABLE usage_history (
    id              SERIAL PRIMARY KEY,
    content_id      INTEGER REFERENCES content(id) ON DELETE CASCADE,
    action          VARCHAR(50) NOT NULL,
    context         JSONB,
    used_at         TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_content_search ON content USING GIN(search_vector);
CREATE INDEX idx_packages_search ON packages USING GIN(search_vector);
CREATE INDEX idx_content_name_trgm ON content USING GIN(name gin_trgm_ops);
CREATE INDEX idx_content_category_trgm ON content USING GIN(category gin_trgm_ops);
CREATE INDEX idx_content_tags ON content USING GIN(tags);
CREATE INDEX idx_content_type ON content(content_type);
CREATE INDEX idx_content_device_type ON content(device_type);
CREATE INDEX idx_content_package ON content(package_id);
CREATE INDEX idx_content_parent_device ON content(parent_device);
CREATE INDEX idx_content_type_category ON content(content_type, category);

-- Search Function
CREATE OR REPLACE FUNCTION search_content(
    query_text TEXT,
    filter_type content_type DEFAULT NULL,
    filter_device_type device_type DEFAULT NULL,
    filter_category TEXT DEFAULT NULL,
    filter_package_id INTEGER DEFAULT NULL,
    filter_parent_device TEXT DEFAULT NULL,
    limit_results INTEGER DEFAULT 50,
    offset_results INTEGER DEFAULT 0
)
RETURNS TABLE (
    id INTEGER,
    name VARCHAR,
    content_type content_type,
    category VARCHAR,
    parent_device VARCHAR,
    file_path TEXT,
    package_name VARCHAR,
    relevance REAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        c.id,
        c.name,
        c.content_type,
        c.category,
        c.parent_device,
        c.file_path,
        p.name as package_name,
        (
            COALESCE(ts_rank(c.search_vector, websearch_to_tsquery('english', query_text)), 0) * 0.5 +
            COALESCE(similarity(c.name, query_text), 0) * 0.3 +
            COALESCE(similarity(COALESCE(c.parent_device, ''), query_text), 0) * 0.2
        )::REAL as relevance
    FROM content c
    LEFT JOIN packages p ON c.package_id = p.id
    WHERE
        (filter_type IS NULL OR c.content_type = filter_type)
        AND (filter_device_type IS NULL OR c.device_type = filter_device_type)
        AND (filter_category IS NULL OR c.category ILIKE '%' || filter_category || '%')
        AND (filter_package_id IS NULL OR c.package_id = filter_package_id)
        AND (filter_parent_device IS NULL OR c.parent_device ILIKE '%' || filter_parent_device || '%')
        AND (
            query_text IS NULL
            OR query_text = ''
            OR c.search_vector @@ websearch_to_tsquery('english', query_text)
            OR c.name % query_text
            OR c.name ILIKE '%' || query_text || '%'
            OR c.parent_device ILIKE '%' || query_text || '%'
        )
    ORDER BY relevance DESC, c.name
    LIMIT limit_results
    OFFSET offset_results;
END;
$$ LANGUAGE plpgsql;

-- Autocomplete Function
CREATE OR REPLACE FUNCTION autocomplete_content(
    partial_text TEXT,
    limit_results INTEGER DEFAULT 10
)
RETURNS TABLE (
    suggestion TEXT,
    content_type content_type,
    match_count BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        c.name::TEXT as suggestion,
        c.content_type,
        COUNT(*)::BIGINT as match_count
    FROM content c
    WHERE c.name ILIKE partial_text || '%'
    GROUP BY c.name, c.content_type
    ORDER BY match_count DESC, c.name
    LIMIT limit_results;
END;
$$ LANGUAGE plpgsql;

-- Stats View
CREATE VIEW content_stats AS
SELECT
    content_type,
    COUNT(*) as count,
    COUNT(DISTINCT package_id) as packages,
    COUNT(DISTINCT parent_device) as devices
FROM content
GROUP BY content_type;
