# TODO: Freeze version and automate versions update
FROM python:3.9-slim AS builder

USER root

# Make sure we don't get notifications we can't answer during building.
ENV DEBIAN_FRONTEND noninteractive

#
# Default config
#
COPY tools/tooling/container/builder /opt/container
RUN groupadd -g "9999" "user" \
    && useradd --create-home --gid "user" --shell "/bin/bash" --system --uid "9999" "user" \
    && rm "/home/user/.profile" \
    && apt-get update \
    && for PACKAGE in `cat "/opt/container/packages.txt"`; do {\
    apt-get install -y "${PACKAGE}" \
    || { echo "Cannot install $PACKAGE"; exit 1; }; \
    }; done \
    && apt-get clean \
    && rm -rf "/opt/container" \
    && curl --fail --location --output "/opt/pypy.tar.bz2" "https://downloads.python.org/pypy/pypy3.9-v7.3.11-linux64.tar.bz2" \
    && tar -C "/opt" -xf "/opt/pypy.tar.bz2" \
    && mv "/opt/pypy3"* "/opt/pypy" \
    && find "/opt/pypy/bin/" -exec chmod +x {} + \
    && ln -s "/opt/pypy/bin/pypy" "/opt/pypy/bin/pypy3" "/usr/local/bin" \
    && mkdir "/opt/app" \
    && chown user:user "/opt/app"
USER user



################################################################################
FROM builder AS release

ENV PATH="/home/user/.local/bin:/usr/local/bin:/usr/bin:/bin"
WORKDIR /opt/app

# Split poetry setup from application data to speed up builds
COPY --chown=user:user Makefile poetry.lock poetry.toml pyproject.toml /opt/app/
RUN mkdir myapp \
    && touch myapp/__init__.py \
    && sed -i -e 's:from = "src":from = ".":' pyproject.toml \
    && make app \
    && rm -rf myapp

COPY --chown=user:user src/ /opt/app/

ENV PATH="/home/user/.local/bin:/usr/local/bin:/usr/bin:/bin"
CMD ["bin/run.sh"]



################################################################################
FROM builder AS dev

USER root
COPY tools/tooling/container/dev /opt/container
ENV PATH="/root/.local/bin:/usr/local/bin:/usr/bin:/bin"
ENV PYTHONPATH="/workspace/src:/workspace/.venv/lib/python3.9/site-packages"
RUN apt-get update \
    && for PACKAGE in `cat /opt/container/packages.txt`; do {\
    apt-get install -y "${PACKAGE}" \
    || { echo "Cannot install $PACKAGE"; exit 1; }; \
    }; done \
    && apt-get clean \
    && rm -rf /opt/container
