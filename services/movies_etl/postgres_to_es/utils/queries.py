def movies_query(offset: int) -> str:
    movies_query = f"""SELECT
                            fw.id as fw_id, 
                            fw.title, 
                            fw.description, 
                            fw.rating, 
                            fw.type, 
                            fw.created, 
                            fw.modified, 
                            pfw.role, 
                            p.id, 
                            p.full_name,
                            g.name,
                            g.id as g_id
                        FROM content.film_work fw
                        LEFT JOIN content.person_film_work pfw ON pfw.film_work_id = fw.id
                        LEFT JOIN content.person p ON p.id = pfw.person_id
                        LEFT JOIN content.genre_film_work gfw ON gfw.film_work_id = fw.id
                        LEFT JOIN content.genre g ON g.id = gfw.genre_id
                        ORDER BY fw.modified DESC
                        LIMIT 100 
                        OFFSET {offset};"""
    return movies_query


def genres_query(offset: int) -> str:
    genres_query = f"""SELECT
                            g.name,
                            g.id as g_id,
                            fw.id as fw_id
                        FROM content.genre g
                        LEFT JOIN content.genre_film_work gfw ON gfw.genre_id = g.id
                        LEFT JOIN content.film_work fw ON fw.id = gfw.film_work_id
                        ORDER BY g.modified DESC
                        LIMIT 100 
                        OFFSET {offset};"""
    return genres_query


def persons_query(offset: int) -> str:
    persons_query = f"""SELECT
                            p.full_name,
                            p.id as p_id,
                            fw.id as fw_id,
                            pfw.role as person_role
                        FROM content.person p
                        LEFT JOIN content.person_film_work pfw ON pfw.person_id = p.id
                        LEFT JOIN content.film_work fw ON fw.id = pfw.film_work_id
                        ORDER BY p.modified DESC
                        LIMIT 100 
                        OFFSET {offset};"""
    return persons_query
