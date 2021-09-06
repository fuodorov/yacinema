import os
import psycopg2


if __name__ == "__main__":
    dsl = {
        'dbname': os.getenv('DB_NAME', 'movies'),
        'user': os.getenv('DB_USER', 'postgres'),
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': os.getenv('DB_PORT', '5432'),
        'password': os.getenv('DB_PASSWORD', 'postgres'),
    }

    SQL = """
    CREATE SCHEMA IF NOT EXISTS content;
    
    CREATE TABLE IF NOT EXISTS content.genre (
        id UUID PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        description TEXT,
        created TIMESTAMP WITH TIME ZONE,
        modified TIMESTAMP WITH TIME ZONE
    );

    CREATE TABLE IF NOT EXISTS content.film_work (
        id UUID PRIMARY KEY,
        title VARCHAR(255) NOT NULL,
        description TEXT,
        creation_date DATE,
        certificate VARCHAR(255),
        file_path VARCHAR(255),
        rating FLOAT,
        type VARCHAR(255) NOT NULL,
        created TIMESTAMP WITH TIME ZONE,
        modified TIMESTAMP WITH TIME ZONE
    );
    
    CREATE TABLE IF NOT EXISTS content.person (
        id UUID PRIMARY KEY,
        full_name VARCHAR(255) NOT NULL,
        birth_date DATE,
        created TIMESTAMP WITH TIME ZONE,
        modified TIMESTAMP WITH TIME ZONE
    );
    
    CREATE TABLE IF NOT EXISTS content.genre_film_work (
        id UUID PRIMARY KEY,
        film_work_id uuid NOT NULL,
        genre_id uuid NOT NULL,
        created TIMESTAMP WITH TIME ZONE
    );
    
    CREATE TABLE IF NOT EXISTS content.person_film_work (
        id UUID PRIMARY KEY,
        film_work_id UUID NOT NULL,
        person_id UUID NOT NULL,
        role TEXT NOT NULL,
        created TIMESTAMP WITH TIME ZONE
    );
    
    CREATE UNIQUE INDEX film_work_genre ON content.genre_film_work (film_work_id, genre_id);
    CREATE UNIQUE INDEX film_work_person_role ON content.person_film_work (film_work_id, person_id, role);
    """

    with psycopg2.connect(**dsl) as conn, conn.cursor() as cursor:
        cursor.execute(SQL)
