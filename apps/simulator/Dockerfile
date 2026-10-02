FROM python:3.12-alpine
WORKDIR /app
COPY apps/simulator/app.py .
COPY apps/simulator/telemetry.py .
COPY apps/simulator/campaigns.json .
COPY scenarios/users.csv .
EXPOSE 8090
CMD ["python", "app.py"]
