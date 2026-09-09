from __future__ import annotations

import json

from bolt_thesis.clients.vllm import VLLMClient


def main() -> None:
    client = VLLMClient()
    result = client.check_server()
    print(json.dumps(result, ensure_ascii=False, indent=2))

    if not result["model_available"]:
        raise SystemExit("설정한 모델이 vLLM 서버에 없습니다.")


if __name__ == "__main__":
    main()
