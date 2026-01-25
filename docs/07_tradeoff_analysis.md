# 07. Trade-off Analysis - Phân Tích Đánh Đổi

> **Document Version**: 1.0
> **Last Updated**: 2026-01-23
> **Status**: Approved
> **Related Documents**: [06_solution_proposals.md](./06_solution_proposals.md), [08_optimal_solution.md](./08_optimal_solution.md)

---

## 1. Executive Summary

Tài liệu này phân tích chi tiết các trade-offs giữa 4 phương án đề xuất, giúp đưa ra quyết định có căn cứ cho việc chọn giải pháp tối ưu.

---

## 2. Trade-off Dimensions

### 2.1 Key Trade-off Axes

```
                    HIGH ACCURACY
                         │
                         │
        Option C ────────┼──────── Option D
        (BERT)           │         (LLM)
                         │
LOW COST ────────────────┼──────────────── HIGH COST
                         │
        Option A ────────┼──────── Option B
        (Rules)          │         (CRF)
                         │
                    LOW ACCURACY
```

### 2.2 Trade-off Matrix

| Dimension | Option A | Option B | Option C | Option D |
|-----------|----------|----------|----------|----------|
| Accuracy ↔ Simplicity | Low/High | Med/Med | High/Low | Med/Med |
| Cost ↔ Performance | Low/Low | Low/Med | Low/High | High/Med |
| Time ↔ Quality | Short/Low | Med/Med | Long/High | Short/Med |
| Data Need ↔ Generalization | None/Poor | Some/Med | More/Good | None/Good |

---

## 3. Detailed Trade-off Analysis

### 3.1 Option A: Rule-Based

#### Trade-off 1: Simplicity vs Accuracy
```
┌─────────────────────────────────────────────────────────────┐
│ SIMPLICITY ────────────────────────────────── ACCURACY      │
│                                                              │
│ ████████████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │
│     HIGH (80%)                           LOW (40-50%)        │
│                                                              │
│ Analysis:                                                    │
│ • Simple to implement (2 weeks)                             │
│ • Easy to understand and debug                              │
│ • BUT: Cannot handle variations                             │
│ • BUT: High maintenance for rules                           │
│                                                              │
│ Trade-off Impact: SEVERE                                     │
│ • Sacrificing too much accuracy for simplicity              │
│ • F1 40-50% không đạt yêu cầu (target: 75%)                 │
└─────────────────────────────────────────────────────────────┘
```

#### Trade-off 2: Development Speed vs Maintainability
```
┌─────────────────────────────────────────────────────────────┐
│ DEV SPEED ─────────────────────────────── MAINTAINABILITY   │
│                                                              │
│ ████████████████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │
│     FAST (2 weeks)                        HARD              │
│                                                              │
│ Analysis:                                                    │
│ • Fast initial development                                  │
│ • BUT: Every new pattern needs new rules                    │
│ • BUT: Rules conflict with each other                       │
│ • BUT: Technical debt accumulates quickly                   │
│                                                              │
│ Trade-off Impact: MODERATE-SEVERE                           │
│ • Short-term gain, long-term pain                           │
└─────────────────────────────────────────────────────────────┘
```

#### Option A Summary
| Gain | Sacrifice | Acceptable? |
|------|-----------|-------------|
| Fast development | Accuracy | ❌ No |
| No training data | Generalization | ❌ No |
| Simple code | Maintainability | ❌ No |

**Verdict**: Trade-offs TOO SEVERE. Not recommended.

---

### 3.2 Option B: CRF + FastText

#### Trade-off 1: Feature Engineering vs Model Complexity
```
┌─────────────────────────────────────────────────────────────┐
│ FEATURE EFFORT ────────────────────────── MODEL COMPLEXITY  │
│                                                              │
│ ████████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │
│     HIGH (manual)                        LOW (CRF)          │
│                                                              │
│ Analysis:                                                    │
│ • Need to design features manually                          │
│ • CRF model itself is simple                                │
│ • Feature quality determines accuracy                       │
│ • Requires domain expertise                                 │
│                                                              │
│ Trade-off Impact: MODERATE                                   │
│ • Feature engineering is time-consuming                     │
│ • But CRF is well-understood and fast                       │
└─────────────────────────────────────────────────────────────┘
```

