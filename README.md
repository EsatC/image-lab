# 🖼️ ImageLab — Cloud-Based Image Processing Platform

12 faktör prensiplerine uygun, bulut tabanlı görüntü işleme platformu.

## ✨ Özellikler

- **Görüntü Yükleme** — Drag & drop veya dosya seçme ile çoklu yükleme
- **Görüntü İşleme** — Histogram eşitleme, gürültü azaltma, bulanıklaştırma, keskinleştirme, kenar tespiti, gri tonlama, sepya, renk ters çevirme
- **Format Dönüşümü** — PNG, JPG, WebP, BMP, TIFF arası dönüşüm
- **Güvenli Erişim** — JWT tabanlı kimlik doğrulama
- **Modern UI** — Dark mode, glassmorphism, responsive tasarım

## 🛠️ Teknoloji Yığını

| Katman | Teknoloji |
|---|---|
| Backend | Python / Flask |
| Frontend | React (Vite) |
| Veritabanı | SQLite |
| Dağıtım | Docker + Docker Compose |
| CI/CD | GitHub Actions |
| Sunucu | Oracle Cloud (1 OCPU, 1 GB RAM) |

## 🚀 Hızlı Başlangıç

### 1. Depoyu klonlayın
```bash
git clone https://github.com/<your-username>/image-lab.git
cd image-lab
```

### 2. Ortam değişkenlerini ayarlayın
```bash
cp .env.example .env
# .env dosyasını düzenleyin
```

### 3. Docker ile çalıştırın
```bash
docker compose up --build
```

Uygulama `http://localhost` adresinde hazır olacaktır.

### Geliştirme Ortamı (Docker olmadan)

**Backend:**
```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
flask run --debug
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## 📁 Proje Yapısı

```
image-lab/
├── backend/
│   ├── app/
│   │   ├── routes/          # API endpoint'leri
│   │   ├── services/        # İş mantığı (görüntü işleme)
│   │   └── models.py        # Veritabanı modelleri
│   ├── config.py            # Konfigürasyon
│   ├── wsgi.py              # Gunicorn entrypoint
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── pages/           # Sayfa bileşenleri
│   │   ├── components/      # Paylaşılan bileşenler
│   │   ├── context/         # React Context (Auth)
│   │   └── api/             # API istemcisi
│   ├── nginx.conf
│   └── Dockerfile
├── docker-compose.yml
├── .github/workflows/       # CI/CD
└── .env.example
```

## 🔌 API Endpoints

| Method | Endpoint | Açıklama |
|---|---|---|
| POST | `/api/auth/register` | Kullanıcı kaydı |
| POST | `/api/auth/login` | Giriş (JWT token) |
| GET | `/api/auth/me` | Mevcut kullanıcı |
| POST | `/api/images/upload` | Görüntü yükleme |
| GET | `/api/images` | Görüntüleri listele |
| GET | `/api/images/:id` | Görüntü detayı / indirme |
| DELETE | `/api/images/:id` | Görüntü silme |
| POST | `/api/images/:id/process` | Görüntü işleme |
| POST | `/api/images/:id/convert` | Format dönüşümü |

## 📜 Lisans

MIT
