FROM python:3.12
LABEL authors="User"
COPY . ./app
WORKDIR ./app
RUN pip install -r requirements.txt
CMD ["python", "bot.py"]