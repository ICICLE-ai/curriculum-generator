"""
Week 7 Solution: Example Tuned CNN
"""

import tensorflow as tf
from tensorflow.keras import layers, models
import numpy as np

X = np.load("X.npy")
y = np.load("y.npy")

num_classes = len(np.unique(y))
y = tf.keras.utils.to_categorical(y, num_classes)

model = models.Sequential([

    layers.Conv2D(32, (3,3), activation='relu', input_shape=(128,128,3)),
    layers.MaxPooling2D((2,2)),

    layers.Conv2D(64, (3,3), activation='relu'),
    layers.MaxPooling2D((2,2)),

    layers.Flatten(),

    layers.Dense(128, activation='relu'),
    layers.Dropout(0.5),

    layers.Dense(num_classes, activation='softmax')
])

model.compile(
    optimizer='adam',
    loss='categorical_crossentropy',
    metrics=['accuracy']
)

model.summary()

history = model.fit(
    X,
    y,
    epochs=10,
    batch_size=32
)

model.save("week7_cnn_model_tuned.h5")