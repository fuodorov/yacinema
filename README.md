# UPD:
- .env.dev
- docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build
- http://127.0.0.1/admin/
- http://127.0.0.1/api/openapi/
- http://127.0.0.1/auth/apidocs/

Launch movies:
- docker exec movies_admin python utils/sqlite_to_postgres/load_data.py


# UPD: Для ревью спринта 7
- Ссылки: 
  - [Репозиторий проекта Auth_sprint_2](https://github.com/SamMeown/Auth_sprint_2)
  - [DeepBlue](https://github.com/BigDeepBlue)
- Добавили взаимодействие AsyncAPI и Auth сервисов. Неавторизованным пользователям, или пользователям без подписки (право 'pro_read') показываются фильмы с рейтингом не выше 7.0. Пользователям с подпиской показываются все фильмы, включая блокбастеры. При падении Auth сервиса изящно деградируем и продолжаем работать, считаем всех пользователей неавторизованными.
- Прокидываем заголовок с request-id между сервисами.
- Поправили swagger. Для нормальной работы надо заходить через nginx (то есть через порт 80), чтобы nginx добавлял заголовок с request-id [http://127.0.0.1/auth/apidocs/](http://127.0.0.1/auth/apidocs/). Ниже ссылки обновили. Аналогично надо заходить в AsyncAPI за swaggerом и для проверки взаимодействия с Auth - например [http://127.0.0.1/api/openapi](http://127.0.0.1/api/openapi)


# Terms of Reference
We further extend our cinema project by developing new Auth service. This is going to be highload service heavily used by almost all other services for user authentication and authorization validation.

## Services

### Auth
A service for users registration, authentication, authorization, validation and permissions and roles management. OpenAPI specification can be found [here](/services/movies_auth/src/docs/v1/Auth_OpenAPI_spec.yml) and when service is running can be watched in swagger at [http://127.0.0.1/auth/apidocs/](http://127.0.0.1/auth/apidocs/).

#### Utiliities
For app initialization run:  
  
```sh
$ flask app init
```
This will create base roles and permissions needed for Auth service - `all_all`(superuser) and `permissions_admin` permissions and `superuser` role. Also, it can create superuser when run with `--with-superuser` option. 

For superuser creation and deletion use:

```sh
$ flask superuser create [--email <email> --first-name <first name> --last-name <last name> --password <password>]
```
and 

```sh
$ flask superuser delete [--email <email>]
```
Both commands can work in interactive mode when run without arguments.

#### Key validation endpoints
For **access token validation** other services should use:  

```
GET /api/v1/auth_token/validation
```

with access token being checked in authorization header. In case token is valid auth service will return:

```200 { "msg": "Token is valid" }```

and in case token is expired, revoked or just invalid:

```401 { "msg": "Token has expired" }``` 

```401 { "msg": "Token has been revoked" }```  
or  
```422 { "msg": "Signature verification failed" }```  

For **user permissions validation** other services should use:

```
GET /api/v1/users/{user_id}/combined_permissions/validation?permissions=<validation query>
```  

with validation query describing condition on user permission to check, e.g. `permissions={"any":["perm_1", {"all": ["perm_2", "perm_3"]}]}` which in case of success returns:

```200 {"valid": true/false}```

Currently there is also another way to check user permission by just requesting all user permissions:

```
GET /api/v1/users/{user_id}/combined_permissions
```

All the above validation endpoints use cache and are very fast and optimized for heavy use by other services.


## Running

### Development

Uses the default Django development server.

1. Rename *.env.dev.example* to *.env.dev*.
2. Update the environment variables in the *.env.dev* file.
3. Build the images and run the containers:

    ```sh
    $ docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build
    ```

    Test it out at [http://localhost:8000](http://localhost:8000). The "movies_admin" and "movies_etl" folder is mounted into the container and your code changes apply automatically.
4. On first run, after initialising the database to fill the database with data:

   ```sh
   $ docker exec movies_admin python utils/sqlite_to_postgres/load_data.py
   ```
### Production

Uses gunicorn + nginx.

1. Rename *.env.prod.example* to *.env.prod*. 
2. Update the environment variables in the *.env.prod* file.
3. Build the images and run the containers:

    ```sh
    $ docker-compose -f docker-compose.yml -f docker-compose.prod.yml up --build
    ```

    Test it out at [http://localhost:1337](http://localhost:1337). No mounted folders. To apply changes, the image must be re-built.

4. On first run, after initialising the database to fill the database with data:

   ```sh
   $ docker exec movies_admin python utils/sqlite_to_postgres/load_data.py
   ```
## Running tests

### Auth
`docker compose exec movies_auth pytest tests`

## Technologies used

- The application runs as a WSGI/ASGI server.
- To render [static files](https://nginx.org/ru/docs/beginners_guide.html#static), **Nginx is used.
- Virtualization is done with **Docker.**.

## Main system components

1. **Server WSGI/ASGI** - server running the application.
2. **Nginx** - proxy server which is an entry point for web application.
3. **PostgreSQL** - relational data storage. 
4. **ETL** - elasticsearch.

## Project requirements

1. The application must be run via WSGI/ASGI.
2. All system components are hosted in Docker.
3. Static files are served by Nginx.

## Recommendations for the project

1. To work with WSGI/ASGI server the database uses a special user.
2. Use docker compose to communicate between containers.
