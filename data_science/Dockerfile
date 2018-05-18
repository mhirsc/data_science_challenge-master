FROM python:2.7

RUN mkdir -p /app/data_science

COPY ./data_science/requirements.txt /app/data_science/requirements.txt
RUN pip install --upgrade pip && pip install -r /app/data_science/requirements.txt

COPY ./data_science /app/data_science

WORKDIR /app/data_science
ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1