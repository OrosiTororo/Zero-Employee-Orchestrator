"""Tests for analyze_code_safety risk classification.

任意コード実行ベクトル (eval/exec/os.system/subprocess/__import__) は
"high" リスクとして受入ゲート (low/medium のみ通過) で拒否されることを固定する。
"""

from app.services.skill_service import analyze_code_safety


class TestHighRiskExecutionVectors:
    def test_eval_is_high_risk(self):
        report = analyze_code_safety("result = eval(user_input)")
        assert report.risk_level == "high"
        assert report.has_dangerous_code is True

    def test_exec_is_high_risk(self):
        report = analyze_code_safety("exec(payload)")
        assert report.risk_level == "high"

    def test_os_system_is_high_risk(self):
        report = analyze_code_safety("import os\nos.system('ls')")
        assert report.risk_level == "high"

    def test_subprocess_is_high_risk(self):
        report = analyze_code_safety("import subprocess\nsubprocess.run(['ls'])")
        assert report.risk_level == "high"

    def test_dunder_import_is_high_risk(self):
        report = analyze_code_safety("mod = __import__('os')")
        assert report.risk_level == "high"

    def test_credential_access_is_high_risk(self):
        report = analyze_code_safety("key = config['api_key']")
        assert report.risk_level == "high"
        assert report.has_credential_access is True

    def test_auth_token_is_high_risk(self):
        report = analyze_code_safety("headers = {'Authorization': access_token}")
        assert report.risk_level == "high"
        assert report.has_credential_access is True

    def test_destructive_operation_is_high_risk(self):
        report = analyze_code_safety("import shutil\nshutil.rmtree(path)")
        assert report.risk_level == "high"
        assert report.has_destructive_operations is True


class TestMediumRiskCapabilities:
    def test_compile_alone_is_medium(self):
        report = analyze_code_safety("code_obj = compile(src, '<s>', 'eval')")
        assert report.risk_level == "medium"
        assert report.has_dangerous_code is True

    def test_file_write_is_medium(self):
        report = analyze_code_safety("with open('out.txt', 'w') as f:\n    f.write(data)")
        assert report.risk_level == "medium"

    def test_external_http_only_is_medium(self):
        report = analyze_code_safety("import httpx\nhttpx.post(url, json=body)")
        assert report.risk_level == "medium"
        assert report.has_external_communication is True


class TestLowRisk:
    def test_clean_code_is_low(self):
        report = analyze_code_safety("def execute(context):\n    return {'status': 'success'}")
        assert report.risk_level == "low"

    def test_max_tokens_is_not_flagged_as_credential(self):
        # Regression: the credential regex must not match the ``token``
        # substring inside ordinary LLM params like ``max_tokens`` — the
        # fallback skill generator always emits ``max_tokens=2048``.
        report = analyze_code_safety("result = provider.complete(messages=m, max_tokens=2048)")
        assert report.has_credential_access is False
        assert report.risk_level == "low"
        assert report.summary == "No safety issues detected"