#### Trade-off 2: Training Data vs Accuracy
```
┌─────────────────────────────────────────────────────────────┐
│ DATA REQUIREMENT ──────────────────────────── ACCURACY      │
│                                                              │
│ ████████░░░░░░░░░░░░░░░░░░░░░░░████████████░░░░░░░░░░░░░░░ │
│   LOW-MED (100+)                   MED (55-65%)             │
│                                                              │
│ Analysis:                                                    │
│ • Less data needed than deep learning                       │
│ • But accuracy ceiling is lower                             │
│ • Cannot learn complex patterns                             │
│ • Features limit what can be learned                        │
│                                                              │
│ Trade-off Impact: MODERATE                                   │
│ • Acceptable data requirement                               │
│ • But accuracy may not meet target (75%)                    │
└─────────────────────────────────────────────────────────────┘
```

#### Trade-off 3: Inference Speed vs Accuracy
```
┌─────────────────────────────────────────────────────────────┐
│ INFERENCE SPEED ───────────────────────────── ACCURACY      │
│                                                              │
│ ████████████████████████░░░░░░░░░░░░░░░░████████████░░░░░░ │
│      FAST (ms)                            MED (55-65%)      │
│                                                              │
│ Analysis:                                                    │
│ • CRF inference is very fast                                │
│ • No GPU needed for inference                               │
│ • But sacrificing accuracy for speed                        │
│ • Speed not critical for our use case                       │
│                                                              │
│ Trade-off Impact: ACCEPTABLE                                 │
│ • Speed advantage not needed                                │
│ • Would prefer higher accuracy                              │
└─────────────────────────────────────────────────────────────┘
```

#### Option B Summary
| Gain | Sacrifice | Acceptable? |
|------|-----------|-------------|
| Less data needed | Max accuracy | ⚠️ Maybe |
| Fast inference | Deep learning power | ⚠️ Maybe |
| Simple model | Feature engineering | ⚠️ Maybe |

**Verdict**: Trade-offs MODERATE. Backup option if BERT fails.

---

### 3.3 Option C: BERT Fine-tuning ⭐

#### Trade-off 1: Accuracy vs Training Complexity
```
┌─────────────────────────────────────────────────────────────┐
│ ACCURACY ──────────────────────────── TRAINING COMPLEXITY   │
│                                                              │
│ ████████████████████████████████░░░░░░░░██████████████░░░░ │
│      HIGH (75-85%)                       MED-HIGH           │
│                                                              │
│ Analysis:                                                    │
│ • Highest expected accuracy                                 │
│ • Transfer learning simplifies training                     │
│ • Need to understand fine-tuning workflow                   │
│ • Hugging Face makes it accessible                          │
│                                                              │
│ Trade-off Impact: ACCEPTABLE                                 │
│ • Complexity is manageable with tutorials                   │
│ • Accuracy gain justifies the effort                        │
└─────────────────────────────────────────────────────────────┘
```

#### Trade-off 2: Performance vs Data Requirement
```
┌─────────────────────────────────────────────────────────────┐
│ PERFORMANCE ────────────────────────── DATA REQUIREMENT     │
│                                                              │
│ ████████████████████████████████░░░░░░░░████████████░░░░░░ │
│      HIGH (75-85%)                       MED (200+ CVs)     │
│                                                              │
│ Analysis:                                                    │
│ • Need 200+ annotated CVs                                   │
│ • We have capacity: 4 annotators × 4 weeks = 200+ CVs      │
│ • Pre-training reduces data need vs training from scratch   │
│ • Data requirement is achievable                            │
│                                                              │
│ Trade-off Impact: ACCEPTABLE                                 │
│ • Data requirement fits our capacity                        │
│ • Performance justifies annotation effort                   │
└─────────────────────────────────────────────────────────────┘
```

