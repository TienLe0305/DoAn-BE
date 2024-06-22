# Run DoAn-BE with Docker

This project demonstrates how to run the backend of a Chrome extension chatbot assistant, developed using FastAPI and MongoDB, with Docker.

## Prerequisites

Make sure you have the following installed on your machine:

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)

## Project Structure

```
.
├── docker-compose.yml
├── Dockerfile
├── app
│   ├── __init__.py
│   ├── .env
│   ├── main.py
│   ├── config.py
│   ├── routes.py
│   ├── models.py
│   ├── database.py
│   ├── auth.py
│   ├── chat.py
│   ├── image.py
│   ├── pdf.py
│   ├── rag.py
│   ├── utils.py
│   ├── web.py
├── requirements.txt
└── README.md
```

## Getting Started

Follow these instructions to set up and run the project.

### Clone the Repository

```bash
git clone https://github.com/TienLe0305/DoAn-BE/tree/master
cd DoAn-BE
```

### Environment Configuration

Create a `.env` file in the `app` directory with the necessary environment variables. An example `.env` file could look like this:

```env
CLIENT_ID=1080662676746-s5ps31peevt9jns27u8r92l106phn80a.apps.googleusercontent.com
CLIENT_SECRET=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
MONGODB_URI=mongodb+srv://lvt030501:JVNn9027TH9xEkVG@doan.dfzs6wb.mongodb.net/?retryWrites=true&w=majority&appName=DOAN
OPENAI_API_KEY =
REDIRECT_URI=http://127.0.0.1:8002/ext/auth/code
```

## Docker Compose Setup

The `docker-compose.yml` file defines the services for the FastAPI backend and MongoDB database.

```yaml
version: '4'
services:
  backend:
    build: .
    ports:
      - "8002:8002"
    environment:
      - MONGODB_URI=mongodb://mongodb:27017/DoAn
      - REDIRECT_URI=http://127.0.0.1:8002/ext/auth/code
    depends_on:
      - mongodb

  mongodb:
    image: mongo
    ports:
      - "27017:27017"
    volumes:
      - mongodb_data:/data/db

volumes:
  mongodb_data:
```

## Dockerfile Setup

The `Dockerfile` sets up the FastAPI application environment.

```Dockerfile
FROM python:3.12
WORKDIR /app
COPY ./requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt
COPY ./app/__init__.py /app/
COPY ./app/.env /app/
COPY ./app/main.py /app/
COPY ./app/config.py /app/
COPY ./app/routes.py /app/
COPY ./app/models.py /app/
COPY ./app/database.py /app/
COPY ./app/auth.py /app/
COPY ./app/chat.py /app/
COPY ./app/image.py /app/
COPY ./app/pdf.py /app/
COPY ./app/rag.py /app/
COPY ./app/utils.py /app/
COPY ./app/web.py /app/
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002"]
```

## Running the Application

To run the FastAPI application with Docker, follow these steps:

1. **Build and Start the Containers**

    Open your terminal and navigate to the project directory. Run the following command to build and start the containers:

    ```bash
    docker-compose up --build
    ```

2. **Access the Application**

    Once the containers are up and running, you can access the FastAPI application at:

    ```
    http://127.0.0.1:8002
    ```

3. **Stop the Containers**

    To stop the running containers, press `Ctrl + C` in the terminal where you ran `docker-compose up`, or run the following command in another terminal:

    ```bash
    docker-compose down
    ```

## Additional Notes

- The `backend` service is dependent on the `mongodb` service, which means MongoDB will be started first.
- The MongoDB data is stored in a Docker volume named `mongodb_data`, which ensures data persistence across container restarts.

## Troubleshooting

- If you encounter issues, make sure Docker and Docker Compose are correctly installed.
- Check the logs for any errors using:

    ```bash
    docker-compose logs
    ```

- Ensure that the port `8002` and `27017` are not being used by other applications on your machine.

## Conclusion

This setup allows you to quickly get a FastAPI application up and running with a MongoDB backend using Docker.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/)
- [Docker](https://www.docker.com/)
- [MongoDB](https://www.mongodb.com/)
