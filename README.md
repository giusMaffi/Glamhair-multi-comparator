# 💇 Glamhairshop AI Assistant

**Assistente conversazionale intelligente per e-commerce prodotti professionali per capelli**

Basato sull'architettura RAG (Retrieval-Augmented Generation) con Claude Sonnet 4, progettato per guidare utenti alla scelta del prodotto perfetto attraverso conversazione consultiva.

---

## 🎯 Funzionalità

- **🧠 Conversazione consultiva AI-powered**: Domande mirate per capire esigenze utente
- **🔍 Semantic Search**: Ricerca semantica multilingue su catalogo completo
- **🎭 Doppia personalità**: 
  - **Hair Care** (B2C): Tono consultivo, focus su benessere capelli
  - **Parrucchiere** (B2B): Tono tecnico, focus su prestazioni/specifiche
- **🛡️ Anti-hallucination**: Misure aggressive per evitare prodotti inventati
- **🌍 Multilingua**: IT, EN, DE, FR, ES
- **📊 Comparatore intelligente**: Confronti dettagliati tra prodotti
- **📱 Widget embeddabile**: Integrabile su sito cliente

---

## 🏗️ Architettura

```
User Query
    ↓
Category Detection (haircare vs parrucchiere)
    ↓
Requirements Extraction (tipo capelli, problema, budget, ecc.)
    ↓
RAG Retrieval (semantic search + reranking)
    ↓
Claude Sonnet 4 (conversation + product selection)
    ↓
Response (conversational + product cards)
```

### Stack Tecnologico

- **Backend**: Python 3.9+, Flask 3.0
- **AI/LLM**: Anthropic Claude Sonnet 4
- **Embeddings**: Sentence Transformers (paraphrase-multilingual-mpnet-base-v2)
- **Vector Storage**: Pickle (MVP) → Qdrant/Pinecone (production)
- **Frontend**: Vanilla HTML/CSS/JS
- **Deployment**: Railway (MVP) / Docker (production)

---

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Anthropic API Key
- Git

### Installation

```bash
# Clone repository
git clone https://github.com/your-org/glamhairshop-assistant.git
cd glamhairshop-assistant

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup environment variables
cp .env.example .env
# Edit .env with your ANTHROPIC_API_KEY
```

## 🤖 Embedding Models

Il sistema utilizza `sentence-transformers` per generare embeddings semantici dei prodotti.

### Primo Avvio

Al primo avvio, il modello embedding (~1GB) viene scaricato automaticamente da Hugging Face:
- **Modello:** `sentence-transformers/all-MiniLM-L6-v2`
- **Dimensione:** ~1GB
- **Location:** `models/embedding_model/`

> **Nota:** La directory `models/` è esclusa da Git. Il download è automatico.

### Rigenerare Models

Se la directory `models/` viene cancellata:
```bash
# I modelli si rigenerano automaticamente
rm -rf models/
python src/rag/embeddings.py  # Re-download automatico
```

### Cache FAISS Indexes

Gli indici FAISS vengono salvati in `data/products/docs/` e sono esclusi da Git:
- **Dimensione:** ~40KB
- **Rigenerazione:** Automatica se mancanti

### Generate Embeddings

```bash
# Generate embeddings for product catalog
python scripts/generate_embeddings.py
```

### Run Locally

```bash
# Start Flask app
python app/app.py

# Open browser
# → http://localhost:5000
```

---

## 📁 Project Structure

See `docs/ARCHITECTURE.md` for detailed architecture documentation.

```
glamhairshop-assistant/
├── app/              # Flask web application
├── src/              # Core RAG + AI logic
├── data/             # Product catalog + embeddings
├── scripts/          # Utility scripts (scraping, embeddings)
├── tests/            # Test suite
└── docs/             # Documentation
```

---

## 🧪 Testing

```bash
# Run all tests
pytest

# Test RAG system
python scripts/test_rag.py

# Test specific component
pytest tests/test_matchers.py -v
```

---

## 🎨 Categories

### 1. Hair Care (B2C Consumer)
- Shampoo, Balsami, Maschere
- Trattamenti, Styling, Oli
- **Brands**: Kerastase, Olaplex, Davines, Aveda, Redken, etc.

### 2. Parrucchiere (B2B Professional)
- **Attrezzature**: Piastre, Phon, Ferri, Spazzole
- **Colorazione**: Tinte (155+ nuance), Ossidanti, Decoloranti
- **Trattamenti**: Permanenti, Stiranti

---

## 🔧 Configuration

Key configuration in `src/config.py`:

```python
# Claude API
ANTHROPIC_API_KEY = "your-key"
MODEL_NAME = "claude-sonnet-4-20250514"
MODEL_TEMPERATURE = 0.7
MAX_TOKENS = 2000

# RAG
EMBEDDING_MODEL = "paraphrase-multilingual-mpnet-base-v2"
TOP_K_PRODUCTS = 20

# Categories
CATEGORIES = ["haircare", "parrucchiere"]
```

---

## 📊 Analytics

Built-in tracking with Umami Analytics (GDPR-compliant):

- Session metrics (duration, messages)
- Product views & clicks
- Conversion tracking
- Language preferences

---

## 🚢 Deployment

### Railway (Recommended for MVP)

```bash
# Connect GitHub repo to Railway
# Auto-deploy on push to main

# Environment variables in Railway dashboard:
ANTHROPIC_API_KEY=sk-ant-...
FLASK_ENV=production
```

### Docker

```bash
# Build image
docker build -t glamhairshop-assistant .

# Run container
docker run -p 8000:8000 \
  -e ANTHROPIC_API_KEY=your-key \
  glamhairshop-assistant
```

See `docs/DEPLOYMENT.md` for detailed deployment guide.

---

## 📖 Documentation

- [Architecture](docs/ARCHITECTURE.md) - System architecture deep dive
- [API Reference](docs/API.md) - API endpoints documentation
- [Deployment Guide](docs/DEPLOYMENT.md) - Production deployment
- [Contributing](docs/CONTRIBUTING.md) - How to contribute

---

## 🔐 Security

- API keys stored in `.env` (never committed)
- CORS configured for specific domains
- Rate limiting on API endpoints
- Input validation & sanitization
- GDPR-compliant analytics

---

## 🗺️ Roadmap

### Phase 1 (MVP - 4 weeks)
- [x] Project setup
- [ ] RAG system (haircare + parrucchiere)
- [ ] Basic Flask API
- [ ] Simple frontend
- [ ] Deploy to Railway

### Phase 2 (Production - 8 weeks)
- [ ] Advanced category routing
- [ ] Multi-brand support (30+ brands)
- [ ] Comparator feature
- [ ] Widget embeddable
- [ ] Analytics dashboard

### Phase 3 (Scale)
- [ ] Vector DB (Qdrant)
- [ ] Redis sessions
- [ ] Multi-language full support
- [ ] Mobile app integration
- [ ] A/B testing framework

---

## 🤝 Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](docs/CONTRIBUTING.md) first.

---

## 📝 License

Proprietary - All rights reserved

---

## 📧 Contact

- **Project Lead**: [Your Name]
- **Email**: support@glamhairshop.it
- **Website**: https://www.glamhairshop.it

---

## 🙏 Acknowledgments

Based on the STIGA Product Assistant architecture blueprint.
Built with Anthropic Claude, Sentence Transformers, and Flask.
