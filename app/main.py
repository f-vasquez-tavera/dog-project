import cv2
import numpy as np
import matplotlib.pyplot as plt
from extract_bottleneck_features import *
from keras.preprocessing import image
from keras.layers import GlobalAveragePooling2D, Dense
from keras.models import Sequential, load_model
from tensorflow.keras.applications.resnet50 import preprocess_input, ResNet50                  
from tqdm import tqdm
from dog_names import dog_names

import os
from app import app
import urllib.request
from flask import Flask, flash, request, redirect, url_for, render_template
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    # Determines if files uploaded to the app are the correct formats
	return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def path_to_tensor(img_path):
    # loads RGB image as PIL.Image.Image type
    img = image.load_img(img_path, target_size=(224, 224))
    # convert PIL.Image.Image type to 3D tensor with shape (224, 224, 3)
    x = image.img_to_array(img)
    # convert 3D tensor to 4D tensor with shape (1, 224, 224, 3) and return 4D tensor
    return np.expand_dims(x, axis=0)

face_cascade = cv2.CascadeClassifier('../haarcascades/haarcascade_frontalface_alt.xml')
def face_detector(img_path):
    # Processes an image and detects if it is a face based on haar_cascade classification
    img = cv2.imread(img_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray)
    return len(faces) > 0

ResNet50_model = ResNet50(weights='imagenet')
def ResNet50_predict_labels(img_path):
    # returns prediction vector for image located at img_path
    img = preprocess_input(path_to_tensor(img_path))
    return np.argmax(ResNet50_model.predict(img))

def dog_detector(img_path):
    # Uses ResNet50 to guess if there's a dog or not in an image
    prediction = ResNet50_predict_labels(img_path)
    return ((prediction <= 268) & (prediction >= 151)) 

Xception_model = load_model('../saved_models/weights.best.Xception.hdf5')


def Xception_predict_breed(img_path):
    # Takes an image and returns the predicted breed
    # extract bottleneck features
    bottleneck_feature = extract_Xception(path_to_tensor(img_path))
    # obtain predicted vector
    predicted_vector = Xception_model.predict(bottleneck_feature)
    # return dog breed that is predicted by the model
    return dog_names[np.argmax(predicted_vector)]

def app_messages(img_path, breed):
    if dog_detector(img_path):
        return f"What a cute dog! Is that a {breed}?\nI'm 85% certain!"
    elif face_detector(img_path):
        return f"That's not a dog, that's a person...\nand they look like a {breed}!"
    else:
        return f"I don't think that's a dog, but if I had to guess...\nyou look like a {breed}!"

@app.route('/')
def upload_form():
    return render_template('upload.html')

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
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        print('upload_image filename: ' + app.config['UPLOAD_FOLDER'] + filename)
        breed = Xception_predict_breed(app.config['UPLOAD_FOLDER'] + filename)
        printout = app_messages(app.config['UPLOAD_FOLDER'] + filename, breed)
        flash(printout)
        return render_template('upload.html', filename=filename)
    else:
        flash('Allowed image types are -> png, jpg, jpeg')
        return redirect(request.url)

@app.route('/display/<filename>')
def display_image(filename):
	#print('display_image filename: ' + filename)
	return redirect(url_for('static', filename='uploads/' + filename), code=301)

def main():
    app.run(host='0.0.0.0', port=3001, debug=True)


if __name__ == '__main__':
    main()