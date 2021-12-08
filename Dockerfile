FROM python:3.8
LABEL maintainer Prasanta Kakati <prasantakakati1994@gmail.com>
RUN apt-get update && \
    apt-get install --yes build-essential curl
RUN mkdir /ekata-gateway-processor-backend
WORKDIR /ekata-gateway-processor-backend
RUN curl -sSL https://raw.githubusercontent.com/sdispater/poetry/master/get-poetry.py | python
COPY pyproject.toml poetry.lock /ekata-gateway-processor-backend/
RUN . $HOME/.poetry/env && \
    poetry config virtualenvs.create false && \
    poetry install --no-dev
COPY . /ekata-gateway-processor-backend
CMD [ "sh", "start.sh" ]
