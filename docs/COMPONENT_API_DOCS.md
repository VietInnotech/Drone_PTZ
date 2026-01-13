# Component API Documentation

## Overview
The API component provides a RESTful and WebSocket interface for managing camera sessions, tracking targets, and system settings.

## Model Management Domain
Responsible for the lifecycle of YOLO detection models.

### Endpoints
- `GET /models`: List all available models in `assets/models/yolo/`.
- `GET /models/{name}`: Get metadata for a specific model.
- `POST /models/upload`: Upload a new model file (.pt or .onnx).
- `DELETE /models/{name}`: Remove a model file.
- `POST /models/{name}/activate`: Set the model as the active detection model.

### Key Classes
- `src.api.model_routes`: Contains route handlers for model management.
- `src.api.settings_manager.SettingsManager`: Used to update `model_path` in `DetectionSettings`.

### Location
- `src/api/model_routes.py`
- `src/api/app.py`
- `tests/integration/test_model_api.py`
