FROM python:3.13-slim

RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip setuptools wheel

RUN pip install --no-cache-dir \
    pandas==2.3.2\
    geopandas==1.1.1\
    shapely==2.1.1 \
    scikit-learn==1.7.2\
    joblib==1.5.2 \
    matplotlib==3.10.6 \
    requests==2.32.5
