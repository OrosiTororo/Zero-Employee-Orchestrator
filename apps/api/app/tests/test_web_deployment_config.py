"""Static safety checks for the production Web UI deployment."""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]


def test_nginx_ui_blocks_framing_and_overwrites_forwarded_client_ip():
    nginx_config = (REPO_ROOT / "docker" / "nginx.ui.conf").read_text(encoding="utf-8")

    assert 'add_header X-Frame-Options "DENY" always;' in nginx_config
    assert "frame-ancestors 'none'" in nginx_config
    assert 'add_header Permissions-Policy "camera=()' in nginx_config
    assert "proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;" not in nginx_config
    assert nginx_config.count("proxy_set_header X-Forwarded-For $remote_addr;") >= 3
    assert "location = /api/v1/auth/google/callback" in nginx_config
    assert "access_log off;" in nginx_config


def test_full_stack_compose_limits_direct_api_exposure_before_trusting_nginx():
    compose_config = (REPO_ROOT / "docker" / "docker-compose.yml").read_text(encoding="utf-8")

    assert '"127.0.0.1:18234:18234"' in compose_config
    assert "FORWARDED_ALLOW_IPS=*" in compose_config
