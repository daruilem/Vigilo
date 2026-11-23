FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app
COPY pyproject.toml README.md LICENSE ./
COPY src ./src
RUN pip install .

RUN useradd --create-home --uid 10001 vigilo
USER vigilo

EXPOSE 8000
# No Server header, and X-Forwarded-For is handled by Vigilo itself
# (see VIGILO_TRUSTED_PROXIES), not by uvicorn.
CMD ["uvicorn", "vigilo.api:app", "--host", "0.0.0.0", "--port", "8000", "--no-server-header", "--no-proxy-headers"]
