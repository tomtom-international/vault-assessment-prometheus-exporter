FROM python:3.9-slim as builder

COPY . /build

WORKDIR /build

RUN pip install --upgrade pip && pip install poetry
# Build the wheel rather than directly installing via pip to avoid installing poetry into the prod image
RUN python -m venv /venv
RUN poetry export --format requirements.txt | /venv/bin/pip install -r /dev/stdin
RUN poetry build --format wheel
RUN /venv/bin/pip install dist/*.whl

FROM python:3.9-slim

RUN addgroup exporter && adduser --system --no-create-home --shell /bin/false --ingroup exporter exporter
USER exporter

ENV CONFIG_FILE="/config.yaml"

COPY --from=builder --chown=exporter:exporter /venv /venv

EXPOSE 9935/tcp

ENTRYPOINT ./venv/bin/start_exporter --config_file=$CONFIG_FILE