import os
import psycopg2


if __name__ == "__main__":
    SCHEMA = os.environ.get('DB_SCHEMA', 'content')

    dsl = {
        'dbname': os.environ.get('DB_NAME', 'movies'),
        'user': os.environ.get('DB_USER', 'postgres'),
        'host': os.environ.get('DB_HOST', 'localhost'),
        'port': os.environ.get('DB_PORT', '5432'),
        'password': os.environ.get('DB_PASSWORD', 'postgres'),
    }

    SQL = f"""    
    CREATE SCHEMA IF NOT EXISTS {SCHEMA};
    
    CREATE TABLE IF NOT EXISTS {SCHEMA}.genre (
        id UUID PRIMARY KEY,
        name TEXT NOT NULL,
        description TEXT,
        created TIMESTAMP WITH TIME ZONE,
        modified TIMESTAMP WITH TIME ZONE
    );

    CREATE TABLE IF NOT EXISTS {SCHEMA}.film_work (
        id UUID PRIMARY KEY,
        title TEXT NOT NULL,
        description TEXT,
        creation_date DATE,
        certificate TEXT,
        file_path TEXT,
        rating FLOAT,
        type TEXT NOT NULL,
        created TIMESTAMP WITH TIME ZONE,
        modified TIMESTAMP WITH TIME ZONE
    );
    
    CREATE TABLE IF NOT EXISTS {SCHEMA}.person (
        id UUID PRIMARY KEY,
        full_name TEXT NOT NULL,
        birth_date DATE,
        created TIMESTAMP WITH TIME ZONE,
        modified TIMESTAMP WITH TIME ZONE
    );
    
    CREATE TABLE IF NOT EXISTS {SCHEMA}.person_film_work (
        id UUID PRIMARY KEY,
        film_work_id UUID NOT NULL,
        person_id UUID NOT NULL,
        role TEXT NOT NULL,
        created TIMESTAMP WITH TIME ZONE
    );
    
    CREATE TABLE IF NOT EXISTS {SCHEMA}.genre_film_work (
        id UUID PRIMARY KEY,
        film_work_id UUID NOT NULL,
        genre_id UUID NOT NULL,
        created TIMESTAMP WITH TIME ZONE
    );
    
    CREATE UNIQUE INDEX film_work_genre ON {SCHEMA}.genre_film_work (film_work_id, genre_id);
    CREATE UNIQUE INDEX film_work_person_role ON {SCHEMA}.person_film_work (film_work_id, person_id, role);
    """

    with psycopg2.connect(**dsl) as conn, conn.cursor() as cursor:
        try:
            cursor.execute(SQL)
            print(f'Schema {SCHEMA} is created.')
        except psycopg2.errors.DuplicateTable as e:
            print(f'Schema {SCHEMA} already exists.')
    conn.close()
