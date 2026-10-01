# CDQAI file version: 2.3.6
"""Exercise Ollama with fabricated evidence only; never load application config."""
import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from cdqai.llm.analyst_guidance import LocalOllama, GuidanceUnavailable

if __name__ == "__main__":
    client = LocalOllama(dict(model="llama3:latest", local_only_confirmed=True, timeout_seconds=60))
    start = time.monotonic()
    try:
        client.verify_model()
        print("Local-only model preflight passed.", flush=True)
        draft = client.draft([{"id": "E1", "source": "MODEL_STRUCTURED",
            "fields": ["StructuredScore_pct"],
            "text": "FABRICATED TEST ONLY. Structured model percentile is 99.5. No causal field attribution is available."}],
            "FABRICATED TEST ONLY. Crash severity unknown; no completeness adjustment.")
        print("Synthetic draft validation passed; response content omitted.")
    except GuidanceUnavailable as exc:
        print("Synthetic check failed:", str(exc))
    except Exception as exc:
        print("Synthetic check failed with type:", type(exc).__name__)
    print(f"Elapsed seconds: {time.monotonic() - start:.1f}")
