FROM python:3.9.7
WORKDIR /app
COPY . /app

RUN pip install -r requirements.txt

CMD ["flask","--app","Engine","--debug","run","--host=0.0.0.0","--port","5001"]