FROM python:3.12-slim

WORKDIR /app
COPY . /app

ENV PYTHONPATH=/app

CMD ["python", "-m", "iboga_experiment.curriculum_v04", "--backend", "fixture", "--conditions", "direct,compute_matched,forced_sitting,full_iboga", "--repeats", "1", "--out", "results/iboga-long-curriculum-v0.4-fixture.json"]
