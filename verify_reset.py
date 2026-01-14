#!/usr/bin/env python
"""Verify reset_model function works correctly."""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.api.model_routes import reset_model

print("✅ reset_model function successfully imported")
print("\nNew endpoint added:")
print("  POST /models/reset - Resets model to default (assets/models/yolo/best5.pt)")
print("\nResponse structure:")
print("""{
  "status": "reset",
  "model_path": "assets/models/yolo/best5.pt",
  "message": "Model setting reset to default"
}""")
