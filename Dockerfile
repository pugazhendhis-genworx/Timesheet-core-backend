FROM python:3.11

WORKDIR /app

COPY requirements/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "src.api.rest.app:app", "--host", "0.0.0.0", "--port", "8000"]
