FROM python:3.11

RUN apt-get -y update && apt-get -y upgrade && apt-get install -y ffmpeg

# Python dependencies
RUN python -m pip install pipenv==2021.11.9
COPY Pipfile Pipfile.lock ./
RUN python -m pipenv install --system

WORKDIR /app
COPY src /app
CMD [ "python", "run_lemon_bot.py" ]
