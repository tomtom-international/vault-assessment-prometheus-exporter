FROM python:3.10.4-alpine3.15 as builder

COPY . /build

WORKDIR /build

RUN python -m venv /venv && /venv/bin/pip --no-cache-dir install .

FROM python:3.10.4-alpine3.15

RUN addgroup exporter && adduser --system --no-create-home --shell /bin/false --ingroup exporter exporter
USER exporter

ENV CONFIG_FILE="/config.yaml"

COPY --from=builder --chown=exporter:exporter /venv /venv

EXPOSE 9935/tcp

ENTRYPOINT ["/bin/sh", "-c", "./venv/bin/start_exporter --config_file=$CONFIG_FILE"]
