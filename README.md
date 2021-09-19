# Terms of Reference

As a second task, we suggest extending the admin panel project: run the application via WSGI/ASGI, configure static file uploads via Nginx, and prepare the infrastructure to work with Docker.

## Running

### Development

Uses the default Django development server.

1. Rename *.env.dev-sample* to *.env.dev*.
1. Update the environment variables in the *docker-compose.dev.yml* and *.env.dev* files.
1. Build the images and run the containers:

    ```sh
    $ docker-compose -f docker-compose.dev.yml up
    ```

    Test it out at [http://localhost:8000](http://localhost:8000). The "movies_admin" folder is mounted into the container and your code changes apply automatically.

### Production

Uses gunicorn + nginx.

1. Rename *.env.prod-sample* to *.env.prod* and *.env.prod.db-sample* to *.env.prod.db*. Update the environment variables.
1. Build the images and run the containers:

    ```sh
    $ docker-compose -f docker-compose.prod.yml up
    ```

    Test it out at [http://localhost:1337](http://localhost:1337). No mounted folders. To apply changes, the image must be re-built.

## Technologies used

- The application runs as a WSGI/ASGI server.
- To render [static files](https://nginx.org/ru/docs/beginners_guide.html#static), **Nginx is used.
- Virtualization is done with **Docker.**.

## Main system components

1. **Server WSGI/ASGI** - server running the application.
2. **Nginx** - proxy server which is an entry point for web application.
3. **PostgreSQL** - relational data storage. 

## Project requirements

1. The application must be run via WSGI/ASGI.
2. All system components are hosted in Docker.
3. Static files are served by Nginx.

## Recommendations for the project

1. To work with WSGI/ASGI server the database uses a special user.
2. Use docker compose to communicate between containers.
