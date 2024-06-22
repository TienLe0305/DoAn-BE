
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