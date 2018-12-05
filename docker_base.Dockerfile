# Stages:
#   base_image : Common base image, both for the builder and for the final image.
#                This contains only minimal dependencies required in both cases
#                for miniconda and the makefile.
#   builder    : stage in which the conda envrionment is created
#                and dependencies are installed
#   final      : the final image containing only the required environment files,
#                and none of the infrastructure required to generate them.

FROM debian:stable-slim AS base_image

ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8
ENV LANGUAGE en_US.UTF-8

ENV CONDA_DIR /opt/conda
ENV PATH $CONDA_DIR/bin:$PATH
ENV SHELL /bin/bash

RUN if [ $(which apk) ]; then \
        apk add --no-cache bash make sed grep gawk curl git bzip2 unzip; \
    elif [ $(which apt-get) ]; then \
        apt-get update && apt-get install --yes bash make sed grep gawk curl git bzip2 unzip; \
    else \
        echo "Invalid Distro: $(uname -a)"; \
        exit 1; \
    fi

CMD [ "/bin/bash" ]

FROM base_image AS builder

RUN if [ $(which apk) ]; then \
        apk add --no-cache ca-certificates openssh-client openssh-keygen; \
    elif [ $(which apt-get) ]; then \
        apt-get --yes install ca-certificates openssh-client; \
    else \
        echo "Invalid Distro: $(uname -a)"; \
        exit 1; \
    fi

ENV MINICONDA_VER latest
ENV MINICONDA Miniconda3-$MINICONDA_VER-Linux-x86_64.sh
ENV MINICONDA_URL https://repo.continuum.io/miniconda/$MINICONDA

RUN curl -L "$MINICONDA_URL" --silent -o miniconda3.sh && \
    /bin/bash miniconda3.sh -f -b -p $CONDA_DIR && \
    rm miniconda3.sh && \
    /opt/conda/bin/conda clean -tipsy && \
    ln -s /opt/conda/etc/profile.d/conda.sh /etc/profile.d/conda.sh && \
    echo ". /opt/conda/etc/profile.d/conda.sh" >> ~/.bashrc && \
    echo "conda activate base" >> ~/.bashrc && \
    conda update --all --yes && \
    conda config --set auto_update_conda False

# Project specific files only from here on forward

RUN mkdir /root/.ssh/ && \
    ssh-keyscan gitlab.com >> /root/.ssh/known_hosts && \
    ssh-keyscan registry.gitlab.com >> /root/.ssh/known_hosts

ARG SSH_PRIVATE_RSA_KEY
ENV ENV_SSH_PRIVATE_RSA_KEY=${SSH_PRIVATE_RSA_KEY}

# Write private key and generate public key
RUN if [[ "$ENV_SSH_PRIVATE_RSA_KEY" ]]; then \
    echo -n "-----BEGIN RSA PRIVATE KEY-----" >> /root/.ssh/id_rsa && \
    echo -n ${ENV_SSH_PRIVATE_RSA_KEY} \
    | sed 's/-----BEGIN RSA PRIVATE KEY-----//' \
    | sed 's/-----END RSA PRIVATE KEY-----//' \
    | sed 's/ /\n/g' \
    >> /root/.ssh/id_rsa && \
    echo -n "-----END RSA PRIVATE KEY-----" >> /root/.ssh/id_rsa && \
    chmod 600 /root/.ssh/* && \
    ssh-keygen -y -f /root/.ssh/id_rsa > /root/.ssh/id_rsa.pub; \
    fi

ADD requirements/ requirements/
ADD scripts/ scripts/

ADD makefile.extra.make makefile.extra.make
ADD makefile.config.make makefile.config.make
ADD makefile makefile

RUN make install

RUN rm -f /root/.ssh/id_rsa

# Deleting pkgs implies that `conda install`
# will at have to pull all packages again.
RUN conda clean --all --yes
# Conda docs say that it is not safe to delete pkgs
# because there may be symbolic links, so we verify
# first that there are no such links.
RUN find -L /opt/conda/envs/ -type l | grep "/opt/conda/pkgs" || exit 0

# The conda install is not usable after this RUN command. Since
# we only need /opt/conda/envs/ anyway, this shouldn't be an issue.
RUN conda clean --all --yes && \
    ls -d /opt/conda/* | grep -v envs | xargs rm -rf && \
    find /opt/conda/ -name "*.exe" | xargs rm -rf && \
    find /opt/conda/ -name "__pycache__" | xargs rm -rf && \
    rm -rf /opt/conda/pkgs/


FROM base_image

COPY --from=builder /opt/conda/ /opt/conda/
COPY --from=builder /vendor/ /vendor
