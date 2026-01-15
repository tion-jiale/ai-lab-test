# app.py
import streamlit as st
import torch
import torchvision.transforms as transforms
from torchvision import models
from PIL import Image
import requests
from io import BytesIO
import pandas as pd

# ----------------------------
# Step 1: Streamlit page setup
# ----------------------------
st.set_page_config(page_title="Real-Time Webcam Classifier", layout="wide")
st.title("Real-Time Webcam Image Classification (Person Stuff)")

# ----------------------------
# Step 2: Download ImageNet class labels
# ----------------------------
LABELS_URL = "https://raw.githubusercontent.com/pytorch/hub/master/imagenet_classes.txt"
response = requests.get(LABELS_URL)
imagenet_classes = [s.strip() for s in response.text.splitlines()]

# ----------------------------
# Step 3: Load pretrained ResNet-18
# ----------------------------
st.info("Loading pretrained ResNet-18 model...")
model = models.resnet18(weights=models.ResNet18_Weights.DEFAULT)
model.eval()  # Set to evaluation mode

# ----------------------------
# Step 4: Define preprocessing pipeline
# ----------------------------
preprocess = transforms.Compose([
    transforms.Resize(256),            # Resize shorter side to 256
    transforms.CenterCrop(224),        # Center crop 224x224
    transforms.ToTensor(),             # Convert to tensor
    transforms.Normalize(              # Normalize with ImageNet mean/std
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )
])

# ----------------------------
# Step 5: Capture/upload image
# ----------------------------
st.subheader("Upload or Capture an Image")
uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])

if uploaded_file:
    image = Image.open(uploaded_file).convert("RGB")
    st.image(image, caption="Uploaded Image", use_column_width=True)

    # Preprocess image
    input_tensor = preprocess(image)
    input_batch = input_tensor.unsqueeze(0)  # Create batch dimension

    # ----------------------------
    # Step 6: Run model prediction
    # ----------------------------
    with torch.no_grad():
        outputs = model(input_batch)
        probabilities = torch.nn.functional.softmax(outputs[0], dim=0)

    # Get Top 5 predictions
    top5_prob, top5_catid = torch.topk(probabilities, 5)
    results = []
    for i in range(top5_prob.size(0)):
        results.append({
            "Label": imagenet_classes[top5_catid[i]],
            "Probability": float(top5_prob[i])
        })

    # Display results in a table
    st.subheader("Top 5 Predictions")
    df_results = pd.DataFrame(results)
    st.table(df_results)

else:
    st.info("Upload an image to see predictions.")
