# Changelog

> [English](../CHANGELOG.md) | [日本語](../ja-JP/CHANGELOG.md) | [中文](../zh/CHANGELOG.md) | [한국어](../ko-KR/CHANGELOG.md) | [Português](../pt-BR/CHANGELOG.md) | Türkçe

Bu projedeki tüm önemli değişiklikler bu dosyada belgelenecektir.

Format: [Keep a Changelog](https://keepachangelog.com/)
Sürümleme: [Semantic Versioning](https://semver.org/)

## [0.1.1] - 2026-03-28

### Eklenen

- **Üretim ortamı Docker Compose** — Kaynak limitleri (bellek/CPU), ağ izolasyonu, log rotasyonu, salt okunur dosya sistemi, `no-new-privileges` güvenlik seçeneği, healthcheck `start_period`
- **CI'da Trivy konteyner imaj taraması** — Birleştirme öncesi Docker imajlarını CRITICAL/HIGH güvenlik açıkları için tarayan yeni CI işi
- **CI'da Red-team güvenlik testleri** — Tam Red-team test paketini çalıştıran ve kritik bulgularda derlemeyi başarısız kılan yeni CI işi
- **65+ i18n çeviri anahtarı** — 6 dilde ~30'dan 65+'a genişletildi. Güvenlik mesajları, ayarlar, gezinme, ortak eylemler, beceri/eklenti yönetimi, sunucu sağlığı, bütçe/maliyet, Judge Layer ve Browser Assist dahil
- **Eksik PII algılama desenleri** — Ehliyet (Japonya/ABD) ve Japonca tam isim desenleri eklenerek tüm 13 PII kategorisi tamamlandı
- **6 dil i18n desteği** — Mevcut Japonca, İngilizce ve Çince'ye ek olarak Korece (한국어), Portekizce (Português) ve Türkçe çevirileri eklendi
- **Genişletilebilir LLM API anahtar ayarları** — Yerleşik 4 sağlayıcının ötesinde özel sağlayıcılar eklenebilir
- **Design Interview geçmiş başarısızlık deseni geri bildirimi** — Experience Memory ve Failure Taxonomy'den benzer başarısızlık desenleri otomatik aranır

### Değişen

- **Varsayılan dil İngilizce olarak değiştirildi** — Daha geniş uluslararası benimseme için `ja`'dan `en`'e değiştirildi (kullanıcılar `LANGUAGE=ja` veya `--lang ja` ile değiştirebilir)
- **Model kataloğu güncellendi** — GPT-5.4 / GPT-5.4 Mini (4.1'den), Llama 4 (3.2'den), Phi-4 (3'ten), Claude Haiku tarihsiz takma ad
- **Dokümantasyon doğruluk düzeltmeleri** — Şişirilmiş metrikler düzeltildi: prompt guard desenleri 40+→28+, uygulama bağlayıcıları 35+→34+, rota modülleri 41→40. Tüm dillerde "GPT-5 Mini"→"GPT-5.4 Mini" düzeltildi
- **VSCode tarzı tek aktivite çubuğu gezinmesi** — Çift kenar çubuğu kaldırıldı, ipuçlu simge tabanlı aktivite çubuğuna geçildi

### Güvenlik

- **CI'da pip-audit artık engelleyici** — `continue-on-error` kaldırıldı; bağımlılık güvenlik açıkları derlemeyi başarısız kılar
- **Red-team testleri güçlendirildi** — Test işleyicileri artık gerçek yüklerle güvenlik modüllerini çalıştırır
- **Sandbox sembolik bağlantı saldırı koruması güçlendirildi** — Çözümlenen yol orijinalden farklı bir dizine işaret ettiğinde algılar ve engeller

## [0.1.0] - 2026-03-12 — Platform v0.1 (Konsolide Sürüm)

İlk uygulama. Tam ayrıntılar için [İngilizce CHANGELOG](../CHANGELOG.md)'a bakın.

[0.1.1]: https://github.com/OrosiTororo/Zero-Employee-Orchestrator/releases/tag/v0.1.1
[0.1.0]: https://github.com/OrosiTororo/Zero-Employee-Orchestrator/releases/tag/v0.1.0
