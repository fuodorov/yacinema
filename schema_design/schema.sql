-- Schemes
CREATE SCHEMA IF NOT EXISTS content;

-- Enums
CREATE TYPE content.film_team_role AS ENUM ('director', 'writer', 'actor');
CREATE TYPE content.film_work_types AS ENUM ('movie', 'series', 'tv-show');
CREATE TYPE content.genre_name_type AS ENUM (
    'Adventure', 'Animation', 'Biography', 'Comedy', 'Crime', 'Documentary', 'Drama', 'Family', 'Fantasy', 'Game-Show',
    'History','Horror', 'Music', 'Musical', 'Mystery', 'News', 'Reality-TV', 'Romance', 'Sci-Fi', 'Short', 'Sport',
    'Talk-Show', 'Thriller', 'War', 'Western'
    );

-- UUID
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Tables
CREATE TABLE IF NOT EXISTS content.film_work (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    creation_date DATE,
    certificate TEXT,
    file_path TEXT,
    rating FLOAT,
    type content.film_work_types,
    created_at TIMESTAMP with time zone,
    updated_at TIMESTAMP with time zone
);
CREATE TABLE IF NOT EXISTS content.genre (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    name content.genre_name_type,
    description TEXT,
    created_at TIMESTAMP with time zone,
    updated_at TIMESTAMP with time zone
);
CREATE TABLE IF NOT EXISTS content.person (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    full_name VARCHAR(255) NOT NULL,
    birthdate DATE,
    created_at TIMESTAMP with time zone,
    updated_at TIMESTAMP with time zone
);
CREATE TABLE IF NOT EXISTS content.film_work_genre (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    film_work_id UUID REFERENCES content.film_work (id),
    genre_id UUID REFERENCES content.genre (id),
    created_at TIMESTAMP with time zone,
    updated_at TIMESTAMP with time zone
);
CREATE TABLE IF NOT EXISTS content.film_work_person (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    film_work_id UUID REFERENCES content.film_work (id),
    person_id UUID REFERENCES content.person (id),
    role content.film_team_role,
    created_at TIMESTAMP with time zone,
    updated_at TIMESTAMP with time zone
);

-- INDEXES
CREATE UNIQUE INDEX film_work_genre ON content.film_work_genre (film_work_id, genre_id);
CREATE UNIQUE INDEX film_work_person_role ON content.film_work_person (film_work_id, person_id, role);