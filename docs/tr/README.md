**Language:** [English](../../README.md) | [日本語](../ja-JP/README.md) | [简体中文](../zh-CN/README.md) | [繁體中文](../zh-TW/README.md) | [한국어](../ko-KR/README.md) | [Português (Brasil)](../pt-BR/README.md) | **Türkçe**

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

> **Yapay Zeka Orkestrasyon Platformu — Tasarla · Yürüt · Doğrula · Geliştir**

---

<div align="center">

**🌐 Language / 言語 / 语言**

[English](../../README.md) | [日本語](../ja-JP/README.md) | [简体中文](../zh-CN/README.md) | [繁體中文](../zh-TW/README.md) | [한국어](../ko-KR/README.md) | [Português (Brasil)](../pt-BR/README.md) | [**Türkçe**](README.md)

</div>

---

**Yapay zekayı bir organizasyon olarak çalıştırma platformu — sadece bir sohbet botu değil.**

İş akışlarını doğal dilde tanımlayın, rol tabanlı yetkilendirme ile birden fazla yapay zeka ajanını düzenleyin ve insan onay kapıları ile tam denetlenebilirlik sağlayarak görevleri yürütün. Self-Healing DAG, Judge Layer ve Experience Memory'ye sahip 9 katmanlı mimariyle oluşturulmuştur.

ZEO'nun kendisi ücretsiz ve açık kaynaklıdır. LLM API maliyetleri kullanıcılar tarafından doğrudan her sağlayıcıya ödenir.

---

## Kılavuzlar

Bu depo platformun kendisidir. Kılavuzlar mimariyi ve tasarım felsefesini açıklar.

<table>
<tr>
<td width="33%">
<a href="../../docs/guides/quickstart-guide.md">
<img src="../../assets/images/guides/quickstart-guide.svg" alt="Hızlı Başlangıç Kılavuzu" />
</a>
</td>
<td width="33%">
<a href="../../docs/guides/architecture-guide.md">
<img src="../../assets/images/guides/architecture-guide.svg" alt="Mimari Derinlemesine İnceleme" />
</a>
</td>
<td width="33%">
<a href="../../docs/guides/security-guide.md">
<img src="../../assets/images/guides/security-guide.svg" alt="Güvenlik Kılavuzu" />
</a>
</td>
</tr>
<tr>
<td align="center"><b>Hızlı Başlangıç Kılavuzu</b><br/>Kurulum, ilk iş akışı, CLI temelleri. <b>Önce bunu okuyun.</b></td>
<td align="center"><b>Mimari Derinlemesine İnceleme</b><br/>9 katmanlı mimari, DAG orkestrasyonu, Judge Layer, Experience Memory.</td>
<td align="center"><b>Güvenlik Kılavuzu</b><br/>Prompt enjeksiyon savunması, onay kapıları, IAM, sandbox, PII koruması.</td>
</tr>
</table>

| Konu | Öğrenecekleriniz |
|------|-----------------|
| 9 Katmanlı Mimari | User → Design Interview → Task Orchestrator → Skill → Judge → Re-Propose → Memory → Provider → Registry |
| Self-Healing DAG | Görev başarısızlığında otomatik yeniden planlama ve yeniden teklif |
| Judge Layer | Kural tabanlı ilk geçiş + Cross-Model yüksek doğruluklu doğrulama |
| Skill / Plugin / Extension | Doğal dilde beceri oluşturma ile 3 katmanlı genişletilebilirlik |
| Human-in-the-Loop | 12 tehlikeli işlem kategorisi insan onayı gerektirir |
| Güvenlik Öncelikli Tasarım | Prompt enjeksiyon savunması (40+ desen), PII maskeleme, dosya sandbox'ı |

---

## Yenilikler

### v0.1.0 — İlk Sürüm (Mart 2026)

