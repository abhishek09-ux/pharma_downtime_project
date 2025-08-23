# train_model.py
# Script to train the enhanced pharmaceutical downtime prediction model

import logging
from app.ml.model import train_model

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

if __name__ == "__main__":
    print("🏭 Pharmaceutical Downtime Prediction Model Training")
    print("=" * 60)
    
    try:
        model, accuracy = train_model()
        print(f"\n✅ Model training completed successfully!")
        print(f"📊 Final Accuracy: {accuracy:.1%}")
        print("🚀 Model is ready for production use.")
        
    except Exception as e:
        print(f"❌ Training failed: {e}")
        import traceback
        traceback.print_exc()
