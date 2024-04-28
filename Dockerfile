FROM python:3.12-alpine
WORKDIR /src
COPY ./src .
RUN pip install \
    munch \
    premailer \
    requests \
    yagmail
CMD ["python", "-u", "main.py"]