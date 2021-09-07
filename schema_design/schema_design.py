import os
import psycopg2


if __name__ == "__main__":
    dsl = {
        'dbname': os.getenv('DB_NAME'),
        'user': os.getenv('DB_USER'),
        'host': os.getenv('DB_HOST'),
        'port': os.getenv('DB_PORT'),
        'password': os.getenv('DB_PASSWORD'),
    }

    SQL = """
    CREATE SCHEMA IF NOT EXISTS content;
    
    CREATE TYPE content.film_team_role AS ENUM ('director', 'writer', 'actor');

    CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

    CREATE TABLE IF NOT EXISTS content.film_work (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        title TEXT NOT NULL,
        description TEXT,
        creation_date DATE,
        certificate TEXT,
        file_path TEXT,
        rating FLOAT,
        type TEXT NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE,
        updated_at TIMESTAMP WITH TIME ZONE
    );
    
    CREATE TABLE IF NOT EXISTS content.genre (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        name TEXT NOT NULL UNIQUE,
        description TEXT,
        created_at TIMESTAMP WITH TIME ZONE,
        updated_at TIMESTAMP WITH TIME ZONE
    );
    
    CREATE TABLE IF NOT EXISTS content.genre_film_work (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        film_work_id UUID REFERENCES content.film_work (id) NOT NULL,
        genre_id UUID REFERENCES content.genre (id) NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE
    );
    
    CREATE TABLE IF NOT EXISTS content.person (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        full_name TEXT NOT NULL,
        birth_date DATE,
        created_at TIMESTAMP WITH TIME ZONE,
        updated_at TIMESTAMP WITH TIME ZONE
    );
    
    CREATE TABLE IF NOT EXISTS content.person_film_work (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        film_work_id UUID REFERENCES content.film_work (id) NOT NULL,
        person_id UUID REFERENCES content.person (id) NOT NULL,
        role content.film_team_role NOT NULL,
        created_at TIMESTAMP with time zone
    );

    CREATE UNIQUE INDEX film_work_genre ON content.genre_film_work (film_work_id, genre_id);
    
    CREATE UNIQUE INDEX film_work_person_role ON content.person_film_work (film_work_id, person_id, role);    
    """

    with psycopg2.connect(**dsl) as conn, conn.cursor() as cursor:
        cursor.execute(SQL)
