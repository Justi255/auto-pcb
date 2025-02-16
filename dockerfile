FROM pytorch/pytorch:2.2.1-cuda11.8-cudnn8-devel as base

# Installs system dependencies.
RUN apt-get update \
        && apt-get install -y \
            flex \
            libcairo2-dev \
            libboost-all-dev \
            openjdk-17-jdk \
            curl \
            zip \
            cmake

# Installs sdk && gradle
RUN curl -s "https://get.sdkman.io" | bash
RUN /bin/bash -c "source $HOME/.sdkman/bin/sdkman-init.sh \
        && sdk -version \
        && sdk install gradle 8.6 \
        && gradle -version"

# Installs system dependencies from conda.
RUN conda install -y -c conda-forge bison

# Installs python dependencies. 
RUN pip install \
        pyunpack>=0.1.2 \
        patool>=1.12 \
        matplotlib>=2.2.2 \
        cairocffi>=0.9.0 \
        pkgconfig>=1.4.0 \
        setuptools>=39.1.0 \
        scipy>=1.1.0 \
        'numpy>=1.20.0,<=1.23.0'\
        shapely>=1.7.0 \
        imageio \
        tabulate \
        pygmo>=2.16.1 \
        pyDOE2>=1.3.0 \
        shap>=0.41.0 \
        Pyro4>=4.82 \
        ConfigSpace>=0.6.0 \
        statsmodels>=0.13.2 \
        xgboost>=1.5.1 

ENV DEBIAN_FRONTEND=noninteractive
# kicad runtime dependencies    
RUN apt-get install -y \
        libglew2.2 \
        # libpython3.10 \
        # python3 \
        # libcurl4 \
        software-properties-common
RUN add-apt-repository ppa:kicad/kicad-7.0-releases \
        && apt update \
        && apt-get install -y \
        libwxgtk3.2* \
        libocct-modeling-algorithms-7.6 \
        libocct-modeling-data-7.6 \
        libocct-data-exchange-7.6 \
        libocct-visualization-7.6 \
        libocct-foundation-7.6 \
        libocct-ocaf-7.6

COPY ./thirdparty/kicad/lib /usr/lib

WORKDIR /

FROM base as inside-docker-local
# Copy files to the working directory
COPY . /auto-pcb
WORKDIR /auto-pcb