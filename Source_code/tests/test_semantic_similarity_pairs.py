"""
Quick semantic-similarity probe for the user-requested Persian word pairs.

Runs both backends so we can see what semantic search would actually do:
  - sentence_transformer: the bundled MiniLM model, what production uses.
  - hash: the deterministic lexical fallback.

For each pair we also show what Elasticsearch's `cosineSimilarity + 1.0`
script_score would produce (range 0..2; >1 means positively related).
"""

import math
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))


def cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def run_backend(label, backend):
    os.environ["SEMANTIC_BACKEND"] = backend

    # Force config + cached model reload so the env change takes effect.
    for mod in [
        "Source_code.utils.offline_semantic",
        "Source_code.config",
    ]:
        if mod in sys.modules:
            del sys.modules[mod]

    from Source_code.config import config  # noqa: E402
    from Source_code.utils.offline_semantic import generate_offline_semantic_vector  # noqa: E402

    pairs = [
        ("ماهانه", "ماهیانه"),                # synonyms (monthly)
        ("اعلام بفرمایید", "اعلامبفرمایید"),  # space vs no-space
        ("ماهانه", "گربه"),                   # unrelated control
    ]

    print(f"\n=== backend: {label}  (dims={config.SEMANTIC_VECTOR_DIMS}) ===")
    print(f"  model path: {config.SEMANTIC_MODEL_PATH}")
    print(f"  model exists: {os.path.isdir(config.SEMANTIC_MODEL_PATH)}")

    results = []
    for a, b in pairs:
        va = generate_offline_semantic_vector(a)
        vb = generate_offline_semantic_vector(b)
        sim = cosine(va, vb)
        es_score = sim + 1.0  # what semantic_search() returns from ES
        results.append((a, b, sim, es_score))
        print(f"  '{a}'  vs  '{b}'")
        print(f"      cosine = {sim:+.4f}    ES script_score = {es_score:.4f}")

    return results


def find_similarity(results, first, second):
    for left, right, sim, es_score in results:
        if left == first and right == second:
            return sim, es_score
    raise AssertionError(f"Pair not found: {first!r}, {second!r}")


def test_sentence_transformer_semantic_pairs_pass():
    results = run_backend("sentence_transformer", "sentence_transformer")

    monthly_sim, monthly_score = find_similarity(results, "ماهانه", "ماهیانه")
    phrase_sim, phrase_score = find_similarity(results, "اعلام بفرمایید", "اعلامبفرمایید")

    assert monthly_sim >= 0.60, f"ماهانه/ماهیانه similarity too low: {monthly_sim:.4f}, score={monthly_score:.4f}"
    assert phrase_sim >= 0.60, f"اعلام بفرمایید/اعلامبفرمایید similarity too low: {phrase_sim:.4f}, score={phrase_score:.4f}"


def main():
    st = run_backend("sentence_transformer", "sentence_transformer")
    hs = run_backend("hash", "hash")

    print("\n=== verdict (sentence_transformer, the production backend) ===")
    threshold = 0.60  # what we'd loosely call "semantically related"
    for a, b, sim, _ in st[:-1]:  # skip control
        verdict = "PASS" if sim >= threshold else "FAIL"
        print(f"  [{verdict}] '{a}' ~ '{b}'  cosine={sim:.4f}  (>= {threshold})")


if __name__ == "__main__":
    main()
