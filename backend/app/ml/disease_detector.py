import io
import os
from typing import Dict

try:
    import torch
    import torchvision.transforms as transforms
    import timm
    from PIL import Image, ImageStat
    _TORCH_AVAILABLE = True
except ImportError:
    _TORCH_AVAILABLE = False


# Trained on 11 of the originally scoped 16 classes. The remaining 5
# (Neck_Blast, Sheath_Blight, False_Smut, Downy_Mildew, Anthracnose) were
# excluded due to lack of sufficient labeled public training data.
# Order matches the alphabetical class order PyTorch's ImageFolder assigned
# during training (train_ds.classes) — this order is load-bearing, do not
# reorder without retraining or predictions will be mislabeled.
DISEASE_CLASSES = [
    "Bacterial_Blight",
    "Brown_Spot",
    "Early_Blight",
    "Healthy",
    "Late_Blight",
    "Leaf_Blast",
    "Leaf_Curl",
    "Mosaic_Virus",
    "Powdery_Mildew",
    "Rust",
    "Tungro",
]


DISEASE_TREATMENTS = {
    "Healthy": {
        "en": "No treatment needed. Crop appears healthy.",
        "hi": "कोई उपचार आवश्यक नहीं। फसल स्वस्थ लग रही है।",
        "ta": "சிகிச்சை தேவையில்லை. பயிர் ஆரோக்கியமாக உள்ளது.",
    },
    "Bacterial_Blight": {
        "en": "Apply copper-based bactericide. Remove infected leaves. Avoid overhead irrigation.",
        "hi": "तांबा आधारित बैक्टीरिसाइड लगाएं। संक्रमित पत्तियां हटाएं।",
        "ta": "தாமிர அடிப்படையிலான பாக்டீரிசைட் பயன்படுத்தவும்.",
    },
    "Brown_Spot": {
        "en": "Apply Mancozeb or Tricyclazole fungicide. Improve potassium nutrition.",
        "hi": "मैन्कोजेब या ट्राईसाइक्लाजोल फफूंदनाशक लगाएं।",
        "ta": "மான்கோஜெப் அல்லது ட்ரைசைக்லஜோல் பூஞ்சைக்கொல்லி பயன்படுத்தவும்.",
    },
    "Leaf_Blast": {
        "en": "Apply Tricyclazole or Isoprothiolane. Avoid excess nitrogen fertilizer.",
        "hi": "ट्राईसाइक्लाजोल लगाएं। अधिक नाइट्रोजन खाद से बचें।",
        "ta": "ட்ரைசைக்லஜோல் பயன்படுத்தவும். அதிக நைட்ரஜன் உரத்தை தவிர்க்கவும்.",
    },
    "Rust": {
        "en": "Apply Propiconazole or Mancozeb fungicide. Remove severely infected leaves.",
        "hi": "प्रोपिकोनाजोल या मैन्कोजेब फफूंदनाशक लगाएं।",
        "ta": "ப்ரோபிகோனசோல் அல்லது மான்கோஜெப் பயன்படுத்தவும்.",
    },
    "Early_Blight": {
        "en": "Apply Mancozeb or Chlorothalonil. Remove infected plant debris.",
        "hi": "मैन्कोजेब या क्लोरोथालोनिल लगाएं।",
        "ta": "மான்கோஜெப் அல்லது குளோரோத்தாலோனில் பயன்படுத்தவும்.",
    },
    "Late_Blight": {
        "en": "Apply Metalaxyl + Mancozeb. Avoid wet leaf conditions.",
        "hi": "मेटालैक्सिल + मैन्कोजेब लगाएं।",
        "ta": "மெட்டாலாக்சில் + மான்கோஜெப் பயன்படுத்தவும்.",
    },
    "Tungro": {
        "en": "No direct cure. Remove and destroy infected plants. Control leafhopper vectors with recommended insecticide. Use resistant varieties next season.",
        "hi": "कोई सीधा इलाज नहीं है। संक्रमित पौधों को हटाकर नष्ट करें। कीटनाशक से लीफहॉपर को नियंत्रित करें।",
        "ta": "நேரடி சிகிச்சை இல்லை. பாதிக்கப்பட்ட செடிகளை அகற்றி அழிக்கவும். பூச்சிக்கொல்லி மூலம் இலைத்தாவி கட்டுப்படுத்தவும்.",
    },
    "Powdery_Mildew": {
        "en": "Apply sulfur-based or Propiconazole fungicide. Improve air circulation between plants.",
        "hi": "सल्फर आधारित या प्रोपिकोनाजोल फफूंदनाशक लगाएं। पौधों के बीच हवा का संचार बढ़ाएं।",
        "ta": "சல்பர் அல்லது ப்ரோபிகோனசோல் பூஞ்சைக்கொல்லி பயன்படுத்தவும். செடிகளுக்கு இடையே காற்றோட்டத்தை மேம்படுத்தவும்.",
    },
    "Leaf_Curl": {
        "en": "No direct cure for viral infection. Remove and destroy infected plants. Control whitefly vectors with recommended insecticide.",
        "hi": "वायरल संक्रमण का कोई सीधा इलाज नहीं। संक्रमित पौधों को हटाकर नष्ट करें। सफेद मक्खी को नियंत्रित करें।",
        "ta": "வைரஸ் தொற்றுக்கு நேரடி சிகிச்சை இல்லை. பாதிக்கப்பட்ட செடிகளை அகற்றி அழிக்கவும். வெள்ளை ஈயை கட்டுப்படுத்தவும்.",
    },
    "Mosaic_Virus": {
        "en": "No direct cure for viral infection. Remove and destroy infected plants. Control aphid vectors and disinfect tools between plants.",
        "hi": "वायरल संक्रमण का कोई सीधा इलाज नहीं। संक्रमित पौधों को हटाकर नष्ट करें। एफिड को नियंत्रित करें।",
        "ta": "வைரஸ் தொற்றுக்கு நேரடி சிகிச்சை இல்லை. பாதிக்கப்பட்ட செடிகளை அகற்றி அழிக்கவும். இலை பேன் கட்டுப்படுத்தவும்.",
    },
}


