FROM continuumio/anaconda:latest

ARG PORT
ARG REDIS_URL
ARG CLIENT_DIR 

ENV PORT $PORT
ENV REDIS_URL $REDIS_URL
ENV CLIENT_DIR $CLIENT_DIR

RUN apt-get update \
  && apt-get install -y python3-pip python3-dev \
  && cd /usr/local/bin \
  && ln -s /usr/bin/python3 python \
  && pip3 install --upgrade pip

# Set up apt-get
RUN apt-get update -y 

RUN apt-get install -y apt-utils gnupg curl libgl1-mesa-glx gcc redis-server 

RUN apt-get install -y python3-matplotlib

RUN apt-get install -y freetype*

RUN mkdir /app

ADD requirements.txt /app

WORKDIR /app

# Install sciris
RUN pip3 install -r requirements.txt

ADD . /app

# Install mpld3
RUN git clone https://github.com/sciris/mpld3.git
RUN cd mpld3 && python3 setup.py submodule && python3 setup.py install

# Install atomica
RUN python3 setup.py develop

RUN pip3 uninstall -y redis
RUN pip3 install redis==2.10.6 
