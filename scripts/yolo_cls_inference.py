"""Simple YOLO Classification Model Inference Script."""

import argparse
from pathlib import Path

import cv2
from ultralytics import YOLO


def infer_yolo_cls(model_path: str, image_path: str) -> None:
    """
    Run YOLO classification inference on a single image.

    Args:
        model_path: Path to the YOLO model file (e.g., .pt or .onnx)
        image_path: Path to the image file to infer on
    """
    # Load the model
    print(f"Loading model from: {model_path}")
    model = YOLO(model_path)

    # Read the image
    print(f"Loading image from: {image_path}")
    image = cv2.imread(image_path)
    if image is None:
        msg = f"Could not read image from: {image_path}"
        raise ValueError(msg)

    # Run inference
    print("Running inference...")
    results = model.predict(image_path, conf=0.5)

    # Process results
    for result in results:
        # Get top prediction
        if result.probs is not None:
            probs = result.probs
            # Get the class with highest probability
            class_probs = probs.data
            top_idx = int(class_probs.argmax())
            top_confidence = float(class_probs[top_idx])
            top_class_name = result.names[top_idx]

            print("\n✓ Inference Complete!")
            print(f"  Class: {top_class_name}")
            print(f"  Class ID: {top_idx}")
            print(f"  Confidence: {top_confidence:.2%}")
            print("  All probabilities:")

            for class_id, prob in enumerate(class_probs):
                class_name = result.names[class_id]
                confidence = float(prob)
                print(f"    - {class_name}: {confidence:.2%}")


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Simple YOLO Classification Inference")
    parser.add_argument(
        "--model",
        type=str,
        default="yolo11n-cls.pt",
        help="Path to YOLO model file",
    )
    parser.add_argument(
        "--image",
        type=str,
        required=True,
        help="Path to image file for inference",
    )

    args = parser.parse_args()

    # Verify image exists
    image_path = Path(args.image)
    if not image_path.exists():
        msg = f"Image not found: {image_path}"
        raise FileNotFoundError(msg)

    # Model will be auto-downloaded by YOLO if it doesn't exist locally
    infer_yolo_cls(args.model, str(image_path))


if __name__ == "__main__":
    main()
