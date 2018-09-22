FROM continuumio/anaconda:latest
ADD . /app
WORKDIR /app

ARG PORT
ARG REDIS_URL
ENV PORT $PORT
ENV REDIS_URL $REDIS_URL

# Set up apt-get
RUN apt-get update -qq && apt-get install -yqq gnupg curl libgl1-mesa-glx gcc

# Install nodejs
RUN curl -sL https://deb.nodesource.com/setup_9.x | bash
RUN apt-get install -yqq nodejs
RUN apt-get clean -y

# Install sciris
RUN git clone https://github.com/optimamodel/sciris.git
RUN cd sciris && git checkout develop && python setup.py develop && python setup-web.py develop

# Install mpld3
RUN git clone https://github.com/optimamodel/mpld3.git
RUN cd mpld3 && python setup.py submodule && python setup.py install

# Install hptool
RUN python setup.py develop

# Install app
WORKDIR client
RUN python install_client.py
RUN python build_client.py

CMD python start_server.py
