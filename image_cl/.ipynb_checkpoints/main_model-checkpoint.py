import tensorflow as tf
import tensorflow_hub as hub
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.preprocessing.image import ImageDataGenerator, array_to_img, img_to_array, load_img
import cv2
import numpy as np
import os
import pandas as pd
from sklearn import model_selection
import shutil

class Preprocessing:
    def __init__(self, x, y, batch_size, train_path, valid_path):
        self.x = x
        self.y = y
        self.batch_size = batch_size
        self.train_path = train_path
        self.valid_path = valid_path
    
    def generator(self):
        train_datagen = ImageDataGenerator(
                                            rescale=1./255,
                                            rotation_range=30,
                                            width_shift_range=0.2,
                                            height_shift_range=0.4,
                                            brightness_range=None,
                                            shear_range=0.2,
                                            zoom_range=0.2,
                                            channel_shift_range=0.4,
                                            fill_mode="nearest",
                                            cval=0.4,
                                            horizontal_flip=True,
                                            vertical_flip=True
                                           )
        test_datagen = ImageDataGenerator(rescale=1./255)
        
        train_generator = train_datagen.flow_from_directory(
                                                            self.train_path,  # this is the target directory
                                                            target_size=(self.x, self.y),  # all images will be resized to 150x150
                                                            batch_size=self.batch_size,
                                                            class_mode='categorical')

        valid_generator = test_datagen.flow_from_directory(
                                                            self.valid_path,
                                                            target_size=(self.x, self.y),
                                                            batch_size=self.batch_size,
                                                            class_mode='categorical')
        
        return train_generator, valid_generator
    
class Model:
    def __init__(self, train_generator, valid_generator, met, los, model_link, x, y):
        self.train_generator = train_generator
        self.valid_generator = valid_generator
        self.met = met
        self.los = los
        self.model_link = model_link
        self.x = x
        self.y = y
    
    def compiler(self, activation, dense1, dropout):
        self.dense = dense1
        self.dropout = dropout
        self.activation = activation
        tl_model = tf.keras.Sequential([
                    hub.KerasLayer(self.model_link, trainable=False),
                    tf.keras.layers.Dropout(self.dropout),
                    tf.keras.layers.Dense(self.dense, activation='relu'),
                    tf.keras.layers.Dense(self.train_generator.num_classes, activation=self.activation)
                ])
        tl_model.build([None, self.x, self.y, 3])
        
        optimizer = tf.keras.optimizers.Adam(lr=1e-3)
        tl_model.compile(optimizer=optimizer, loss=self.los, metrics=self.met)
        
        return tl_model
    
    def train(self, epochs, model):
        self.epochs = epochs
        self.model = model
        steps_per_epoch = np.ceil(self.train_generator.samples/self.train_generator.batch_size)
        val_steps_per_epoch = np.ceil(self.valid_generator.samples/self.valid_generator.batch_size)
        print(self.valid_generator)
        hist = self.model.fit(
                            self.train_generator, 
                            epochs=self.epochs,
                            verbose=1,
                            steps_per_epoch=steps_per_epoch,
                            validation_data=self.valid_generator,
                            validation_steps=val_steps_per_epoch).history

        return self.model, hist

class Predictions:
    
    def __init__(self, image_dir, model, test_df, x, y):
        self.image_dir = image_dir
        self.model = model
        self.test_df = test_df
        self.x = x
        self.y = y
    
    def predict(self, image_name):
        self.image_name = image_name
        test_img = cv2.imread(os.path.join(self.image_dir, self.image_name))
        test_img = np.resize(test_img, (1, self.x, self.y, 3))
        tf_model_predictions = self.model.predict(test_img)
        id_ = np.argmax(tf_model_predictions)
        
        return image_name, id_