- **9 katmanlı mimari** — User Layer → Design Interview → Task Orchestrator → Skill Layer → Judge Layer → Re-Propose → State & Memory → Provider → Skill Registry
- **Self-Healing DAG** — Görev başarısızlığında dinamik DAG yeniden yapılandırma ile otomatik yeniden planlama
- **Judge Layer** — Kural tabanlı ilk geçiş + Cross-Model yüksek doğruluklu doğrulama
- **Experience Memory** — Geçmiş yürütmelerden öğrenerek gelecek performansı iyileştirme
- **Skill / Plugin / Extension** — 3 katmanlı genişletilebilirlik: 8 yerleşik beceri, 10 eklenti, 5 uzantı
- **Doğal dilde beceri oluşturma** — Bir beceriyi doğal dilde tanımlayın, yapay zeka otomatik olarak oluşturur (güvenlik kontrolleriyle)
- **Tarayıcı Asistanı** — Chrome uzantısı overlay sohbet, gerçek zamanlı ekran paylaşımı ve hata teşhisi
- **Medya oluşturma** — Görüntü (DALL-E, SD), video (Runway ML, Pika), ses (TTS, ElevenLabs), müzik (Suno), 3D (dinamik sağlayıcı kaydı)
- **Yapay zeka araç entegrasyonu** — 25+ harici araç (GitHub, Slack, Jira, Figma vb.) yapay zeka tarafından çalıştırılabilir
- **Güvenlik öncelikli** — Prompt enjeksiyon savunması (5 kategori, 40+ desen), onay kapıları, IAM, PII koruması, dosya sandbox'ı
- **Çoklu model desteği** — `model_catalog.json` ile dinamik model kataloğu, kullanım dışı modeller için otomatik geri dönüş
- **i18n** — Japonca / İngilizce / Çince — Arayüz, yapay zeka yanıtları ve CLI kesintisiz geçiş
- **Otonom çalışma** — Docker / Cloudflare Workers ile 24/365 arka plan yürütme
- **Kendini geliştirme** — Yapay zeka kendi becerilerini analiz eder ve geliştirir (onay gerekli)
- **A2A iletişim** — Ajanlar arası eşler arası mesajlaşma, kanallar ve müzakere

---

## 🖥️ Masaüstü Uygulamasını İndirin

