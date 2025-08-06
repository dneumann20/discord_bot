FROM python:3.12-slim

WORKDIR /home/ubuntu/discordbot
COPY . /home/ubuntu/discordbot

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python3", "/home/ubuntu/discordbot/Botbaka.py"]