"""Evaluator — 複数モデルの結果からスコアを算出。"""

from collections import defaultdict
from app.judge.models import SampleResult, EvalResult


async def evaluate(
    segments: list,
    samples: list[SampleResult],
) -> list[EvalResult]:
    """各セグメントのスコアを算出。3モデル一致→1.0、2/3→0.67、全不一致→0.0"""
    grouped: dict[str, list[SampleResult]] = defaultdict(list)
    for s in samples:
        grouped[s.segment_id].append(s)

    results = []
    for seg_id, seg_samples in grouped.items():
        agrees_count = sum(1 for s in seg_samples if s.agrees)
        total = len(seg_samples)

        if total == 0:
            score = 0.0
        elif agrees_count == total:
            score = 1.0
        elif agrees_count >= total * 2 / 3:
            score = 0.67
        else:
            score = 0.0

        issues = [s.response for s in seg_samples if not s.agrees and s.response]
        results.append(EvalResult(segment_id=seg_id, score=score, issues=issues))

    return results