PEST_ANOMALY_DISEASES = {"Mosaic_Virus", "Tungro", "Leaf_Curl"}


class DiseaseDetector:
    def __init__(self, model_path: str):
        self.model = None
        self.device = None
        self.transform = None

        if not _TORCH_AVAILABLE:
            print("Torch/timm/PIL not available. Using demo detector.")
            return

        if not model_path or not os.path.exists(model_path):
            print(f"Trained disease model not found: {model_path}. Using demo detector.")
            return

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = self._load_model(model_path)

        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225],
            ),
        ])

    def _load_model(self, model_path: str):
        model = timm.create_model(
            "efficientnet_b4",
            pretrained=False,
            num_classes=len(DISEASE_CLASSES),
        )

        state = torch.load(model_path, map_location=self.device)

        if isinstance(state, dict) and "state_dict" in state:
            state = state["state_dict"]

        if isinstance(state, dict) and "model_state_dict" in state:
            state = state["model_state_dict"]

        clean_state = {}
        for key, value in state.items():
            clean_key = key.replace("module.", "")
            clean_state[clean_key] = value

        model.load_state_dict(clean_state, strict=False)
        model.to(self.device)
        model.eval()

        print("Disease model loaded successfully:", model_path)
        return model

    def predict(self, image_bytes: bytes) -> Dict:
        if self.model is None or self.transform is None:
            return _demo_prediction(image_bytes)

        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        tensor = self.transform(image).unsqueeze(0).to(self.device)

        with torch.no_grad():
            logits = self.model(tensor)
            probs = torch.softmax(logits, dim=1)[0]

        top_prob, top_idx = probs.topk(5)

        top_predictions = {
            DISEASE_CLASSES[idx.item()]: round(prob.item(), 4)
            for prob, idx in zip(top_prob, top_idx)
        }

        disease = DISEASE_CLASSES[top_idx[0].item()]
        confidence = float(top_prob[0].item())

        severity = _get_severity(confidence)

        treatments = DISEASE_TREATMENTS.get(
            disease,
            {
                "en": f"{disease} detected. Consult an agriculture expert and apply recommended treatment.",
                "hi": f"{disease} पाया गया। कृषि विशेषज्ञ से सलाह लें।",
                "ta": f"{disease} கண்டறியப்பட்டது. விவசாய நிபுணரை அணுகவும்.",
            },
        )

        return {
            "disease_name": disease,
            "confidence": round(confidence, 4),
            "severity": severity,
            "affected_area_percent": round(confidence * 100, 1),
            "treatment_en": treatments["en"],
            "treatment_hi": treatments["hi"],
            "treatment_ta": treatments["ta"],
            "is_pest_anomaly": disease in PEST_ANOMALY_DISEASES,
            "top_predictions": top_predictions,
        }


def _get_severity(confidence: float) -> str:
    if confidence >= 0.95:
        return "critical"
    if confidence >= 0.88:
        return "high"
    if confidence >= 0.75:
        return "medium"
    return "low"


def _demo_prediction(image_bytes: bytes) -> Dict:
    """
    Demo fallback only.
    This is not real trained AI detection.
    Used when efficientnet_disease.pt is missing.
    """
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB").resize((224, 224))
    stat = ImageStat.Stat(image)

    r, g, b = stat.mean
    brightness = (r + g + b) / 3

    # Simple demo rules for testing UI/backend flow
    if g > r + 15 and g > b + 15 and brightness > 90:
        disease = "Healthy"
        confidence = 0.82
    elif r > g + 10 or brightness < 70:
        disease = "Brown_Spot"
        confidence = 0.89
    elif b > g:
        disease = "Bacterial_Blight"
        confidence = 0.84
    else:
        disease = "Leaf_Blast"
        confidence = 0.86

    treatments = DISEASE_TREATMENTS.get(disease, DISEASE_TREATMENTS["Healthy"])

    top_predictions = {
        disease: confidence,
        "Healthy": round(max(0.01, 1 - confidence), 4),
    }

    return {
        "disease_name": disease,
        "confidence": round(confidence, 4),
        "severity": _get_severity(confidence),
        "affected_area_percent": round(confidence * 100, 1),
        "treatment_en": treatments["en"],
        "treatment_hi": treatments["hi"],
        "treatment_ta": treatments["ta"],
        "is_pest_anomaly": disease in PEST_ANOMALY_DISEASES,
        "top_predictions": top_predictions,
    }


_detector_instance = None


def get_detector(model_path: str) -> DiseaseDetector:
    global _detector_instance
    if _detector_instance is None:
        _detector_instance = DiseaseDetector(model_path)
    return _detector_instance