FROM python:3.10-buster

WORKDIR /decision

COPY ./decision.py .

COPY ./requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python3", "decision.py"] 