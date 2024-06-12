FROM python:3.10

RUN python -m pip install flask flask-cors gunicorn torch numpy onnxruntime transformers

WORKDIR /app

ADD model_api.py model_api.py
ADD ruElectra-small-onnx-quantized.onnx ruElectra-small-onnx-quantized.onnx

EXPOSE 5000

CMD [ "gunicorn", "--bind", "0.0.0.0:5000", "model_api:app" ]