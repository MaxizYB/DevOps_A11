ARG BASE_IMAGE=m.daocloud.io/docker.io/library/python@sha256:f82c96458eedc847b233e582eb31336f4954b39cae020b6dcf5b3ed0e5cbcd74
FROM ${BASE_IMAGE}

ENV LC_ALL=C.UTF-8 \
    TZ=UTC \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc make libc6-dev strace git \
    && dpkg-query -W -f='${Package}=${Version}\n' gcc make libc6-dev strace git > /opt/toolchain.lock \
    && echo "python3=$(python3 -c 'import platform; print(platform.python_version())')" >> /opt/toolchain.lock \
    && echo "arch=$(dpkg --print-architecture)" >> /opt/toolchain.lock \
    && rm -rf /var/lib/apt/lists/*

COPY requirements-dev.lock /tmp/requirements-dev.lock
RUN pip install --no-cache-dir --require-hashes -r /tmp/requirements-dev.lock \
    && pip freeze | sed 's/^/pip:/' >> /opt/toolchain.lock

RUN useradd --uid 10001 --create-home app \
    && install -d -o app -g app /app /app/work
WORKDIR /app
COPY --chown=app:app services/buildchecker/buildchecker/ services/buildchecker/buildchecker/
COPY --chown=app:app services/buildchecker/tests/ services/buildchecker/tests/
COPY --chown=app:app services/buildchecker/pytest.ini services/buildchecker/pytest.ini
COPY --chown=app:app scripts/e4/ scripts/e4/
COPY --chown=app:app pytest.ini /app/pytest.ini
COPY --chown=app:app fixtures/e3/md-rd/ fixtures/md-rd/
ENV PYTHONPATH=/app:/app/services/buildchecker
USER app
CMD ["python", "-m", "buildchecker", "version"]
