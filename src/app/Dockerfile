FROM python:3.10

RUN python3 -m pip install flask flask-cors gunicorn torch numpy==1.26 onnxruntime transformers gdown

WORKDIR /app

ADD model_api.py model_api.py

EXPOSE 5000

CMD [ "gunicorn", "--bind", "0.0.0.0:5000", "model_api:app" ]