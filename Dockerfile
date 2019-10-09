FROM python:3
ENV PYTHONUNBUFFERED 1
RUN mkdir /code
WORKDIR /code
COPY requirements.txt /code/
RUN pip install -r requirements.txt
RUN python -m spacy download en_core_web_md
COPY . /code/

EXPOSE 8000
STOPSIGNAL SIGINT
#ENTRYPOINT ["python", "src/collaborative_platform/manage.py"]
