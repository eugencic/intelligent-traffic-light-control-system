FROM python:3.10.7

WORKDIR /app

COPY . /app

COPY requirements.txt .
RUN pip install --trusted-host pypi.python.org -r requirements.txt

EXPOSE 8000

CMD ["python", "-u", "main.py", "--port", "8000"]
