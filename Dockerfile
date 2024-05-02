FROM python:3.12-alpine
WORKDIR /src
ADD requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY src .
CMD ["python", "-u", "main.py"]