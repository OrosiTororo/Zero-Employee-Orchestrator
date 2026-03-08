"""Skill テンプレート — 新規 Skill 作成のベース.

使い方:
1. このファイルをコピーして新しい Skill を作成する
2. SKILL_MANIFEST を編集して Skill のメタ情報を設定する
3. execute() 関数に実行ロジックを実装する
4. テストを書いて動作確認する
"""

SKILL_MANIFEST = {
    "slug": "my-skill",
    "name": "My Skill",
    "description": "スキルの説明を記入",
    "version": "0.1.0",
    "skill_type": "custom",
    "author": "",
    "permissions": {
        "read_local": False,
        "write_local": False,
        "external_api": False,
        "external_send": False,
    },
    "required_providers": [],
    "incompatible_skills": [],
    "estimated_cost": "low",
}


async def execute(context: dict) -> dict:
    """スキルを実行する.

    Args:
        context: 実行コンテキスト
            - input: ユーザー入力
            - local_context: ローカルファイル情報
            - provider: LLM プロバイダー
            - settings: 設定

    Returns:
        実行結果
            - status: "success" | "error" | "needs_approval"
            - output: 出力データ
            - artifacts: 成果物リスト
            - cost_usd: 使用コスト
    """
    return {
        "status": "success",
        "output": "スキル実行結果をここに返す",
        "artifacts": [],
        "cost_usd": 0.0,
    }
