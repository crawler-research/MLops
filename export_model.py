#!/usr/bin/env python3
import torch
from torchvision.models import mobilenet_v2, MobileNet_V2_Weights

if __name__ == "__main__":
    weights = MobileNet_V2_Weights.DEFAULT
    model = mobilenet_v2(weights=weights)
    model.eval()

    example = torch.randn(1, 3, 224, 224)

    traced = torch.jit.trace(model, example)
    traced.save("model.pt")
