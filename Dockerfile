FROM python:3.11.1-alpine3.17 as builder

COPY . /build

WORKDIR /build

RUN python -m venv /venv && /venv/bin/pip --no-cache-dir install .

FROM python:3.11.1-alpine3.17

RUN addgroup --gid 1000 exporter && adduser --uid 1000 --system --no-create-home --shell /bin/false --ingroup exporter exporter
USER exporter

ENV CONFIG_FILE="/config.yaml"

COPY --from=builder --chown=exporter:exporter /venv /venv

EXPOSE 9935/tcp

ENTRYPOINT ["/bin/sh", "-c", "./venv/bin/start_exporter --config_file=$CONFIG_FILE"]
