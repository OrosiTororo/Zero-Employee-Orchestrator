"""Cross-Model Judge Pipeline — メインオーケストレーター。"""

from app.judge.models import JudgeResult
from app.judge.segmenter import segment
from app.judge.sampler import sample
from app.judge.evaluator import evaluate
from app.judge.improver import improve


async def judge(original_output: str, context: str = "") -> JudgeResult:
    """Judge パイプラインを実行（Two-stage Detection 統合）。"""
    from app.judge.pre_check import pre_check

    # Stage 1: 安価なプリチェック
    pre_result = await pre_check(original_output, context)
    if not pre_result.passed:
        return JudgeResult(
            segments=[], samples=[], eval_results=[],
            improved_output=original_output,
            overall_score=0.0,
        )

    # Stage 2: Cross-Model Judge（高価）
    segments = await segment(original_output)
    samples = await sample(segments, context)
    eval_results = await evaluate(segments, samples)
    improved = await improve(original_output, eval_results)

    if eval_results:
        overall = sum(er.score for er in eval_results) / len(eval_results)
    else:
        overall = 1.0

    return JudgeResult(
        segments=segments,
        samples=samples,
        eval_results=eval_results,
        improved_output=improved,
        overall_score=round(overall, 2),
    )
