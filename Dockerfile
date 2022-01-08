FROM python:3.8
COPY ./app ./app
COPY ./requirements.txt ./requirements.txt
RUN pip install -r ./requirements.txt
ENV HOST="0.0.0.0"
ENV PORT=5000
CMD ["python -m app.main.main"]
ENTRYPOINT uvicorn app.main:app --host ${HOST} --port ${PORT}