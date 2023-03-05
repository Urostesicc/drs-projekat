FROM python:3.9.7
WORKDIR /app
COPY . /app

RUN pip install -r requirements.txt

EXPOSE 5000

CMD ["flask","--app","FlaskAPI","--debug","run","--host=0.0.0.0","--port","5000"]