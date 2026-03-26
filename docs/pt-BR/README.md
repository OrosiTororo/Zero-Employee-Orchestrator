**Language:** [English](../../README.md) | [日本語](../ja-JP/README.md) | [简体中文](../zh-CN/README.md) | [繁體中文](../zh-TW/README.md) | [한국어](../ko-KR/README.md) | **Português (Brasil)** | [Türkçe](../tr/README.md)

# Zero-Employee Orchestrator

[![Stars](https://img.shields.io/github/stars/OrosiTororo/Zero-Employee-Orchestrator?style=flat)](https://github.com/OrosiTororo/Zero-Employee-Orchestrator/stargazers)
[![Forks](https://img.shields.io/github/forks/OrosiTororo/Zero-Employee-Orchestrator?style=flat)](https://github.com/OrosiTororo/Zero-Employee-Orchestrator/network/members)
[![Contributors](https://img.shields.io/github/contributors/OrosiTororo/Zero-Employee-Orchestrator?style=flat)](https://github.com/OrosiTororo/Zero-Employee-Orchestrator/graphs/contributors)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](../../LICENSE)
![Python](https://img.shields.io/badge/-Python-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/-FastAPI-009688?logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/-React-61DAFB?logo=react&logoColor=black)
![TypeScript](https://img.shields.io/badge/-TypeScript-3178C6?logo=typescript&logoColor=white)
![Rust](https://img.shields.io/badge/-Rust-000000?logo=rust&logoColor=white)
![Docker](https://img.shields.io/badge/-Docker-2496ED?logo=docker&logoColor=white)

> **Plataforma de Orquestração de IA — Projetar · Executar · Verificar · Melhorar**

---

<div align="center">

**🌐 Language / 言語 / 语言**

[English](../../README.md) | [日本語](../ja-JP/README.md) | [简体中文](../zh-CN/README.md) | [繁體中文](../zh-TW/README.md) | [한국어](../ko-KR/README.md) | [**Português (Brasil)**](README.md) | [Türkçe](../tr/README.md)

</div>

---

**A plataforma para operar IA como uma organização — não apenas um chatbot.**

Defina fluxos de trabalho de negócios em linguagem natural, orquestre múltiplos agentes de IA com delegação baseada em papéis e execute tarefas com portões de aprovação humana e auditabilidade completa. Construído com uma arquitetura de 9 camadas com Self-Healing DAG, Judge Layer e Experience Memory.

O ZEO em si é gratuito e de código aberto. Os custos de API dos LLMs são pagos diretamente pelos usuários a cada provedor.

---

## Guias

Este repositório é a plataforma em si. Os guias explicam a arquitetura e a filosofia de design.

<table>
<tr>
<td width="33%">
<a href="../../docs/guides/quickstart-guide.md">
<img src="../../assets/images/guides/quickstart-guide.svg" alt="Guia de Início Rápido" />
</a>
</td>
<td width="33%">
<a href="../../docs/guides/architecture-guide.md">
<img src="../../assets/images/guides/architecture-guide.svg" alt="Mergulho na Arquitetura" />
</a>
</td>
<td width="33%">
<a href="../../docs/guides/security-guide.md">
<img src="../../assets/images/guides/security-guide.svg" alt="Guia de Segurança" />
</a>
</td>
</tr>
<tr>
<td align="center"><b>Guia de Início Rápido</b><br/>Instalação, primeiro fluxo de trabalho, básico do CLI. <b>Leia este primeiro.</b></td>
<td align="center"><b>Mergulho na Arquitetura</b><br/>Arquitetura de 9 camadas, orquestração DAG, Judge Layer, Experience Memory.</td>
<td align="center"><b>Guia de Segurança</b><br/>Defesa contra injeção de prompt, portões de aprovação, IAM, sandbox, proteção PII.</td>
</tr>
</table>

| Tópico | O que Você Aprenderá |
|--------|---------------------|
| Arquitetura de 9 Camadas | User → Design Interview → Task Orchestrator → Skill → Judge → Re-Propose → Memory → Provider → Registry |
| Self-Healing DAG | Replanejamento automático e re-proposta em caso de falha de tarefa |
| Judge Layer | Verificação de qualidade em dois estágios + Cross-Model |
| Skill / Plugin / Extension | Extensibilidade em 3 níveis com geração de skills em linguagem natural |
| Human-in-the-Loop | 12 categorias de operações perigosas requerem aprovação humana |
| Design Security-First | Defesa contra injeção de prompt (40+ padrões), mascaramento PII, sandbox de arquivos |

---

## Novidades

### v0.1.0 — Lançamento Inicial (Mar 2026)

- **Arquitetura de 9 camadas** — User Layer → Design Interview → Task Orchestrator → Skill Layer → Judge Layer → Re-Propose → State & Memory → Provider → Skill Registry
- **Self-Healing DAG** — Replanejamento automático em caso de falha com reconstrução dinâmica do DAG
- **Judge Layer** — Primeira passagem baseada em regras + verificação de alta precisão Cross-Model
- **Experience Memory** — Aprende com execuções passadas para melhorar o desempenho futuro
- **Skill / Plugin / Extension** — Extensibilidade em 3 níveis: 8 skills integradas, 10 plugins, 5 extensões
- **Geração de skills em linguagem natural** — Descreva uma skill em linguagem natural e a IA gera automaticamente (com verificações de segurança)
- **Browser Assist** — Chat overlay com extensão Chrome, compartilhamento de tela em tempo real e diagnóstico de erros
- **Geração de mídia** — Imagem (DALL-E, SD), vídeo (Runway ML, Pika), áudio (TTS, ElevenLabs), música (Suno), 3D (registro dinâmico de provedores)
- **Integração de ferramentas de IA** — 25+ ferramentas externas (GitHub, Slack, Jira, Figma, etc.) operáveis por IA
- **Security-first** — Defesa contra injeção de prompt (5 categorias, 40+ padrões), portões de aprovação, IAM, proteção PII, sandbox de arquivos
- **Suporte multi-modelo** — Catálogo dinâmico de modelos via `model_catalog.json`, fallback automático para modelos descontinuados
- **i18n** — Japonês / Inglês / Chinês — UI, respostas da IA e CLI tudo alternado de forma fluída
- **Operação autônoma** — Docker / Cloudflare Workers para execução em segundo plano 24/365
- **Auto-aprimoramento** — IA analisa e melhora suas próprias skills (com aprovação)
- **Comunicação A2A** — Mensagens peer-to-peer entre agentes, canais e negociação

---

## 🖥️ Baixar Aplicativo Desktop

Instaladores desktop pré-compilados estão disponíveis na página de [Releases](https://github.com/OrosiTororo/Zero-Employee-Orchestrator/releases).

| SO | Arquivo | Descrição |
|---|---|---|
| **Windows** | `.msi` / `-setup.exe` | Instalador Windows |
| **macOS** | `.dmg` | macOS (Intel / Apple Silicon) |
| **Linux** | `.AppImage` | Portátil (sem necessidade de instalação) |
| **Linux** | `.deb` / `.rpm` | Debian/Ubuntu / Fedora/RHEL |

Todos os instaladores incluem um **assistente de configuração** onde você escolhe seu idioma (English / 日本語 / 中文). O idioma pode ser alterado a qualquer momento em **Configurações**.

---

## 🚀 Início Rápido

Comece a operar em menos de 2 minutos:

### Passo 1: Instalação

```bash
# PyPI
pip install zero-employee-orchestrator

# Ou a partir do código fonte
git clone https://github.com/OrosiTororo/Zero-Employee-Orchestrator.git
cd Zero-Employee-Orchestrator && pip install .

# Ou Docker
docker compose up -d
```

### Passo 2: Configuração (Sem Necessidade de Chave de API)

```bash
# Opção A: Modo assinatura (sem chave necessária)
zero-employee config set DEFAULT_EXECUTION_MODE subscription

# Opção B: Ollama LLM local (totalmente offline)
zero-employee config set DEFAULT_EXECUTION_MODE free
zero-employee pull qwen3:8b

# Opção C: Plataforma multi-LLM (uma chave, vários modelos)
zero-employee config set OPENROUTER_API_KEY <your-key>

# Opção D: Chaves de API individuais por provedor
zero-employee config set GEMINI_API_KEY <your-key>
```

> **O ZEO em si é gratuito.** Os custos de API dos LLMs são pagos diretamente a cada provedor. Veja [USER_SETUP.md](../../USER_SETUP.md) para detalhes.

### Passo 3: Iniciar

```bash
# Web UI
zero-employee serve
# → http://localhost:18234

# Chat local (Ollama)
zero-employee local --model qwen3:8b --lang en
```

✨ **Pronto!** Você agora tem uma plataforma completa de orquestração de IA com portões de aprovação humana e auditabilidade.

### Alterando o Idioma (CLI)

O idioma padrão é inglês. Você pode alterá-lo de várias formas:

```bash
# Na inicialização
zero-employee chat --lang ja    # Japonês
zero-employee chat --lang zh    # Chinês

# Persistentemente (salvo em ~/.zero-employee/config.json)
zero-employee config set LANGUAGE pt

# Em tempo de execução (no modo chat)
/lang en                         # Mudar para Inglês
/lang ja                         # Mudar para Japonês
/lang zh                         # Mudar para Chinês

# Via API
curl -X PUT http://localhost:18234/api/v1/config \
  -H "Content-Type: application/json" \
  -d '{"key": "LANGUAGE", "value": "pt"}'
```

A configuração de idioma se aplica em todo o sistema: saída do CLI, respostas da IA e a interface Web mudam juntas.

---

## 📦 O que Está Incluído

```
Zero-Employee-Orchestrator/
├── apps/
│   ├── api/                  # Backend FastAPI
│   │   └── app/
│   │       ├── core/               # Config, DB, segurança, i18n
│   │       ├── api/routes/         # 39 módulos de rotas REST API
│   │       ├── api/ws/             # WebSocket
│   │       ├── models/             # SQLAlchemy ORM
│   │       ├── schemas/            # Pydantic DTO
│   │       ├── services/           # Lógica de negócios
│   │       ├── repositories/       # Abstração de I/O do DB
│   │       ├── orchestration/      # DAG, Judge, máquina de estados
│   │       ├── providers/          # Gateway LLM, Ollama, RAG
│   │       ├── security/           # IAM, segredos, sanitização, defesa de prompt
│   │       ├── policies/           # Portões de aprovação, limites de autonomia
│   │       ├── integrations/       # Sentry, MCP, skills externas, Browser Assist
│   │       └── tools/              # Conectores de ferramentas externas
│   ├── desktop/              # Tauri v2 + React UI
│   ├── edge/                 # Cloudflare Workers
│   └── worker/               # Workers em segundo plano
├── skills/                   # 8 skills integradas
├── plugins/                  # 10 manifestos de plugins
├── extensions/               # 5 manifestos de extensões
│   └── browser-assist/
│       └── chrome-extension/ # Extensão Chrome para Browser Assist
├── packages/                 # Pacotes NPM compartilhados
├── docs/                     # Docs multi-idioma & guias
│   ├── ja-JP/                # 日本語
│   ├── zh-CN/                # 简体中文
│   ├── zh-TW/                # 繁體中文
│   ├── ko-KR/                # 한국어
│   ├── pt-BR/                # Português (Brasil)
│   ├── tr/                   # Türkçe
│   └── guides/               # Guias de arquitetura, segurança, início rápido
└── assets/
    └── images/
        ├── guides/           # Imagens de cabeçalho dos guias
        └── logo/             # Ativos de logo
```

---

## 🏗️ Arquitetura de 9 Camadas

```
┌─────────────────────────────────────────┐
│  1. User Layer       — Entrada em linguagem natural      │
│  2. Design Interview — Exploração de requisitos          │
│  3. Task Orchestrator — Decomposição DAG e agendamento   │
│  4. Skill Layer      — Skills especializadas + Contexto  │
│  5. Judge Layer      — QA em dois estágios + Cross-Model │
│  6. Re-Propose       — Rejeição → reconstrução dinâmica  │
│  7. State & Memory   — Experience Memory                │
│  8. Provider         — Gateway LLM (LiteLLM)            │
│  9. Skill Registry   — Publicar / Buscar / Importar     │
└─────────────────────────────────────────┘
```

---

## 🎯 Principais Funcionalidades

### Orquestração Central

| Funcionalidade | Descrição |
|---------------|-----------|
| **Design Interview** | Exploração e refinamento de requisitos em linguagem natural |
| **Spec / Plan / Tasks** | Artefatos intermediários estruturados — reutilizáveis, auditáveis, reversíveis |
| **Task Orchestrator** | Planejamento baseado em DAG com estimativa de custos e troca de modo de qualidade |
| **Judge Layer** | Primeira passagem baseada em regras + verificação Cross-Model de alta precisão |
| **Self-Healing / Re-Propose** | Replanejamento automático em caso de falha com reconstrução dinâmica do DAG |
| **Experience Memory** | Aprende com execuções passadas para melhorar o desempenho futuro |

### Extensibilidade

| Funcionalidade | Descrição |
|---------------|-----------|
| **Skill / Plugin / Extension** | Extensibilidade em 3 níveis com gerenciamento CRUD completo |
| **Geração de Skills em Linguagem Natural** | Descreva em linguagem natural → IA gera automaticamente (com verificações de segurança) |
| **Marketplace de Skills** | Publicação, busca, avaliação e instalação de skills da comunidade |
| **Importação de Skills Externas** | Importar skills de repositórios GitHub |
| **Auto-aprimoramento** | IA analisa e melhora suas próprias skills (com aprovação) |
| **Meta-Skills** | IA aprende a aprender (Feeling / Seeing / Dreaming / Making / Learning) |

### Capacidades de IA

| Funcionalidade | Descrição |
|---------------|-----------|
| **Browser Assist** | Overlay de extensão Chrome — IA vê sua tela em tempo real |
| **Geração de Mídia** | Imagem, vídeo, áudio, música, 3D — com registro dinâmico de provedores |
| **Integração de Ferramentas de IA** | 25+ ferramentas externas (GitHub, Slack, Jira, Figma, etc.) |
| **Comunicação A2A** | Mensagens peer-to-peer entre agentes, canais e negociação |
| **IA Avatar** | Aprende seus padrões de decisão e evolui com você |
| **IA Secretária** | Brain dump → tarefas estruturadas, ponte entre você e a organização de IA |
| **Motor de Reaproveitamento** | Converte automaticamente 1 conteúdo em 10 formatos de mídia |

### Segurança

| Funcionalidade | Descrição |
|---------------|-----------|
| **Defesa contra Injeção de Prompt** | 5 categorias, 40+ padrões de detecção |
| **Portões de Aprovação** | 12 categorias de operações perigosas requerem aprovação humana |
| **Sandbox de Arquivos** | IA só pode acessar pastas permitidas pelo usuário (padrão: STRICT) |
| **Proteção de Dados** | Controle de política de upload/download (padrão: LOCKDOWN) |
| **Proteção PII** | Detecção automática e mascaramento de 13 categorias de informações pessoais |
| **IAM** | Separação de contas humanas/IA, IA impedida de acessar segredos e admin |
| **Segurança Red-team** | 8 categorias, 20+ testes de autoavaliação de vulnerabilidades |

### Operações

| Funcionalidade | Descrição |
|---------------|-----------|
| **Suporte Multi-modelo** | Catálogo dinâmico, fallback automático, substituição de provedor por tarefa |
| **i18n** | Japonês / Inglês / Chinês — UI, respostas da IA, CLI |
| **Operação Autônoma** | Docker / Cloudflare Workers — roda mesmo com seu PC desligado |
| **Agendador 24/365** | 9 tipos de gatilho: cron, criação de ticket, limiar de orçamento, etc. |
| **Integração iPaaS** | Integração webhook n8n / Zapier / Make |
| **Cloud Native** | Camada de abstração AWS / GCP / Azure / Cloudflare |
| **Governança & Conformidade** | GDPR / HIPAA / SOC2 / ISO27001 / CCPA / APPI |

---

## 🔒 Segurança

O ZEO é projetado com **segurança em primeiro lugar** e defesa em múltiplas camadas:

| Camada | Descrição |
|--------|-----------|
| **Defesa contra Injeção de Prompt** | Detecta e bloqueia injeção de instruções de entradas externas (5 categorias, 40+ padrões) |
| **Portões de Aprovação** | 12 categorias de operações perigosas (envio, exclusão, cobrança, alteração de permissão) requerem aprovação humana |
| **Limites de Autonomia** | Limita explicitamente o que a IA pode fazer de forma autônoma |
| **IAM** | Contas humanas/IA separadas; IA impedida de acessar segredos e permissões admin |
| **Gestão de Segredos** | Criptografia Fernet, mascaramento automático, suporte a rotação |
| **Sanitização** | Remoção automática de chaves de API, tokens e PII |
| **Headers de Segurança** | CSP, HSTS, X-Frame-Options em todas as respostas |
| **Limitação de Taxa** | Limitação de taxa de API baseada em slowapi |
| **Log de Auditoria** | Todas as operações críticas registradas (integrado desde o design, não adicionado depois) |

Veja [SECURITY.md](../../SECURITY.md) para relatar vulnerabilidades.

---

## 🖥️ Referência CLI

```bash
zero-employee serve              # Iniciar servidor API
zero-employee serve --port 8000  # Porta personalizada
zero-employee serve --reload     # Hot reload

zero-employee chat               # Modo chat (todos os provedores)
zero-employee chat --mode free   # Modo gratuito (Ollama / g4f)
zero-employee chat --lang en     # Seleção de idioma

zero-employee local              # Chat local (Ollama)
zero-employee local --model qwen3:8b --lang en

zero-employee models             # Listar modelos instalados
zero-employee pull qwen3:8b      # Baixar modelo

zero-employee config list        # Mostrar todas as configurações
zero-employee config set <KEY>   # Definir um valor
zero-employee config get <KEY>   # Obter um valor

zero-employee db upgrade         # Executar migrações do DB
zero-employee health             # Verificação de saúde
zero-employee security status    # Status de segurança
zero-employee update             # Atualizar para a versão mais recente
```

---

## 🤖 Modelos LLM Suportados

Gerenciado via `model_catalog.json` — troque modelos sem alterar código.

| Modo | Descrição | Exemplos |
|------|-----------|---------|
| **Quality** | Mais alta qualidade | Claude Opus, GPT-5.4, Gemini 2.5 Pro |
| **Speed** | Resposta rápida | Claude Haiku, GPT-5 Mini, Gemini 2.5 Flash |
| **Cost** | Baixo custo | Haiku, Mini, Flash Lite, DeepSeek |
| **Free** | Gratuito | Nível gratuito Gemini, Ollama local |
| **Subscription** | Sem chave de API necessária | via g4f |

Substituição de provedor por tarefa é suportada — especifique provedor, modelo e modo de execução por tarefa.

---

## 🧩 Skill / Plugin / Extension

### Extensibilidade em 3 Níveis

| Tipo | Descrição | Exemplos |
|------|-----------|---------|
| **Skill** | Processamento especializado de propósito único | spec-writer, review-assistant, browser-assist |
| **Plugin** | Agrupa múltiplas Skills | ai-secretary, ai-self-improvement, youtube |
| **Extension** | Integração de sistema & infraestrutura | mcp, oauth, notifications, browser-assist |

### Gere Skills com Linguagem Natural

```bash
POST /api/v1/registry/skills/generate
{
  "description": "Uma skill que resume documentos longos em 3 pontos-chave"
}
```

16 padrões perigosos são auto-detectados. Apenas skills que passam nas verificações de segurança são registradas.

---

## 🌐 Browser Assist

Chat overlay com extensão Chrome — IA vê sua tela em tempo real e te guia.

- **Chat Overlay**: UI de chat diretamente em qualquer site
- **Compartilhamento de Tela em Tempo Real**: IA vê o que você vê (sem screenshots manuais)
- **Diagnóstico de Erros**: IA lê mensagens de erro na tela e sugere correções
- **Assistência em Formulários**: Orientação passo-a-passo campo por campo
- **Privacidade em Primeiro Lugar**: Screenshots processados temporariamente, PII mascarado automaticamente, campos de senha desfocados

### Configuração

```
1. Carregue extensions/browser-assist/chrome-extension/ no Chrome
   → chrome://extensions → Modo desenvolvedor → "Carregar sem compactação"
2. Clique no ícone de chat em qualquer site
3. Faça perguntas por texto ou compartilhe sua tela com o botão de screenshot
```

---

## 🛠️ Stack Tecnológica

### Backend
- Python 3.12+ / FastAPI / uvicorn
- SQLAlchemy 2.x (async) + Alembic
- SQLite (dev) / PostgreSQL (produção)
- LiteLLM Router SDK
- bcrypt / Criptografia Fernet
- Limitação de taxa slowapi

### Frontend
- React 19 + TypeScript + Vite
- shadcn/ui + Tailwind CSS
- TanStack Query + Zustand

### Desktop
- Tauri v2 (Rust) + Python sidecar

### Deploy
- Docker + docker-compose
- Cloudflare Workers (serverless)

---

## ❓ FAQ

<details>
<summary><b>Preciso de chaves de API para começar?</b></summary>

Não. Você pode usar o modo assinatura (sem chave necessária) ou Ollama para IA local totalmente offline. Veja a seção Início Rápido acima.
</details>

<details>
<summary><b>Quanto custa?</b></summary>

O ZEO em si é gratuito. Os custos de API dos LLMs são pagos diretamente por você a cada provedor (OpenAI, Anthropic, Google, etc.). Você também pode rodar totalmente gratuito com modelos locais Ollama.
</details>

<details>
<summary><b>Posso usar múltiplos provedores de LLM simultaneamente?</b></summary>

Sim. O ZEO suporta substituição de provedor por tarefa — você pode usar Claude para revisões de spec de alta qualidade e GPT para execução rápida de tarefas no mesmo fluxo de trabalho.
</details>

<details>
<summary><b>Meus dados estão seguros?</b></summary>

O ZEO é projetado para auto-hospedagem. Seus dados ficam na sua infraestrutura. O sandbox de arquivos é STRICT por padrão, transferência de dados é LOCKDOWN por padrão, e detecção automática de PII é habilitada por padrão.
</details>

<details>
<summary><b>Qual a diferença para AutoGen / CrewAI / LangGraph?</b></summary>

O ZEO é uma **plataforma de fluxo de trabalho de negócios**, não um framework para desenvolvedores. Ele fornece portões de aprovação humana, log de auditoria, sistema de extensibilidade em 3 níveis, browser assist, geração de mídia e uma API REST completa — tudo projetado para operar IA como uma organização, não apenas encadear prompts.
</details>

---

## 🧪 Desenvolvimento

```bash
# Configuração
git clone https://github.com/OrosiTororo/Zero-Employee-Orchestrator.git
cd Zero-Employee-Orchestrator
pip install -e ".[dev]"

# Iniciar (hot reload)
zero-employee serve --reload

# Testar
pytest apps/api/app/tests/

# Lint
ruff check apps/api/app/
ruff format apps/api/app/
```

---

## 🤝 Contribuições

Contribuições são bem-vindas.

1. Fork → Branch → PR (fluxo padrão)
2. Questões de segurança: siga [SECURITY.md](../../SECURITY.md) para relato privado
3. Padrões de código: formato ruff, type hints obrigatórias, async def

---

## 💜 Patrocinadores

Este projeto é gratuito e de código aberto. Patrocinadores ajudam a manter e fazer o projeto crescer.

[**Torne-se um Patrocinador**](https://github.com/sponsors/OrosiTororo)

---

## 🌟 Histórico de Stars

[![Star History Chart](https://api.star-history.com/svg?repos=OrosiTororo/Zero-Employee-Orchestrator&type=Date)](https://star-history.com/#OrosiTororo/Zero-Employee-Orchestrator&Date)

---

## 📄 Licença

MIT — Use livremente, modifique conforme necessário, contribua de volta se puder.

---

<p align="center">
  <strong>Zero-Employee Orchestrator</strong> — Opere IA como uma organização.<br>
  Construído com segurança, auditabilidade e supervisão humana em mente.
</p>
