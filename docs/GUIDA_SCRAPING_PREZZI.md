# 🚀 GLAMHAIR PDP SCRAPING - GUIDA OPERATIVA
## Versione Corretta con Estrazione Prezzi

**Data:** 2026-01-20  
**Autore:** Peppe  
**Versione:** 2.0 (con Price Extraction)

---

## 📋 COSA È CAMBIATO

### ❌ Script Vecchio (bloccato)
- ✅ Estraeva: descrizione, ingredienti, modo uso, tecnologie
- ❌ **NON estraeva: prezzi**

### ✅ Script Nuovo (corretto)
- ✅ Estrae: descrizione, ingredienti, modo uso, tecnologie
- ✅ **ESTRAE: regular_price, promo_price, discount_percent**

---

## 🎯 WORKFLOW OPERATIVO

### FASE 1: TEST PRE-SCRAPING (OBBLIGATORIO)

Prima di lanciare lo scraping completo, **SEMPRE testare su 3 prodotti campione.**

```bash
# 1. Vai nella directory del progetto
cd ~/Projects/Glamhair-multi-comparator

# 2. Assicurati che il venv sia attivo
source venv/bin/activate

# 3. Crea la directory scripts/scraping se non esiste
mkdir -p scripts/scraping

# 4. Copia il file di test
# SCARICA test_pdp_extraction_with_prices.py da Claude
# e salvalo in: scripts/scraping/test_pdp_extraction_with_prices.py

# 5. Lancia il test
python scripts/scraping/test_pdp_extraction_with_prices.py
```

#### 📊 OUTPUT ATTESO DEL TEST

Dovresti vedere per ogni prodotto:

```
📊 EXTRACTED DATA:

1️⃣  DESCRIZIONE COMPLETA:
   Length: 937 chars
   Preview: Kerastase Chronologiste Bain Règènerant è uno shampoo...

2️⃣  INGREDIENTI:
   attivi, il bain règènerant sublima tutti i tipi di capelli...

3️⃣  MODO D'USO:
   applicare una piccola quantità di bain règènerant...

4️⃣  TECNOLOGIE:
   Abissina, Acido Ialuronico, Vitamina E

5️⃣  💰 PREZZI (NEW!):
   Regular Price: €36.00
   Promo Price: €25.20
   Discount: 30%
   You Save: €10.80
```

#### ✅ CRITERI DI SUCCESSO DEL TEST

Il test è PASSATO se:
- [ ] Tutti e 3 i prodotti hanno descrizione completa
- [ ] Almeno 2/3 hanno ingredienti e modo d'uso
- [ ] Almeno 2/3 hanno tecnologie estratte
- [ ] **TUTTI e 3 hanno regular_price** ← CRITICAL
- [ ] Almeno 2/3 hanno promo_price (se in promo)

#### ❌ SE IL TEST FALLISCE

```bash
# Verifica che Chrome/ChromeDriver sia installato
chromedriver --version

# Se manca, installa:
brew install chromedriver  # macOS
# oppure scarica da: https://chromedriver.chromium.org/

# Rilancia il test
python scripts/scraping/test_pdp_extraction_with_prices.py
```

---

### FASE 2: BACKUP PRE-SCRAPING

```bash
# Crea backup di sicurezza
cd ~/Projects/Glamhair-multi-comparator/data/products/

# Backup manuale aggiuntivo (oltre a quello automatico)
cp ALL_PRODUCTS.json ALL_PRODUCTS_MANUAL_BACKUP_$(date +%Y%m%d_%H%M%S).json

# Verifica backup creato
ls -lh ALL_PRODUCTS*
```

---

### FASE 3: DEPLOYMENT SCRIPT PRINCIPALE

```bash
# 1. Copia lo script corretto
# SCARICA scrape_pdp_with_prices.py da Claude
# e salvalo in: scripts/scraping/scrape_pdp.py
# (SOVRASCRIVENDO il vecchio file!)

# 2. Verifica che il file sia corretto
grep "PRICES" scripts/scraping/scrape_pdp.py

# Dovresti vedere:
# "PDP (Product Detail Page) Scraper - WITH PRICE EXTRACTION"
# "# ⭐ PRICES - NEW!"

# 3. Verifica che il file di input esista
ls -lh data/products/ALL_PRODUCTS.json
```

---

### FASE 4: LANCIO SCRAPING COMPLETO

```bash
# ⚠️ ATTENZIONE: Questo processo richiederà TEMPO
# Con ~600 prodotti e delay di 2 secondi: circa 40-60 minuti

# 1. Avvia lo scraping
python scripts/scraping/scrape_pdp.py

# 2. Monitora l'output
# Dovresti vedere per ogni prodotto:
# 📦 Product 1/600 (0.2%) - ETA: 45min
#    Brand - Product Name...
#    URL: https://...
#    ✅ Enriched successfully
#       Ingredienti: ...
#       Tecnologie: ...
#       💰 Regular: €36.00
#       🎁 Promo: €25.20 (-30%)

# 3. Ogni 50 prodotti vedrai un checkpoint:
# ======================================================================
# 📊 PROGRESS CHECKPOINT:
#    Processed: 50/600 (8.3%)
#    Enriched: 48
#    Errors: 2
#    Success rate: 96.0%
# ======================================================================
```

#### 🚨 SE LO SCRAPING SI BLOCCA

