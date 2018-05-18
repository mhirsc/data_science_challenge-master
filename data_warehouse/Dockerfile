FROM python:2.7

RUN mkdir -p /app/data_warehouse

COPY ./data_warehouse/requirements.txt /app/data_warehouse/requirements.txt
RUN pip install --upgrade pip && pip install -r /app/data_warehouse/requirements.txt

COPY ./data_warehouse /app/data_warehouse

WORKDIR /app/data_warehouse
ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PORT=5000
EXPOSE 5000
