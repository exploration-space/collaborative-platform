FROM python:3
ENV PYTHONUNBUFFERED 1
RUN mkdir /code
WORKDIR /code
COPY requirements.txt /code/
RUN pip install -r requirements.txt
RUN python -m spacy download en_core_web_md
COPY . /code/

RUN curl -sL https://deb.nodesource.com/setup_10.x | bash -
RUN curl -sL https://dl.yarnpkg.com/debian/pubkey.gpg | apt-key add -
RUN echo "deb https://dl.yarnpkg.com/debian/ stable main" | tee /etc/apt/sources.list.d/yarn.list
RUN apt update && apt install -y yarn
RUN cd src/collaborative_platform/apps/overview/assets && \
yarn install && \
yarn build

EXPOSE 3000
EXPOSE 8000
STOPSIGNAL SIGINT
#ENTRYPOINT ["python", "src/collaborative_platform/manage.py"]
