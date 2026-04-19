"""
Week 7: Introduction to CNNs (Starter)

Goal:
- Build your first CNN
- Train it
- Modify architecture and observe results
"""

import tensorflow as tf
from tensorflow.keras import layers, models
import numpy as np

# =========================
# Load preprocessed data
# (Use your Week 6 saved arrays)
# =========================

X = np.load("X.npy")   # shape: (num_samples, 128, 128, 3)
y = np.load("y.npy")

num_classes = len(np.unique(y))

# Convert labels to categorical
y = tf.keras.utils.to_categorical(y, num_classes)

# =========================
# Build CNN Model
# =========================

model = models.Sequential([

    # Try changing number of filters (16 → 32)
    layers.Conv2D(16, (3,3), activation='relu', input_shape=(128,128,3)),
    layers.MaxPooling2D((2,2)),

    # Try changing kernel size (3,3 → 5,5)
    layers.Conv2D(32, (3,3), activation='relu'),
    layers.MaxPooling2D((2,2)),

    layers.Flatten(),

    # Try changing neurons (64 → 128)
    layers.Dense(64, activation='relu'),

    # Try adding Dropout layer here
    # layers.Dropout(0.5),

    layers.Dense(num_classes, activation='softmax')
])

# =========================
# Compile Model
# =========================

model.compile(
    optimizer='adam',
    loss='categorical_crossentropy',
    metrics=['accuracy']
)

model.summary()

# =========================
# Train Model
# =========================

history = model.fit(
    X,
    y,
    epochs=5,   # Try changing epochs (5 → 10)
    batch_size=32
)

# =========================
# Save model
# =========================
model.save("week7_cnn_model.h5")