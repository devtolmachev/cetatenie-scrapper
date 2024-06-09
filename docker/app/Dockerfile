FROM python:3.12

RUN pip install poetry 

WORKDIR /app

COPY pyproject.toml /app/
RUN poetry config virtualenvs.create false
RUN poetry install --no-root --no-interaction --no-ansi

COPY . /app
EXPOSE 8000
ENTRYPOINT python3 bubble_parser/api.py
