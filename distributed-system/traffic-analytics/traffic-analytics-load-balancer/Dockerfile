FROM python:3.10.7

WORKDIR /app

COPY . .

COPY requirements.txt .
RUN pip install --trusted-host pypi.python.org -r requirements.txt

EXPOSE 7000

CMD ["python", "-u", "main.py", "--port", "7000"]
