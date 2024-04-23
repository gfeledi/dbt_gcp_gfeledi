# Python image to use.
FROM python:3.9
# FROM ghcr.io/dbt-labs/dbt-bigquery:1.5.6

ENV PYTHONUNBUFFERED True
# Set the working directory in the docker image to /dbt_gcp
WORKDIR /dbt_gcp

# copy the requirements file used for dependencies
COPY ./requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --trusted-host pypi.python.org -r requirements.txt

# Copy the rest of the working directory contents into the container at /dbt_gcp
COPY analytics analytics
COPY bin bin

# Download dbt dependencies
RUN dbt deps --profiles-dir analytics --project-dir analytics

EXPOSE 8080
# Run app.py when the container launches
ENTRYPOINT ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "1", "--threads", "8", "--timeout", "300", "bin.main:app"]
# ENTRYPOINT exec python -m gunicorn --bind :8080 --workers 1 --threads 8 --timeout 300 bin.main:app


