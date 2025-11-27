FROM python:3.12
LABEL authors="User"
WORKDIR ./app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt
CMD ["python", "bot.py"]