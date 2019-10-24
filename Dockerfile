FROM python:3
ENV PYTHONUNBUFFERED 1
RUN mkdir /code
WORKDIR /code
COPY requirements.txt /code/
RUN apt update
RUN apt install -y python3-gdal
RUN pip install -r requirements.txt
COPY . /code/

EXPOSE 8000
STOPSIGNAL SIGINT
#ENTRYPOINT ["python", "src/collaborative_platform/manage.py"]
