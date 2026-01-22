# 🔍 DIAGNOSTIC REPORT - Glamhair Multi Comparator
**Data:** 22 Gennaio 2026, 14:00
**Status:** Context rotto (P1), Comportamento da fixare (P2)

---

## ✅ COSA FUNZIONA

- Flask su porta 5001 ✅
- RAG embeddings v2.1 (scores 0.77-0.81) ✅  
- Catalogo completo (2619 prodotti) ✅
- FAISS index corretto ✅
- UI base funzionante ✅

---

## ❌ PROBLEMI DA FIXARE

### P1 - CONTEXT NON MANTENUTO (CRITICAL) 🔴

**Sintomo:**
- Ogni messaggio riparte da zero
- Log mostra "Formatted 1 messages" sempre (dovrebbe essere 2, 3, 4...)
- Query "fammi vedere cosa hai" → Claude non sa di cosa parli

**Root Cause:**
- `app/routes/api.py` linea ~95-100
- Logica `conversation_history[:-1]` svuota storia su primo messaggio
- Manca context-aware query enrichment per query corte

**Fix Necessario:**
1. Correggere logica conversation_history (non svuotare su primo msg)
2. Aggiungere enriched query per query corte (<=5 parole)
3. Combinare ultimo messaggio utente con query corrente

**Impact:** BLOCKER - Senza context il sistema è inutilizzabile

---

### P2 - COMPORTAMENTO RISPOSTA SBAGLIATO (HIGH) 🟠

**Sintomo:**
- Query "hai shampoo wella?" → Fa anamnesi PRIMA di mostrare prodotti
- Dice "diversi shampoo" ma ne mostra solo 1
- Non mostra TUTTI i prodotti trovati dal RAG

**Comportamento Atteso:**
```
Query BRAND (es. "hai shampoo wella?")
→ Mostra TUTTI i 10 shampoo Wella trovati
→ POI chiede: "Quale ti interessa? Dimmi il tuo problema"

Query PROBLEMA (es. "capelli secchi")  
→ Breve consulenza (2-3 domande)
→ POI mostra top 5-10 prodotti
```

**Root Cause:**
- `src/api/prompts/base_prompt.py` dice a Claude di fare sempre anamnesi
- Nessuna differenziazione tra query BRAND vs query PROBLEMA

**Fix Necessario:**
- Riscrivere prompt con regole chiare
- SE query contiene brand → mostra prodotti SUBITO
- SE query descrive problema → consulenza PRIMA

---

### P3 - PRODOTTI INCOMPLETI (MEDIUM) 🟡

**Sintomo:**
- RAG trova 10 shampoo Wella (verificato con test)
- Claude ne mostra solo 1-2 nella risposta
- Cliente non vede catalogo completo

**Root Cause:**
- top_k=20 potrebbe essere basso per alcune categorie
- Claude seleziona arbitrariamente quali menzionare
- Prompt non dice "elenca TUTTI"

**Fix Necessario:**
- Aumentare top_k per query brand-specific
- Prompt: "Se trovi 5+ prodotti stesso brand, elenca TUTTI"

---

## 🎯 PROSSIMO STEP

### FIX P1: app/routes/api.py (ORA)

**Modifiche necessarie linea ~95-100:**

```python
# PRIMA (ROTTO):
conversation_history = current_app.session_manager.get_conversation_history(session_id)
if conversation_history and len(conversation_history) > 0:
    conversation_history = conversation_history[:-1]  # ← SVUOTA su primo msg!

# DOPO (FIXATO):
conversation_history = current_app.session_manager.get_conversation_history(session_id)
# Rimuovi ultimo solo se storia ha >1 messaggio
if len(conversation_history) > 1:
    conversation_history = conversation_history[:-1]
else:
    conversation_history = []

# AGGIUNGI: Context-aware retrieval
if len(user_message.split()) <= 5 and conversation_history:
    last_user_msgs = [m for m in conversation_history if m['role'] == 'user']
    if last_user_msgs:
        enriched_query = f"{last_user_msgs[-1]['content']} {user_message}"
    else:
        enriched_query = user_message
else:
    enriched_query = user_message

# USA enriched_query per retrieval
products = retriever.search(
    query=enriched_query,  # ← Non user_message
    top_k=20,
    min_similarity=0.3
)
```

---

## 📊 PRIORITÀ

1. **P1** (BLOCKER) → Fix context → 15 minuti
2. **P2** (HIGH) → Fix comportamento → 30 minuti  
3. **P3** (MEDIUM) → Ottimizzazioni → 15 minuti

**TOTALE: 1 ora per sistema funzionante**

---

**READY FOR EXECUTION**
