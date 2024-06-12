from flask import Flask, request, jsonify
import numpy as np
import torch
import onnxruntime
from transformers import AutoTokenizer
from onnxruntime import InferenceSession, SessionOptions
import argparse

app = Flask(__name__)

def create_onnx_session(
        model_path: str,
        provider: str = "CPUExecutionProvider",
        num_threads: int = 2
        ) -> InferenceSession:
    """Создание сессии для инференса модели с помощью ONNX Runtime.

    @param model_path: путь к модели в формате ONNX
    @param provider: инференс на ЦП
    @return: ONNX Runtime-сессия
    """    
    options = SessionOptions()
    options.graph_optimization_level = \
        onnxruntime.GraphOptimizationLevel.ORT_ENABLE_ALL
    options.intra_op_num_threads = num_threads
    session = InferenceSession(model_path, options, providers=[provider])
    session.disable_fallback()
    return session

def onnx_inference(
        text: list,
        session: InferenceSession,
        tokenizer: AutoTokenizer,
        max_length: int) -> np.ndarray:
    
    """Инференс модели с помощью ONNX Runtime.

    @param session: ONNX Runtime-сессия
    @param tokenizer: токенизатор
    @param max_length: максимальная длина последовательности в токенах
    @return: логиты на выходе из модели
    """
    inputs = tokenizer(
        text, padding="max_length", truncation=True, max_length=max_length, return_tensors="np")
    input_feed = {
        "input_ids": inputs["input_ids"].astype(np.int64)
    }
    outputs = session.run(output_names=["output"], input_feed=input_feed)[0]
    outputs = torch.argmax(torch.Tensor(outputs), dim=2)

    results = []

    id_to_label  = {0:'O', 1:'B-discount', 2:'B-value', 3:'I-value'}

    for i, text in enumerate(text):
        token_predictions = outputs[i].tolist()
        word_ids = inputs.word_ids(batch_index=i)
        # Собираем предсказания для слов
        final_predictions = []
        previous_word_idx = None
        for word_idx, pred in zip(word_ids, token_predictions):
            if word_idx is None:
                continue
            elif word_idx != previous_word_idx:
                final_predictions.append(id_to_label[pred])
                previous_word_idx = word_idx
        
        results.append(final_predictions)
    return results

@app.route('/predict', methods = ['POST'])
def predict():
    data = request.get_json()
    text = data.get('text', [])
    outputs = onnx_inference(text, session, tokenizer, 512)
    if outputs: 
        print('OK')
    else:
        print('Error')
    return jsonify({'response': outputs})

@app.route('/', methods=['GET'])
def check_state():
    return 'OK'

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Flask app')

    parser.add_argument('--port', type=int, default=5000, help='Port to run the Flask app on')
    parser.add_argument('--num_threads', type=int, default=1, help='Port to run the Flask app on')
    args = parser.parse_args()

    session = create_onnx_session('ruElectra-small-onnx-quantized.onnx', args.num_threads)
    model_name = 'ai-forever/ruElectra-small'
    tokenizer = AutoTokenizer.from_pretrained(model_name)

    app.run(port=args.port)
