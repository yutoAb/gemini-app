from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
import os
from werkzeug.utils import secure_filename
from google.cloud import speech
import io
import os
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
CORS(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///my_database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = './temp_audio'

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)

class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return f'<Item {self.name}>'
    
    def to_dict(self):
        return {"id": self.id, "name": self.name}

@app.route('/')
def hello():
    return "Hello from Flask!"

@app.route('/items', methods=['GET'])
def get_items():
    items = Item.query.all()
    return jsonify([item.to_dict() for item in items])

@app.route('/items/<int:item_id>', methods=['DELETE'])
def delete_item(item_id):
    item = Item.query.get(item_id)
    if item:
        db.session.delete(item)
        db.session.commit()
        return jsonify({"message": "Deleted"}), 200
    return jsonify({"message": "Item not found"}), 404

@app.route('/items', methods=['POST'])
def add_item():
    name = request.json['name']
    item = Item(name=name)
    db.session.add(item)
    db.session.commit()
    return jsonify(str(item)), 201

@app.route('/upload-audio', methods=['POST'])
def upload_audio():
    if 'file' not in request.files:
        return "No file part", 400

    file = request.files['file']
    if file.filename == '':
        return "No selected file", 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    # Google Speech-to-Text に送る処理
    client = speech.SpeechClient()

    with io.open(filepath, "rb") as audio_file:
        content = audio_file.read()

    audio = speech.RecognitionAudio(content=content)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.WEBM_OPUS,  # webm形式なら
        sample_rate_hertz=48000,
        language_code="ja-JP",
    )

    try:
        response = client.recognize(config=config, audio=audio)
        results = [result.alternatives[0].transcript for result in response.results]
        transcript = results[0] if results else "音声が認識されませんでした"

        # ✅ DB に保存
        item = Item(name=transcript)
        db.session.add(item)
        db.session.commit()

        # ✅ JSON形式で返す（フロントがすぐにUIに追加できる）
        return jsonify(str(item)), 201

    except Exception as e:
        return f"音声認識エラー: {str(e)}", 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)