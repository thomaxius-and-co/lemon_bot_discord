FROM python:3.9.1


# Python dependencies
RUN python -m pip install pipenv==2021.11.9
COPY Pipfile Pipfile.lock ./
RUN python -m pipenv install --system

WORKDIR /app
COPY src /app
CMD [ "python", "run_lemon_bot.py" ]
