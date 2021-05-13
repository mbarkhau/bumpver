# Stages:
#   root       : Common image, both for the builder and for the final image.
#                This contains only minimal dependencies required in both cases
#                for miniconda and the Makefile.
#   env_builder: stage in which the conda envrionment is created
#                and dependencies are installed
#   base       : the final image containing only the required environment files,
#                and none of the infrastructure required to generate them.

FROM registry.gitlab.com/mbarkhau/bootstrapit/env_builder AS builder

RUN mkdir /root/.ssh/ && \
    ssh-keyscan gitlab.com >> /root/.ssh/known_hosts && \
    ssh-keyscan registry.gitlab.com >> /root/.ssh/known_hosts

ADD requirements/ requirements/
ADD scripts/ scripts/

ADD Makefile.bootstrapit.make Makefile.bootstrapit.make
ADD Makefile Makefile

# install envs (relatively stable)
ADD requirements/conda.txt requirements/conda.txt
RUN make build/envs.txt

# install python package dependencies (change more often)
ADD requirements/ requirements/
RUN make conda

# Deleting pkgs implies that `conda install`
# will have to pull all packages again.
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

RUN apt-get install --yes mercurial;

COPY --from=builder /opt/conda/ /opt/conda/
COPY --from=builder /vendor/ /vendor