```bash
# 1. CTRL+C per interrompere
# 2. Controlla quanto ha fatto
cd data/products/
ls -lh ALL_PRODUCTS_ENRICHED.json

# 3. Se ha fatto pochi prodotti (<50), rilancia
python scripts/scraping/scrape_pdp.py

# 4. Se ha fatto molti prodotti (>100), contattami per recovery
```

---

### FASE 5: VERIFICA POST-SCRAPING

```bash
cd ~/Projects/Glamhair-multi-comparator/data/products/

# 1. Verifica file creato
ls -lh ALL_PRODUCTS_ENRICHED.json

# Dimensione attesa: ~2-3 MB (più grande del file originale)

# 2. Conta prodotti totali
python3 -c "import json; data=json.load(open('ALL_PRODUCTS_ENRICHED.json')); print(f'Total products: {len(data)}')"

# 3. Conta prodotti arricchiti con successo
python3 -c "import json; data=json.load(open('ALL_PRODUCTS_ENRICHED.json')); enriched=[p for p in data if p.get('pdp_scraped')]; print(f'Enriched: {len(enriched)}/{len(data)} ({len(enriched)/len(data)*100:.1f}%)')"

# 4. Conta prodotti con prezzi
python3 -c "import json; data=json.load(open('ALL_PRODUCTS_ENRICHED.json')); with_price=[p for p in data if p.get('regular_price')]; print(f'With prices: {len(with_price)}/{len(data)} ({len(with_price)/len(data)*100:.1f}%)')"

# 5. Mostra esempio prodotto arricchito
python3 -c "import json; data=json.load(open('ALL_PRODUCTS_ENRICHED.json')); print(json.dumps([p for p in data if p.get('regular_price')][0], indent=2, ensure_ascii=False))" | head -50
```

#### ✅ CRITERI DI SUCCESSO FINALE

Lo scraping è completato CON SUCCESSO se:
- [ ] Success rate > 85% (errori < 15%)
- [ ] Almeno 90% dei prodotti ha regular_price
- [ ] File ALL_PRODUCTS_ENRICHED.json esiste
- [ ] File size ~2-3x del file originale

---

### FASE 6: GIT COMMIT

```bash
# Solo DOPO aver verificato che tutto è OK

cd ~/Projects/Glamhair-multi-comparator

# 1. Verifica status
git status

# 2. Aggiungi i file modificati
git add scripts/scraping/scrape_pdp.py
git add scripts/scraping/test_pdp_extraction_with_prices.py
git add data/products/ALL_PRODUCTS_ENRICHED.json
git add data/products/ALL_PRODUCTS_BEFORE_PDP.json

# 3. Commit
git commit -m "feat: add price extraction to PDP scraper

- Integrate PriceExtractor class for regular/promo prices
- Extract regular_price, promo_price, discount_percent
- Add comprehensive test script
- Successfully scraped ~600 products with price data
- Success rate: XX% (update with actual rate)"

# 4. Push
git push origin main

# 5. Verifica su GitHub
open https://github.com/giusMaffi/Glamhair-multi-comparator
```

---

## 🔧 TROUBLESHOOTING

### Problema: "ChromeDriver not found"

```bash
# macOS
brew install chromedriver

# Verifica
chromedriver --version
```

### Problema: "No such file: ALL_PRODUCTS.json"

```bash
# Verifica path
pwd
# Deve essere: /Users/giuseppemaffione/Projects/Glamhair-multi-comparator

cd ~/Projects/Glamhair-multi-comparator
python scripts/scraping/scrape_pdp.py
```

### Problema: "Regular price not found" nel test

```bash
# Controlla che il sito sia raggiungibile
curl -I https://www.glamhairshop.it/

# Prova con delay maggiore
# Modifica DELAY_BETWEEN_REQUESTS = 3 nello script
```

---

## 📊 STIMA TEMPI

| Fase | Durata | Note |
|------|--------|------|
| Test 3 prodotti | 1-2 min | Obbligatorio |
| Backup | 10 sec | Automatico + manuale |
| Scraping 600 prodotti | 40-60 min | Dipende da connessione |
| Verifica | 2-3 min | Controlli qualità |
| Git commit | 1 min | Documentazione |
| **TOTALE** | **~50-70 min** | |

---

## ✅ CHECKLIST FINALE

Prima di procedere:
- [ ] Script di test copiato e funzionante
- [ ] Test passato con successo (3/3 prodotti con prezzi)
- [ ] Backup manuale creato
- [ ] Script principale copiato
- [ ] Chrome/ChromeDriver installato
- [ ] Tempo disponibile (~1 ora)

Durante lo scraping:
- [ ] Monitor output ogni 50 prodotti
- [ ] Success rate > 85%
- [ ] Prezzi estratti correttamente

Dopo lo scraping:
- [ ] File ENRICHED creato
- [ ] Verifica conteggi OK
- [ ] Esempio prodotto contiene prezzi
- [ ] Git commit effettuato

---

## 🚨 NUMERO DI EMERGENZA

Se qualcosa va storto, **NON ANDARE AVANTI**.

Condividi con Claude:
1. Output dell'errore completo
2. Ultimo checkpoint mostrato
3. Output del comando: `ls -lh data/products/`

---

## 🎯 PROSSIMI STEP (POST-SCRAPING)

Una volta completato lo scraping:
1. ✅ Dataset arricchito con prezzi
2. 🔄 Generazione embeddings (prossima chat)
3. 🤖 RAG system con filtro prezzo funzionante
4. 🚀 Deploy del chatbot

---

**Good luck! 🚀**

*Ricorda: TEST FIRST, SCRAPE LATER*
