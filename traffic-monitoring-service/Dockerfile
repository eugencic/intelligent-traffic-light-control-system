#FROM python:3.9
FROM tensorflow/tensorflow:2.7.0-gpu
WORKDIR /app

COPY . /app
RUN pip install --no-cache-dir numpy
RUN apt-get update && apt-get install -y libsm6
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "-u", "main.py"]
