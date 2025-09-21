#!/usr/bin/env python3
import argparse
import json
import os
from pathlib import Path

import torch
from PIL import Image
from torchvision import transforms

IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]

LABELS_FILE = Path("imagenet_classes.json")  # опційно: словник {idx: label}


def load_labels():
    if LABELS_FILE.exists():
        with open(LABELS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        # очікуємо формат {"0": "label0", ...}
        return {int(k): v for k, v in data.items()}
    return None  # якщо файла нема — виведемо індекси


def preprocess(img: Image.Image) -> torch.Tensor:
    t = transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
    ])
    return t(img).unsqueeze(0)


def topk_probs(logits: torch.Tensor, k=3):
    probs = torch.softmax(logits, dim=1)
    p, idx = torch.topk(probs, k)
    return p.squeeze(0).tolist(), idx.squeeze(0).tolist()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("image", help="Path to image file")
    parser.add_argument("--model", default="model.pt", help="TorchScript model path")
    args = parser.parse_args()

    assert os.path.exists(args.model), f"Model not found: {args.model}"
    img = Image.open(args.image).convert("RGB")

    x = preprocess(img)
    model = torch.jit.load(args.model, map_location="cpu")
    model.eval()

    with torch.inference_mode():
        logits = model(x)

    probs, idxs = topk_probs(logits, k=3)
    labels = load_labels()

    print("Top-3 predictions:")
    for i, (p, idx) in enumerate(zip(probs, idxs), 1):
        name = labels.get(idx, f"class_{idx}") if labels else f"class_{idx}"
        print(f"  {i}. {name:25s}  prob={p:.4f}")


if __name__ == "__main__":
    main()
