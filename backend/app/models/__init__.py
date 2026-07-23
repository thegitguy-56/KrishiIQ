from app.models.user import User
from app.models.farmer import Farmer
from app.models.farm import Farm
from app.models.crop import CropRecord
from app.models.sensor_reading import SensorReading
from app.models.disease_detection import DiseaseDetection
from app.models.advisory import Advisory

__all__ = [
    "User", "Farmer", "Farm", "CropRecord",
    "SensorReading", "DiseaseDetection", "Advisory",
]
