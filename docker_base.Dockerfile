# Stages:
#   root       : Common image, both for the builder and for the final image.
#                This contains only minimal dependencies required in both cases
#                for miniconda and the makefile.
#   env_builder: stage in which the conda envrionment is created
#                and dependencies are installed
#   base       : the final image containing only the required environment files,
#                and none of the infrastructure required to generate them.

FROM registry.gitlab.com/mbarkhau/bootstrapit/env_builder AS builder

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


FROM registry.gitlab.com/mbarkhau/bootstrapit/root

COPY --from=builder /opt/conda/ /opt/conda/
COPY --from=builder /vendor/ /vendor