Önceden derlenmiş masaüstü yükleyiciler [Releases](https://github.com/OrosiTororo/Zero-Employee-Orchestrator/releases) sayfasında mevcuttur.

| İşletim Sistemi | Dosya | Açıklama |
|---|---|---|
| **Windows** | `.msi` / `-setup.exe` | Windows yükleyici |
| **macOS** | `.dmg` | macOS (Intel / Apple Silicon) |
| **Linux** | `.AppImage` | Taşınabilir (kurulum gerektirmez) |
| **Linux** | `.deb` / `.rpm` | Debian/Ubuntu / Fedora/RHEL |

Tüm yükleyiciler, dilinizi (English / 日本語 / 中文 / 한국어 / Português / Türkçe) seçebileceğiniz bir **kurulum sihirbazı** içerir. Dil, **Ayarlar**'dan her zaman değiştirilebilir.

---

## 🚀 Hızlı Başlangıç

2 dakikadan kısa sürede çalışmaya başlayın:

### Adım 1: Kurulum

```bash
# PyPI
pip install zero-employee-orchestrator

# Veya kaynak koddan
git clone https://github.com/OrosiTororo/Zero-Employee-Orchestrator.git
cd Zero-Employee-Orchestrator && pip install .

# Veya Docker
docker compose up -d
```

### Adım 2: Yapılandırma (API Anahtarı Gerekmez)

```bash
# Seçenek A: Abonelik modu (anahtar gerekmez)
zero-employee config set DEFAULT_EXECUTION_MODE subscription

# Seçenek B: Ollama yerel LLM (tamamen çevrimdışı)
zero-employee config set DEFAULT_EXECUTION_MODE free
zero-employee pull qwen3:8b

# Seçenek C: Çoklu LLM platformu (bir anahtar, birçok model)
zero-employee config set OPENROUTER_API_KEY <your-key>

# Seçenek D: Her sağlayıcı için ayrı API anahtarları
zero-employee config set GEMINI_API_KEY <your-key>
```

> **ZEO'nun kendisi ücretsizdir.** LLM API maliyetleri doğrudan her sağlayıcıya ödenir. Ayrıntılar için [USER_SETUP.md](../../USER_SETUP.md) belgesine bakın.

### Adım 3: Başlatma

```bash
# Web Arayüzü
zero-employee serve
# → http://localhost:18234

# Yerel sohbet (Ollama)
zero-employee local --model qwen3:8b --lang en
```

✨ **İşte bu kadar!** İnsan onay kapıları ve denetlenebilirlik ile tam bir yapay zeka orkestrasyon platformuna sahipsiniz.

### Dil Değiştirme (CLI)

Varsayılan dil İngilizce'dir. Birkaç yolla değiştirebilirsiniz:

```bash
# Başlatırken
zero-employee chat --lang ja    # Japonca
zero-employee chat --lang zh    # Çince
zero-employee chat --lang ko    # Korece
zero-employee chat --lang pt    # Portekizce
zero-employee chat --lang tr    # Türkçe

# Kalıcı olarak (~/.zero-employee/config.json dosyasına kaydedilir)
zero-employee config set LANGUAGE tr

# Çalışma zamanında (sohbet modunda)
/lang en                         # İngilizce'ye geç
/lang ja                         # Japonca'ya geç
/lang zh                         # Çince'ye geç
/lang ko                         # Korece'ye geç
/lang pt                         # Portekizce'ye geç
/lang tr                         # Türkçe'ye geç

# API üzerinden
curl -X PUT http://localhost:18234/api/v1/config \
  -H "Content-Type: application/json" \
  -d '{"key": "LANGUAGE", "value": "tr"}'
```

Dil ayarı sistem genelinde geçerlidir: CLI çıktısı, yapay zeka yanıtları ve Web arayüzü birlikte değişir.

---

## 📦 İçindekiler

```
Zero-Employee-Orchestrator/
├── apps/
│   ├── api/                  # FastAPI arka ucu
│   │   └── app/
│   │       ├── core/               # Yapılandırma, VT, güvenlik, i18n
│   │       ├── api/routes/         # 39 REST API rota modülü
│   │       ├── api/ws/             # WebSocket
│   │       ├── models/             # SQLAlchemy ORM
│   │       ├── schemas/            # Pydantic DTO
│   │       ├── services/           # İş mantığı
│   │       ├── repositories/       # VT G/Ç soyutlama
│   │       ├── orchestration/      # DAG, Judge, durum makinesi
│   │       ├── providers/          # LLM ağ geçidi, Ollama, RAG
│   │       ├── security/           # IAM, gizli anahtar, temizleme, prompt savunma
│   │       ├── policies/           # Onay kapıları, otonomi sınırları
│   │       ├── integrations/       # Sentry, MCP, harici beceriler, Tarayıcı Asistanı
│   │       └── tools/              # Harici araç bağlayıcıları
│   ├── desktop/              # Tauri v2 + React UI
│   ├── edge/                 # Cloudflare Workers
│   └── worker/               # Arka plan çalışanları
├── skills/                   # 8 yerleşik beceri
├── plugins/                  # 10 eklenti bildirimi
├── extensions/               # 5 uzantı bildirimi
│   └── browser-assist/
│       └── chrome-extension/ # Tarayıcı Asistanı Chrome uzantısı
├── packages/                 # Paylaşılan NPM paketleri
├── docs/                     # Çok dilli belgeler ve kılavuzlar
│   ├── ja-JP/                # 日本語
│   ├── zh-CN/                # 简体中文
│   ├── zh-TW/                # 繁體中文
│   ├── ko-KR/                # 한국어
│   ├── pt-BR/                # Português (Brasil)
│   ├── tr/                   # Türkçe
│   └── guides/               # Mimari, güvenlik, hızlı başlangıç kılavuzları
└── assets/
    └── images/
        ├── guides/           # Kılavuz başlık görselleri
        └── logo/             # Logo varlıkları
```

---

## 🏗️ 9 Katmanlı Mimari

```
┌─────────────────────────────────────────┐
│  1. User Layer       — Doğal dilde girdi              │
│  2. Design Interview — Gereksinim keşfi               │
│  3. Task Orchestrator — DAG ayrıştırma ve zamanlama   │
│  4. Skill Layer      — Uzmanlaşmış Beceriler + Bağlam │
│  5. Judge Layer      — İki aşamalı + Cross-Model KG   │
│  6. Re-Propose       — Ret → dinamik DAG yeniden inşa │
│  7. State & Memory   — Experience Memory              │
│  8. Provider         — LLM Ağ Geçidi (LiteLLM)       │
│  9. Skill Registry   — Yayınla / Ara / İçe Aktar     │
└─────────────────────────────────────────┘
```

---

## 🎯 Temel Özellikler

### Çekirdek Orkestrasyon

| Özellik | Açıklama |
|---------|----------|
| **Design Interview** | Doğal dilde gereksinim keşfi ve detaylandırma |
| **Spec / Plan / Tasks** | Yapılandırılmış ara çıktılar — yeniden kullanılabilir, denetlenebilir, geri alınabilir |
| **Task Orchestrator** | DAG tabanlı planlama, maliyet tahmini ve kalite modu geçişi |
| **Judge Layer** | Kural tabanlı ilk geçiş + Cross-Model yüksek doğruluklu doğrulama |
| **Self-Healing / Re-Propose** | Başarısızlıkta otomatik yeniden planlama, dinamik DAG yeniden yapılandırma |
| **Experience Memory** | Geçmiş yürütmelerden öğrenerek gelecek performansı iyileştirme |

### Genişletilebilirlik

| Özellik | Açıklama |
|---------|----------|
| **Skill / Plugin / Extension** | Tam CRUD yönetimi ile 3 katmanlı genişletilebilirlik |
| **Doğal Dilde Beceri Oluşturma** | Doğal dilde açıklayın → Yapay zeka otomatik oluşturur (güvenlik kontrolleriyle) |
| **Beceri Pazaryeri** | Topluluk becerilerinin yayınlanması, aranması, incelenmesi ve kurulması |
| **Harici Beceri İçe Aktarma** | GitHub depolarından beceri içe aktarma |
| **Kendini Geliştirme** | Yapay zeka kendi becerilerini analiz eder ve geliştirir (onay gerekli) |
| **Meta Beceriler** | Yapay zeka öğrenmeyi öğrenir (Feeling / Seeing / Dreaming / Making / Learning) |

### Yapay Zeka Yetenekleri

| Özellik | Açıklama |
|---------|----------|
| **Tarayıcı Asistanı** | Chrome uzantısı overlay — Yapay zeka ekranınızı gerçek zamanlı görür |
| **Medya Oluşturma** | Görüntü, video, ses, müzik, 3D — dinamik sağlayıcı kaydıyla |
| **Yapay Zeka Araç Entegrasyonu** | 25+ harici araç (GitHub, Slack, Jira, Figma vb.) |
| **A2A İletişim** | Ajanlar arası eşler arası mesajlaşma, kanallar ve müzakere |
| **Avatar Yapay Zeka** | Karar kalıplarınızı öğrenir ve sizinle birlikte gelişir |
| **Sekreter Yapay Zeka** | Beyin boşaltma → yapılandırılmış görevler, siz ve yapay zeka organizasyonu arasında köprü |
| **Yeniden Kullanım Motoru** | 1 içeriği 10 medya formatına otomatik dönüştürme |

### Güvenlik

| Özellik | Açıklama |
|---------|----------|
| **Prompt Enjeksiyon Savunması** | 5 kategori, 40+ tespit deseni |
| **Onay Kapıları** | 12 tehlikeli işlem kategorisi insan onayı gerektirir |
| **Dosya Sandbox'ı** | Yapay zeka yalnızca kullanıcı tarafından izin verilen klasörlere erişebilir (varsayılan: STRICT) |
| **Veri Koruması** | Yükleme/indirme politika kontrolü (varsayılan: LOCKDOWN) |
| **PII Koruması** | 13 kişisel bilgi kategorisinin otomatik tespiti ve maskelenmesi |
| **IAM** | İnsan/yapay zeka hesap ayrımı, yapay zekanın gizli anahtar ve yönetici erişimi engellenir |
| **Kırmızı Takım Güvenliği** | 8 kategori, 20+ test ile öz-zafiyet değerlendirmesi |

### Operasyonlar

| Özellik | Açıklama |
|---------|----------|
| **Çoklu Model Desteği** | Dinamik katalog, otomatik geri dönüş, görev başına sağlayıcı geçersiz kılma |
| **i18n** | Japonca / İngilizce / Çince — Arayüz, yapay zeka yanıtları, CLI |
| **Otonom Çalışma** | Docker / Cloudflare Workers — Bilgisayarınız kapalıyken bile çalışır |
| **24/365 Zamanlayıcı** | 9 tetikleyici türü: cron, bilet oluşturma, bütçe eşiği vb. |
| **iPaaS Entegrasyonu** | n8n / Zapier / Make webhook entegrasyonu |
| **Bulut Yerel** | AWS / GCP / Azure / Cloudflare soyutlama katmanı |
| **Yönetişim ve Uyum** | GDPR / HIPAA / SOC2 / ISO27001 / CCPA / APPI |

---

## 🔒 Güvenlik

ZEO çok katmanlı savunma ile **güvenlik öncelikli** tasarlanmıştır:

| Katman | Açıklama |
|--------|----------|
| **Prompt Enjeksiyon Savunması** | Harici girdilerden talimat enjeksiyonunu tespit eder ve engeller (5 kategori, 40+ desen) |
| **Onay Kapıları** | 12 tehlikeli işlem kategorisi (gönderme, silme, faturalandırma, izin değişiklikleri) insan onayı gerektirir |
| **Otonomi Sınırları** | Yapay zekanın otonom olarak yapabileceklerini açıkça sınırlar |
| **IAM** | Ayrı insan/yapay zeka hesapları; yapay zekanın gizli anahtar ve yönetici izinlerine erişimi engellenir |
| **Gizli Anahtar Yönetimi** | Fernet şifreleme, otomatik maskeleme, rotasyon desteği |
| **Temizleme** | API anahtarları, belirteçler ve PII'nin otomatik kaldırılması |
| **Güvenlik Başlıkları** | Tüm yanıtlarda CSP, HSTS, X-Frame-Options |
| **Hız Sınırlama** | slowapi tabanlı API hız sınırlama |
| **Denetim Günlüğü** | Tüm kritik işlemler kaydedilir (tasarımdan itibaren yerleşik, sonradan eklenmedi) |

Zafiyet bildirimi için [SECURITY.md](../../SECURITY.md) belgesine bakın.

---

## 🖥️ CLI Referansı

```bash
zero-employee serve              # API sunucusunu başlat
zero-employee serve --port 8000  # Özel bağlantı noktası
zero-employee serve --reload     # Canlı yeniden yükleme

zero-employee chat               # Sohbet modu (tüm sağlayıcılar)
zero-employee chat --mode free   # Ücretsiz mod (Ollama / g4f)
zero-employee chat --lang en     # Dil seçimi

zero-employee local              # Yerel sohbet (Ollama)
zero-employee local --model qwen3:8b --lang en

zero-employee models             # Yüklü modelleri listele
zero-employee pull qwen3:8b      # Model indir

zero-employee config list        # Tüm ayarları göster
zero-employee config set <KEY>   # Değer ayarla
zero-employee config get <KEY>   # Değer al

zero-employee db upgrade         # VT geçişlerini çalıştır
zero-employee health             # Sağlık kontrolü
zero-employee security status    # Güvenlik durumu
zero-employee update             # En son sürüme güncelle
```

---

## 🤖 Desteklenen LLM Modelleri

`model_catalog.json` ile yönetilir — kod değişikliği olmadan model değiştirin.

| Mod | Açıklama | Örnekler |
|-----|----------|----------|
| **Quality** | En yüksek kalite | Claude Opus, GPT-5.4, Gemini 2.5 Pro |
| **Speed** | Hızlı yanıt | Claude Haiku, GPT-5 Mini, Gemini 2.5 Flash |
| **Cost** | Düşük maliyet | Haiku, Mini, Flash Lite, DeepSeek |
| **Free** | Ücretsiz | Gemini ücretsiz katman, Ollama yerel |
| **Subscription** | API anahtarı gerekmez | g4f aracılığıyla |

Görev başına sağlayıcı geçersiz kılma desteklenir — her görev için sağlayıcı, model ve yürütme modunu belirleyin.

---

## 🧩 Skill / Plugin / Extension

### 3 Katmanlı Genişletilebilirlik

| Tür | Açıklama | Örnekler |
|-----|----------|----------|
| **Skill** | Tek amaçlı uzmanlaşmış işleme | spec-writer, review-assistant, browser-assist |
| **Plugin** | Birden fazla Skill'i paketler | ai-secretary, ai-self-improvement, youtube |
| **Extension** | Sistem entegrasyonu ve altyapı | mcp, oauth, notifications, browser-assist |

### Doğal Dille Beceri Oluşturun

```bash
POST /api/v1/registry/skills/generate
{
  "description": "Uzun belgeleri 3 ana noktaya özetleyen bir beceri"
}
```

16 tehlikeli desen otomatik tespit edilir. Yalnızca güvenlik kontrollerini geçen beceriler kaydedilir.

---

## 🌐 Tarayıcı Asistanı

Chrome uzantısı overlay sohbet — Yapay zeka ekranınızı gerçek zamanlı görür ve size rehberlik eder.

- **Overlay Sohbet**: Herhangi bir web sitesinde doğrudan sohbet arayüzü
- **Gerçek Zamanlı Ekran Paylaşımı**: Manuel ekran görüntüsü olmadan yapay zeka ekranınızı görür
- **Hata Teşhisi**: Yapay zeka ekrandaki hata mesajlarını okur ve düzeltme önerir
- **Form Yardımı**: Alan alan adım adım rehberlik
- **Gizlilik Öncelikli**: Ekran görüntüleri geçici olarak işlenir, PII otomatik maskelenir, şifre alanları bulanıklaştırılır

### Kurulum

```
1. Chrome'da extensions/browser-assist/chrome-extension/ yükleyin
   → chrome://extensions → Geliştirici modu → "Paketlenmemiş uzantı yükle"
2. Herhangi bir web sitesinde sohbet simgesine tıklayın
3. Metin ile soru sorun veya ekran görüntüsü düğmesiyle ekranınızı yapay zekaya paylaşın
```

---

## 🛠️ Teknoloji Yığını

### Arka Uç
- Python 3.12+ / FastAPI / uvicorn
- SQLAlchemy 2.x (async) + Alembic
- SQLite (geliştirme) / PostgreSQL (üretim)
- LiteLLM Router SDK
- bcrypt / Fernet şifreleme
- slowapi hız sınırlama

### Ön Uç
- React 19 + TypeScript + Vite
- shadcn/ui + Tailwind CSS
- TanStack Query + Zustand

### Masaüstü
- Tauri v2 (Rust) + Python yan araç

### Dağıtım
- Docker + docker-compose
- Cloudflare Workers (sunucusuz)

---

## ❓ SSS

<details>
<summary><b>Başlamak için API anahtarlarına ihtiyacım var mı?</b></summary>

Hayır. Abonelik modunu (anahtar gerekmez) veya Ollama'yı (tamamen çevrimdışı yerel yapay zeka) kullanabilirsiniz. Yukarıdaki Hızlı Başlangıç bölümüne bakın.
</details>

<details>
<summary><b>Maliyeti ne kadar?</b></summary>

ZEO'nun kendisi ücretsizdir. LLM API maliyetleri her sağlayıcıya (OpenAI, Anthropic, Google vb.) doğrudan tarafınızdan ödenir. Ollama yerel modelleriyle tamamen ücretsiz de çalıştırabilirsiniz.
</details>

<details>
<summary><b>Birden fazla LLM sağlayıcısını aynı anda kullanabilir miyim?</b></summary>

Evet. ZEO görev başına sağlayıcı geçersiz kılmayı destekler — aynı iş akışında yüksek kaliteli spec incelemeleri için Claude'u, hızlı görev yürütme için GPT'yi kullanabilirsiniz.
</details>

<details>
<summary><b>Verilerim güvende mi?</b></summary>

ZEO kendi sunucunuzda barındırma için tasarlanmıştır. Verileriniz kendi altyapınızda kalır. Dosya sandbox'ı varsayılan olarak STRICT, veri aktarımı varsayılan olarak LOCKDOWN ve PII otomatik tespiti varsayılan olarak etkindir.
</details>

<details>
<summary><b>AutoGen / CrewAI / LangGraph'tan farkı ne?</b></summary>

ZEO bir **iş akışı platformudur**, geliştirici çerçevesi değil. İnsan onay kapıları, denetim günlüğü, 3 katmanlı genişletilebilirlik sistemi, tarayıcı asistanı, medya oluşturma ve eksiksiz bir REST API sağlar — tümü yapay zekayı bir organizasyon olarak çalıştırmak için tasarlanmıştır, sadece promptları zincirlemek için değil.
</details>

---

## 🧪 Geliştirme

```bash
# Kurulum
git clone https://github.com/OrosiTororo/Zero-Employee-Orchestrator.git
cd Zero-Employee-Orchestrator
pip install -e ".[dev]"

# Başlat (canlı yeniden yükleme)
zero-employee serve --reload

# Test
pytest apps/api/app/tests/

# Lint
ruff check apps/api/app/
ruff format apps/api/app/
```

---

## 🤝 Katkıda Bulunma

Katkılarınızı bekliyoruz.

1. Fork → Branch → PR (standart akış)
2. Güvenlik sorunları: özel bildirim için [SECURITY.md](../../SECURITY.md) belgesini takip edin
3. Kodlama standartları: ruff biçimlendirme, tür ipuçları zorunlu, async def

---

## 💜 Sponsorlar

Bu proje ücretsiz ve açık kaynaklıdır. Sponsorluk projenin sürdürülmesine ve büyümesine yardımcı olur.

[**Sponsor Olun**](https://github.com/sponsors/OrosiTororo)

---

## 🌟 Yıldız Geçmişi

[![Star History Chart](https://api.star-history.com/svg?repos=OrosiTororo/Zero-Employee-Orchestrator&type=Date)](https://star-history.com/#OrosiTororo/Zero-Employee-Orchestrator&Date)

---

## 📄 Lisans

MIT — Özgürce kullanın, gerektiği gibi değiştirin, yapabiliyorsanız katkıda bulunun.

---

<p align="center">
  <strong>Zero-Employee Orchestrator</strong> — Yapay zekayı bir organizasyon olarak çalıştırın.<br>
  Güvenlik, denetlenebilirlik ve insan gözetimi düşünülerek oluşturulmuştur.
</p>