#### Trade-off 3: Development Time vs Scientific Value
```
┌─────────────────────────────────────────────────────────────┐
│ DEV TIME ─────────────────────────────── SCIENTIFIC VALUE   │
│                                                              │
│ ████████████████░░░░░░░░░░░░░░░░████████████████████████░░ │
│     MED (6 weeks)                        HIGH               │
│                                                              │
│ Analysis:                                                    │
│ • 6 weeks is longest among options                          │
│ • But fits within 12-week timeline                          │
│ • BERT fine-tuning is publishable research                  │
│ • High scientific value for NCKH                            │
│                                                              │
│ Trade-off Impact: FAVORABLE                                  │
│ • Time investment yields high return                        │
│ • Scientific value is critical for NCKH                     │
└─────────────────────────────────────────────────────────────┘
```

#### Trade-off 4: Inference Speed vs Accuracy
```
┌─────────────────────────────────────────────────────────────┐
│ INFERENCE SPEED ────────────────────────────── ACCURACY     │
│                                                              │
│ ████████████░░░░░░░░░░░░░░░░░░░░████████████████████████░░ │
│     MED (~1-2s)                           HIGH (75-85%)     │
│                                                              │
│ Analysis:                                                    │
│ • BERT inference slower than CRF                            │
│ • ~1-2 seconds per CV is acceptable                         │
│ • Target: ≤5s per CV (we meet this)                         │
│ • Accuracy is more important for research                   │
│                                                              │
│ Trade-off Impact: ACCEPTABLE                                 │
│ • Speed is still within requirements                        │
│ • Accuracy priority is correct                              │
└─────────────────────────────────────────────────────────────┘
```

#### Option C Summary
| Gain | Sacrifice | Acceptable? |
|------|-----------|-------------|
| High accuracy | Training complexity | ✅ Yes |
| Scientific value | Development time | ✅ Yes |
| Modern approach | Inference speed | ✅ Yes |

**Verdict**: Trade-offs FAVORABLE. Recommended option.

---

### 3.4 Option D: LLM (GPT/Claude)

#### Trade-off 1: Development Speed vs Cost
```
┌─────────────────────────────────────────────────────────────┐
│ DEV SPEED ─────────────────────────────────── ONGOING COST  │
│                                                              │
│ ████████████████████████████░░░░░░████████████████████░░░░ │
│      FAST (1 week)                        HIGH ($10-100/mo) │
│                                                              │
│ Analysis:                                                    │
│ • Fastest to implement                                      │
│ • But ongoing API costs                                     │
│ • $0 budget constraint violated                             │
│ • Cost scales with usage                                    │
│                                                              │
│ Trade-off Impact: SEVERE                                     │
│ • Budget constraint is hard limit                           │
│ • Cannot afford API costs                                   │
└─────────────────────────────────────────────────────────────┘
```

#### Trade-off 2: Flexibility vs Scientific Rigor
```
┌─────────────────────────────────────────────────────────────┐
│ FLEXIBILITY ────────────────────────── SCIENTIFIC RIGOR     │
│                                                              │
│ ████████████████████████░░░░░░░░░░░░░░░░░░░░░░░░████░░░░░░ │
│      HIGH (prompt engineering)             LOW              │
│                                                              │
│ Analysis:                                                    │
│ • Prompts can be adjusted easily                            │
│ • No training needed                                        │
│ • BUT: "We used GPT" is not research contribution          │
│ • BUT: Cannot publish novel findings                        │
│                                                              │
│ Trade-off Impact: SEVERE                                     │
│ • Scientific value is critical for NCKH                     │
│ • Using LLM API is not acceptable contribution              │
└─────────────────────────────────────────────────────────────┘
```

#### Trade-off 3: Convenience vs Control
```
┌─────────────────────────────────────────────────────────────┐
│ CONVENIENCE ─────────────────────────────────── CONTROL     │
│                                                              │
│ ████████████████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │
│      HIGH (no training)                    LOW (black box)  │
│                                                              │
│ Analysis:                                                    │
│ • No model training needed                                  │
│ • Easy to use                                               │
│ • BUT: Cannot fine-tune on our data                        │
│ • BUT: Output format inconsistent                          │
│ • BUT: Model may change without notice                      │
│                                                              │
│ Trade-off Impact: MODERATE-SEVERE                           │
│ • Lack of control is problematic for research              │
└─────────────────────────────────────────────────────────────┘
```

