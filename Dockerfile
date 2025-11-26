FROM python:3.12
LABEL authors="User"
COPY . ./app
WORKDIR ./app
CMD ["python", "bot.py"]