FROM python:3

HEALTHCHECK CMD curl -fs http://localhost:8000/health || exit 1
EXPOSE 8000

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD [ "sh", "-c", "./entrypoint.sh" ]
