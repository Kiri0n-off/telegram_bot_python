FROM python:3.12.2-slim
WORKDIR /code
RUN apt-get update \
    && apt-get -y install libpq-dev gcc
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
RUN mkdir /logs_ps
EXPOSE 5000
COPY . .
CMD ["python", "bot.py"]
