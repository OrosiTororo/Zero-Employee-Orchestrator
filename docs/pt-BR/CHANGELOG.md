# Changelog

> [English](../CHANGELOG.md) | [日本語](../ja-JP/CHANGELOG.md) | [中文](../zh/CHANGELOG.md) | [한국어](../ko-KR/CHANGELOG.md) | Português | [Türkçe](../tr/CHANGELOG.md)

Todas as alterações notáveis deste projeto serão documentadas neste arquivo.

Formato: [Keep a Changelog](https://keepachangelog.com/)
Versionamento: [Semantic Versioning](https://semver.org/)

## [0.1.1] - 2026-03-28

### Adicionado

- **Docker Compose para produção** — Limites de recursos (memória/CPU), isolamento de rede, rotação de logs, sistema de arquivos somente leitura, opção de segurança `no-new-privileges`, `start_period` no healthcheck
- **Verificação Trivy de imagem de contêiner no CI** — Novo job no CI que verifica vulnerabilidades CRITICAL/HIGH nas imagens Docker antes do merge
- **Testes de segurança Red-team no CI** — Novo job no CI que executa a suíte completa de testes Red-team e falha em descobertas críticas
- **65+ chaves de tradução i18n** — Expandido de ~30 para 65+ chaves em todos os 6 idiomas. Cobertura: mensagens de segurança, configurações, navegação, ações comuns, gerenciamento de skills/plugins, saúde do servidor, orçamento/custo, Judge Layer e Browser Assist
- **Padrões de detecção PII ausentes** — Adicionados padrões de carteira de motorista (Japão/EUA) e nome completo japonês, completando todas as 13 categorias de PII
- **Suporte i18n para 6 idiomas** — Adicionados Coreano (한국어), Português (Português) e Turco (Türkçe) às traduções existentes em Japonês, Inglês e Chinês
- **Configurações extensíveis de chave de API LLM** — Agora é possível adicionar provedores personalizados além dos 4 integrados
- **Feedback de padrões de falha do Design Interview** — Busca automática de padrões de falha similares no Experience Memory e Failure Taxonomy

### Alterado

- **Idioma padrão alterado para Inglês** — Mudado de `ja` para `en` para maior adoção internacional (usuários podem definir `LANGUAGE=ja` ou `--lang ja`)
- **Catálogo de modelos atualizado** — GPT-5.4 / GPT-5.4 Mini (de 4.1), Llama 4 (de 3.2), Phi-4 (de 3), Claude Haiku alias sem data
- **Correções de precisão na documentação** — Métricas inflacionadas corrigidas: padrões do prompt guard 40+→28+, conectores de apps 35+→34+, módulos de rotas 41→40. "GPT-5 Mini"→"GPT-5.4 Mini" corrigido em todos os idiomas
- **Navegação estilo Cowork com barra de navegação** — Barra lateral dupla removida, substituída por barra de navegação com ícones e tooltips

### Segurança

- **pip-audit agora bloqueia o build no CI** — `continue-on-error` removido; vulnerabilidades em dependências causam falha no build
- **Testes Red-team fortalecidos** — Handlers de teste agora exercitam módulos de segurança com payloads reais
- **Proteção contra ataque symlink no Sandbox reforçada** — Detecta e bloqueia quando o caminho resolvido aponta para um diretório diferente

## [0.1.0] - 2026-03-12 — Platform v0.1 (Release Consolidado)

Implementação inicial. Consulte o [CHANGELOG em Inglês](../CHANGELOG.md) para detalhes completos.

[0.1.1]: https://github.com/OrosiTororo/Zero-Employee-Orchestrator/releases/tag/v0.1.1
[0.1.0]: https://github.com/OrosiTororo/Zero-Employee-Orchestrator/releases/tag/v0.1.0
