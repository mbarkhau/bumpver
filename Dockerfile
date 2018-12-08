FROM registry.gitlab.com/mbarkhau/pycalver/base

ADD src/ src/
ADD stubs/ stubs/
ADD test/ test/
ADD setup.cfg setup.cfg
ADD makefile makefile
ADD makefile.config.make makefile.config.make
ADD makefile.extra.make makefile.extra.make

ENV PYTHONPATH="src/:vendor/"

CMD make serve