#### Option D Summary
| Gain | Sacrifice | Acceptable? |
|------|-----------|-------------|
| Fast development | Ongoing cost | ❌ No |
| No training | Scientific value | ❌ No |
| Flexibility | Control & reproducibility | ❌ No |

**Verdict**: Trade-offs UNACCEPTABLE. Not suitable.

---

## 4. Cross-Option Trade-offs

### 4.1 Option A vs Option C
```
Choosing A over C means:
├── Gain: 4 weeks saved
├── Lose: 25-35% accuracy
├── Lose: Scientific credibility
└── Verdict: NOT WORTH IT

Choosing C over A means:
├── Lose: 4 weeks
├── Gain: 25-35% accuracy
├── Gain: Scientific credibility
└── Verdict: WORTH IT ✓
```

### 4.2 Option B vs Option C
```
Choosing B over C means:
├── Gain: 2 weeks saved
├── Gain: Simpler model
├── Lose: 10-20% accuracy
├── Lose: Some scientific novelty
└── Verdict: MAYBE (as backup)

Choosing C over B means:
├── Lose: 2 weeks
├── Lose: Model simplicity
├── Gain: 10-20% accuracy
├── Gain: Scientific novelty
└── Verdict: PREFERRED ✓
```

### 4.3 Summary Decision Matrix

| Comparison | Winner | Reason |
|------------|--------|--------|
| A vs B | B | Better accuracy |
| A vs C | C | Much better accuracy + science |
| A vs D | D | Better accuracy |
| B vs C | C | Better accuracy + science |
| B vs D | B | Zero cost + reproducible |
| C vs D | C | Zero cost + science + control |
| **Overall** | **C** | Best accuracy, science, cost |

---

## 5. Risk-Adjusted Trade-offs

### 5.1 Accuracy Risk

| Option | Expected F1 | Risk | Risk-Adjusted F1 |
|--------|-------------|------|------------------|
| A | 45% | Low (predictable) | 45% |
| B | 60% | Medium | 55% |
| C | 80% | Medium | 72% |
| D | 65% | High (variable) | 55% |

### 5.2 Timeline Risk

| Option | Dev Time | Risk | Risk-Adjusted Time |
|--------|----------|------|-------------------|
| A | 2 weeks | Low | 2 weeks |
| B | 4 weeks | Medium | 5 weeks |
| C | 6 weeks | Medium | 7 weeks |
| D | 1 week | Low | 1 week |

### 5.3 Cost Risk

| Option | Expected Cost | Risk | Risk-Adjusted Cost |
|--------|---------------|------|-------------------|
| A | $0 | None | $0 |
| B | $0 | None | $0 |
| C | $0 | Low (Colab limits) | $0 |
| D | $50/mo | High (usage spikes) | $100/mo |

---

## 6. Final Trade-off Verdict

```
┌─────────────────────────────────────────────────────────────┐
│                    TRADE-OFF CONCLUSION                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ✅ OPTION C (BERT) offers the best trade-off balance:      │
│                                                              │
│  1. ACCURACY vs COMPLEXITY                                   │
│     → High accuracy (75-85%) justifies complexity           │
│     → Complexity is manageable with tutorials               │
│                                                              │
│  2. TIME vs VALUE                                            │
│     → 6 weeks fits timeline (12 weeks total)                │
│     → Scientific value is critical, worth the time          │
│                                                              │
│  3. DATA vs PERFORMANCE                                      │
│     → 200 CVs annotation is achievable                      │
│     → Team has capacity for this                            │
│                                                              │
│  4. COST vs CAPABILITY                                       │
│     → $0 with Google Colab                                  │
│     → Gets state-of-the-art capability                      │
│                                                              │
│  No critical trade-offs sacrificed.                         │
│  All trade-offs are ACCEPTABLE for project goals.           │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

*Document created as part of CV Assistant Research Project documentation.*
