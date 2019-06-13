FROM continuumio/anaconda3:latest

RUN apt-get update -y

RUN python3 -m ensurepip

# Set up apt-get

RUN apt-get install -y apt-utils gnupg curl libgl1-mesa-glx gcc redis-server supervisor

RUN apt-get install -y freetype*

ADD . /app
WORKDIR /app

RUN python3 -m pip install celery==4.2.2 # Because Celery 4.3 is broken

ARG PORT
ARG REDIS_URL
ENV PORT $PORT
ENV REDIS_URL $REDIS_URL

# Install nodejs
RUN curl -sL https://deb.nodesource.com/setup_9.x | bash
RUN apt-get install -yqq nodejs
RUN apt-get clean -y

# Install sciris
RUN git clone https://github.com/sciris/sciris.git
RUN cd sciris && python setup.py develop
RUN git clone https://github.com/sciris/scirisweb.git
RUN cd scirisweb && python setup.py develop

# Install mpld3
RUN git clone https://github.com/sciris/mpld3.git
RUN cd mpld3 && python3 setup.py submodule && python3 setup.py install

# Install Optima Nutrition
RUN python3 setup.py develop

# Install app
WORKDIR client
RUN python3 install_client.py
RUN python3 build_client.py

CMD /etc/init.d/redis-server start && supervisord
