# Enable BuildKit (for parallel execution)
# syntax=docker/dockerfile:1.4

# ---- Build frontend stage ----
FROM node:20 AS frontend
WORKDIR /client
COPY client/package.json /client/package.json
RUN npm install

COPY client/assets /client/assets
COPY client/build /client/build
COPY client/src /client/src
COPY client/static /client/static
# RUN npm rebuild node-sass
RUN npm run prod

# ---- Set up virtual environment ----
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS venv
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --extra frontend

# ---- Final container ----
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS final

# System setup
ENV TZ=UTC
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
RUN export DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends locales nginx redis-server supervisor
RUN echo "en_US.UTF-8 UTF-8" > /etc/locale.gen
RUN locale-gen

# Install nutrition
WORKDIR /app
COPY --from=venv /app/.venv /app/.venv
COPY nutrition /app/nutrition
COPY nutrition_app /app/nutrition_app
COPY pyproject.toml /app/pyproject.toml
COPY client/flask_app.py /app/flask_app.py
COPY client/gunicorn_config.py /app/gunicorn_config.py
COPY README.md /app/README.md
COPY CHANGELOG.md /app/CHANGELOG.md
RUN uv pip install .

# Copy over frontend content
COPY client/nginx.conf /etc/nginx/sites-enabled/default
EXPOSE 80
COPY --from=frontend /client/dist /client/dist

# Finalize supervisor setup
COPY client/supervisord.conf /etc/supervisor/conf.d/supervisord.conf
CMD ["/usr/bin/supervisord", "-n", "-c", "/etc/supervisor/supervisord.conf"]
