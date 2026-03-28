# Changelog

> [English](../CHANGELOG.md) | [日本語](../ja-JP/CHANGELOG.md) | [中文](../zh/CHANGELOG.md) | 한국어 | [Português](../pt-BR/CHANGELOG.md) | [Türkçe](../tr/CHANGELOG.md)

이 프로젝트의 모든 주요 변경 사항을 기록합니다.

형식: [Keep a Changelog](https://keepachangelog.com/)
버전: [Semantic Versioning](https://semver.org/)

## [0.1.1] - 2026-03-28

### 추가

- **프로덕션 Docker Compose** — 리소스 제한(메모리/CPU), 네트워크 격리, 로그 로테이션, 읽기 전용 파일시스템, `no-new-privileges` 보안 옵션, 헬스체크 `start_period`
- **CI에 Trivy 컨테이너 이미지 스캔 추가** — 병합 전 Docker 이미지의 CRITICAL/HIGH 취약점 스캔
- **CI에 Red-team 보안 테스트 추가** — 전체 Red-team 테스트 스위트 실행, 치명적 발견 시 빌드 실패
- **65+ i18n 번역 키** — 전체 6개 언어에서 약 30개에서 65+개로 확장. 보안 메시지, 설정, 네비게이션, 공통 액션, 스킬/플러그인 관리, 서버 헬스, 예산/비용, Judge Layer, 브라우저 어시스트 포함
- **누락된 PII 검출 패턴 추가** — 운전면허증(일본/미국)과 일본어 성명 패턴 추가, 전체 13개 PII 카테고리 완성
- **6언어 i18n 지원** — 기존 일본어·영어·중국어에 한국어(한국어)·포르투갈어(Português)·터키어(Türkçe) UI 번역 추가
- **확장 가능한 LLM API 키 설정** — 기본 4개 프로바이더 외 커스텀 프로바이더 자유 추가 가능
- **Design Interview 과거 실패 패턴 피드백** — Experience Memory와 Failure Taxonomy에서 유사 실패 패턴을 자동 검색하여 Interview 중 경고·추가 질문을 동적 주입

### 변경

- **기본 언어를 영어로 변경** — 국제적 채택 촉진을 위해 `ja`에서 `en`으로 변경 (사용자는 `LANGUAGE=ja` 또는 `--lang ja`로 변경 가능)
- **모델 카탈로그 최신 업데이트** — GPT-5.4 / GPT-5.4 Mini (4.1에서), Llama 4 (3.2에서), Phi-4 (3에서), Claude Haiku 비날짜 별칭
- **문서 정확성 수정** — 과장 표기 수정: 프롬프트 가드 패턴 40+→28+, 앱 커넥터 35+→34+, 라우트 모듈 41→40. 전 언어에서 "GPT-5 Mini"→"GPT-5.4 Mini" 수정
- **VSCode 스타일 단일 활동 바 네비게이션** — 이중 사이드바 제거, 툴팁이 있는 아이콘 기반 활동 바로 통일

### 보안

- **CI에서 pip-audit 블로킹 적용** — `continue-on-error` 제거, 의존성 취약점 발견 시 빌드 실패
- **Red-team 테스트 강화** — 설정 검증만이 아닌 실제 페이로드로 보안 모듈을 실행하도록 개선
- **Sandbox 심볼릭 링크 공격 방어 강화** — resolve() 후 경로가 원본과 다른 디렉토리를 가리키는 경우 감지·차단

## [0.1.0] - 2026-03-12 — Platform v0.1 (통합 릴리스)

초기 구현. 자세한 내용은 [영어 CHANGELOG](../CHANGELOG.md)를 참조하세요.

[0.1.1]: https://github.com/OrosiTororo/Zero-Employee-Orchestrator/releases/tag/v0.1.1
[0.1.0]: https://github.com/OrosiTororo/Zero-Employee-Orchestrator/releases/tag/v0.1.0
