from __future__ import annotations

import json
import platform

import torch


def main() -> None:
    result = {
        "python_platform": platform.platform(),
        "torch_version": torch.__version__,
        "cuda_available": torch.cuda.is_available(),
        "torch_cuda_version": torch.version.cuda,
        "gpu_count": torch.cuda.device_count() if torch.cuda.is_available() else 0,
        "gpus": [],
    }

    if torch.cuda.is_available():
        for index in range(torch.cuda.device_count()):
            props = torch.cuda.get_device_properties(index)
            result["gpus"].append(
                {
                    "index": index,
                    "name": props.name,
                    "total_vram_gb": round(props.total_memory / 1024**3, 2),
                    "compute_capability": f"{props.major}.{props.minor}",
                    "bf16_supported": bool(torch.cuda.is_bf16_supported()),
                }
            )

    print(json.dumps(result, ensure_ascii=False, indent=2))

    if not result["cuda_available"]:
        raise SystemExit("CUDA GPU를 찾지 못했습니다.")


if __name__ == "__main__":
    main()
