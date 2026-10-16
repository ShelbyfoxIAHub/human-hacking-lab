FROM python:3.12-alpine
WORKDIR /app
COPY apps/appsec/appsec.py .
COPY apps/appsec/modules.json .
EXPOSE 8097
CMD ["python", "appsec.py"]