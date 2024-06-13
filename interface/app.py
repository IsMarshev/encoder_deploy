import os
from flask import Flask, request, render_template, send_from_directory, jsonify
import requests
import pandas as pd
import json

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'

# Ensure the upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/')
def index():
    return render_template('main_page.html')

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['file']
    if file:
        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(file_path)
        id_data = get_id(file_path)
        return render_template('main_page.html', filename=file.filename, id_data=id_data)
    return "No file uploaded", 400

@app.route('/content/<int:id>', methods=['GET'])
def get_content(id):
    file_path = os.path.join(UPLOAD_FOLDER, request.args.get('filename'))
    data = pd.read_csv(file_path)
    text_columns = [i for i in data.columns if 'text' in i.lower()]
    # print(text_columns)
    labels = request_to_api(data.iloc[id - 1][text_columns[0]])
    text = data.iloc[id - 1][text_columns[0]]
    content = marking_text(text, labels)
    return jsonify({'content': content})

def get_id(file_path):
    data = pd.read_csv(file_path)
    return list(range(1, len(data) + 1))

def request_to_api(text):
    headers = {'Content-Type':'application/json'}
    if isinstance(text,str):
        data = {'text':[text]}
    elif isinstance(text, list):
        data = {'text':text}
    url = 'http://localhost:5000/predict'
    response = requests.post(url,data=json.dumps(data),headers=headers)
    return json.loads(response.text)['response']

def marking_text(text,labels):
    text = text.split()
    for label in labels:
        for _ in range(len(label)):
            if label[_] == 'B-discount':
                text[_]= f"<mark style='background-color: #0099ff; padding: 0.2em 0.4em; border-radius: 5px;'>{text[_]}</mark>"
            elif label[_] == 'B-value' or label[_] == 'I-value':
                text[_]= f"<mark style='background-color: #00a416; padding: 0.2em 0.4em; border-radius: 5px;'>{text[_]}</mark>"
    return ' '.join(text)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

if __name__ == '__main__':
    app.run(debug=True, port=8080)
