import os
from flask import Flask, flash, render_template, request, jsonify, redirect, url_for
from keras.models import load_model
from PIL import Image
from io import BytesIO
import base64
import numpy as np
from utils.DHC_OCR import DHC_OCR
import os
from werkzeug.utils import secure_filename
import base64


app = Flask(__name__)
model = load_model("25epochs.h5")

# Your existing class_indices dictionary
class_indices = {
    0: 'क', 1: 'ख', 2: 'ग', 3: 'घ', 4: 'ङ', 5: 'च', 6: 'छ', 7: 'ज', 8: 'झ', 9: 'ञ',
    10: 'ट', 11: 'ठ', 12: 'ड', 13: 'ढ', 14: 'ण', 15: 'त', 16: 'थ', 17: 'द', 18: 'ध',
    19: 'न', 20: 'प', 21: 'फ', 22: 'ब', 23: 'भ', 24: 'म', 25: 'य', 26: 'र', 27: 'ल',
    28: 'व', 29: 'श', 30: 'ष', 31: 'स', 32: 'ह', 33: 'क्ष', 34: 'त्र', 35: 'ज्ञ',
    36: '०', 37: '१', 38: '२', 39: '३', 40: '४', 41: '५', 42: '६', 43: '७', 44: '८', 45: '९'
}
app = Flask(__name__)

UPLOAD_FOLDER = 'app/static/uploads/'

app.secret_key = "ocr"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
 
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/predict')
def predict_page():
    return render_template('predict.html')

# Route for upload page
@app.route('/upload')
def upload_page():
    return render_template('upload.html')

@app.route('/word')
def word_page():
    return render_template('word.html')

@app.route('/predict', methods=['POST'])
def predict_character():
    # Get the image data from the canvas
    img_data = request.form['img_data'].split(",")[1]
    img = Image.open(BytesIO(base64.b64decode(img_data)))

    # Resize to your model's input size
    img = img.resize((32, 32))

    # Convert to grayscale and normalize
    img_array = np.array(img.convert("L")) / 255.0

    # Make prediction
    input_image = np.expand_dims(np.expand_dims(img_array, axis=0), axis=3)
    predicted_probs = model.predict(input_image)
    predicted_label_index = np.argmax(predicted_probs)

    # Get the predicted label name from the class_indices dictionary
    predicted_label_name = class_indices.get(predicted_label_index, "Unknown Class")

    # Get the probability of the predicted class
    probability = float(predicted_probs[0][predicted_label_index])

    return jsonify({'prediction': predicted_label_name, 'probability': probability})

@app.route('/', methods=['POST'])
def upload_image():
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        flash('No image selected for uploading')
        return redirect(request.url)
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        flash('Image successfully uploaded and displayed below')

        print("xyz file path = ", filepath)
        docr = DHC_OCR()
        devanagari_label, success = docr.predict_image(img=filepath)
        # devanagari_label, success = docr.predict_webcam()

        output_txt = "This image most likely belongs to {} with a {:.2f} percent confidence.".format(devanagari_label, success)
        print("yashuv app.py -->  {}".format(output_txt))
        docr.segment_prediction

        return render_template('upload.html', filename=filename, prediction=output_txt)
    else:
        flash('Allowed Image types are - png, jpg, jpeg')
        return redirect(request.url)
    
@app.route('/display/<filename>')
def display_image(filename):
    #print('display_image filename: ' + filename)
    return redirect(url_for('static', filename='uploads/' + filename), code=301)

# Redirect from '/' to the home page
@app.route('/home')
def redirect_to_home():
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True)