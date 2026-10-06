> **تحديث الواجهات — 5 أكتوبر 2026:** افتح `/ui/` من خادم FastAPI نفسه. أُضيف ربط النص والصورة والصوت الموحد والمقارنة والمصادر وسجل البصمة. تفاصيل التشغيل والتحقق والحدود في [FRONTEND_RELEASE](docs/FRONTEND_RELEASE.md). أرقام الاختبارات والحالات في الأقسام القديمة أدناه تاريخية؛ لم يُعتمد عدد إجمالي جديد دون تشغيل الاختبارات الكاملة بالنماذج.

<p align="center">
  <img src="docs/assets/baseerah-banner.png" alt="BASEERAH — بصيرة" width="100%">
</p>

<h1 align="center">بصيرة | BASEERAH</h1>

<p align="center">
  <strong>منصة ذكاء اصطناعي للتحقق من المحتوى الإسلامي الرقمي وتتبع مصدره وسياقه الأصلي</strong>
</p>

<p align="center">
  AI-Powered Islamic Content Verification & Context Tracing
</p>

<p align="center">
  <strong>افحص المصدر • راجع السياق • تحقق بالدليل</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.13-3776AB?logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/FastAPI-API-009688?logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/RAG-Hybrid-6C63FF" alt="Hybrid RAG">
  <img src="https://img.shields.io/badge/FAISS-Vector_Search-5A67D8" alt="FAISS">
  <img src="https://img.shields.io/badge/EasyOCR-Arabic_OCR-8B5CF6" alt="EasyOCR">
  <img src="https://img.shields.io/badge/Whisper-Arabic_ASR-7C3AED" alt="Whisper">
  <img src="https://img.shields.io/badge/Tests-43_Passing-success" alt="43 Tests Passing">
</p>

<p align="center">
  <strong>فريق أثَر | ATHAR — #368</strong><br>
  Islamic AI Challenge Hackathon
</p>

---

## عن بصيرة

**بصيرة (BASEERAH)** نموذج أولي لمنصة معرفية مدعومة بالذكاء الاصطناعي، صُممت للمساعدة في التحقق من المحتوى الإسلامي الرقمي المتداول والرجوع إلى **المصدر والسياق** بدل الاكتفاء بمشاهدة اقتباس أو مقطع منفصل.

يدعم الـBackend الحالي ثلاثة أنواع من المدخلات:

- **Text** — التحقق من النصوص والاقتباسات.
- **Image** — استخراج النص العربي باستخدام OCR ثم التحقق منه.
- **Audio** — تحليل الصوت وتتبع المصدر والسياق والتحقق من هوية المتحدث ورصد مؤشرات الصوت الصناعي مع مراجعة بشرية عند الحاجة.

لا تهدف بصيرة إلى إصدار فتوى أو استبدال المرجعية العلمية، وإنما إلى تقديم **أدلة قابلة للتتبع** تساعد المستخدم على مراجعة المصدر والسياق.

---

## المشكلة

قد ينتشر محتوى ديني رقمي على شكل:

- اقتباس مكتوب.
- صورة تحتوي على نص.
- مقطع صوتي.
- جزء مقتطع من محاضرة أو درس.
- محتوى منسوب إلى عالم أو مصدر معين.

المشكلة ليست دائمًا في وجود الكلمات نفسها، بل قد تكون في:

1. فقدان المصدر الأصلي.
2. اقتطاع الكلام من سياقه.
3. حذف ما قبله أو ما بعده.
4. نسبة النص إلى مصدر غير صحيح.
5. تداول محتوى لا يوجد عليه دليل كافٍ.

ومن هنا جاءت فكرة:

> **Context Trace — تتبع السياق**

بحيث لا تعرض بصيرة التطابق فقط، بل تحاول إرجاع المستخدم إلى الموضع المرتبط به داخل المصدر.

---

## الحل

يمر المحتوى داخل بصيرة عبر Pipeline موحدة للتحقق:

```text
                     ┌─────────────────┐
                     │      INPUT      │
                     └────────┬────────┘
                              │
                ┌─────────────┼─────────────┐
                │             │             │
              Text          Image         Audio
                │             │             │
                │          EasyOCR     Faster-Whisper
                │             │             │
                └─────────────┼─────────────┘
                              │
                              ▼
                    Arabic Normalization
                              │
                              ▼
                     Candidate Windows
                              │
                              ▼
                ┌─────────────────────────┐
                │ Retrieval / Quote Match │
                └────────────┬────────────┘
                             │
                             ▼
                   Trusted Knowledge Base
                             │
                             ▼
                      Confidence Gate
                       ┌─────┴─────┐
                       │           │
                  Sufficient   Insufficient
                   Evidence      Evidence
                       │           │
                       ▼           ▼
                 Context Trace  Safe Abstention
                       │
                       ▼
              Source + Context + Evidence
```

---

## Context Trace

الميزة المحورية في بصيرة هي **تتبع السياق**.

عند العثور على مقطع مرتبط بالمحتوى، لا يكتفي النظام بإظهار نتيجة البحث، بل يستطيع استرجاع:

```text
Previous Context
      ↓
Matched Content
      ↓
Next Context
```

ويتم ذلك بالاعتماد على ترتيب `chunk_index` داخل المصدر نفسه.

هذا التصميم يسمح بعرض:

- الكلام السابق.
- الجزء المطابق.
- الكلام اللاحق.
- اسم المصدر.
- عنوان الوثيقة.
- رابط المصدر عند توفره.

بدون تخزين نسخ مكررة من السياق داخل كل Chunk.

---

## الذكاء الاصطناعي المستخدم

### 1. Semantic Embeddings

يستخدم المشروع:

```text
sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
```

لإنشاء تمثيلات دلالية للنصوص العربية والاستعلامات.

---

### 2. FAISS Vector Search

يستخدم **FAISS** للبحث الدلالي السريع داخل المقاطع المفهرسة من المصادر.

---

### 3. Hybrid RAG

بصيرة لا تعتمد على تشابه واحد فقط.

يتم حساب التشابه بشكل منفصل بين:

- عنوان المصدر.
- محتوى المقطع.

ثم دمجهما حاليًا بالأوزان:

```text
Title Similarity   = 60%
Content Similarity = 40%
```

هذه النتيجة هي **درجة تقنية للاسترجاع** وليست حكمًا شرعيًا أو نسبة لصحة الحديث أو الفتوى.

---

### 4. Quote Matching

المحتوى الناتج من OCR أو ASR قد يحتوي على أخطاء مثل:

```text
الله → اللة
```

أو فقدان مسافات وكلمات.

لذلك أضيفت طبقة **Quote Matcher** للمساعدة في اكتشاف الاقتباسات القريبة لفظيًا قبل الرجوع إلى الاسترجاع الدلالي عند الحاجة.

هذه الطبقة مخصصة لمرشحات OCR/ASR ولا تستبدل البحث الدلالي العام للنصوص.

---

### 5. Arabic OCR

تستخدم بصيرة:

```text
EasyOCR
```

لاستخراج النص العربي من الصور.

بعد الاستخراج يتم بناء Sliding Windows من المقاطع النصية، ثم إرسالها إلى مسار التحقق نفسه.

---

### 6. Arabic Speech Recognition

تستخدم بصيرة:

```text
Faster-Whisper
```

لتحويل الصوت العربي إلى نص.

المسار:

```text
Audio
  ↓
Whisper ASR
  ↓
Transcript Segments
  ↓
Candidate Windows
  ↓
Quote Matching / Retrieval
  ↓
Verification
```

---

## Audio Intelligence Engine

يتضمن مسار التحقق الصوتي في بصيرة عدة إشارات مستقلة:

- **Faster-Whisper** لتحويل الصوت العربي إلى نص.
- **Embeddings + FAISS** للبحث عن المصدر والسياق.
- **WavLM Speaker Verification** لمقارنة هوية المتحدث مع الأصوات المرجعية الموثوقة.
- **Anti-Deepfake ONNX Model** لرصد مؤشرات الصوت الصناعي بشكل تجريبي.
- **Human Review Policy** لتحويل الحالات غير الحاسمة أو المتعارضة إلى مراجعة بشرية بدل إصدار حكم تلقائي.

المسار الموحد المستخدم في الواجهة:

`POST /verify/audio/full`

> نتائج التحقق الصوتي هي مؤشرات مساعدة وليست إثباتا جنائيا نهائيا لأصالة التسجيل. ميزة اكتشاف القص والدمج ما زالت تجريبية وغير مفعلة في مسار الـMVP لأنها لم تجتز التحقق المضبوط بشكل موثوق.

للتفاصيل التقنية والقيود والتقييم: `docs/TECHNICAL_VERIFICATION.md`

---

## Safe Abstention

أحد المبادئ الأساسية في بصيرة:

> **عدم وجود دليل كافٍ أفضل من اختراع إجابة.**

إذا لم يتجاوز الدليل حدود الثقة التقنية، يعيد النظام:

```text
لم يتم العثور على دليل كافٍ للتحقق من هذا المحتوى.
```

وفي هذه الحالة لا يعرض مصدرًا أو Context Trace على أنه مؤكد.

---

## Confidence Gate

يستخدم النظام حاليًا حدودًا تقنية للتحكم في قبول نتائج الاسترجاع:

```python
MIN_FINAL_SCORE = 0.30
MIN_MARGIN = 0.05
```

أما Quote Matching فيستخدم:

```python
MIN_QUOTE_SCORE = 0.40
MIN_QUOTE_MARGIN = 0.15
```

> هذه الحدود تخص جودة المطابقة والاسترجاع فقط، ولا تمثل درجة صحة دينية.

---

## المصادر والمرجعية

تم تصميم بنية بصيرة بحيث تكون قاعدة المعرفة **مقيدة بمصادر موثوقة ومحددة** بدل البحث المفتوح غير المنضبط.

يتضمن نموذج البيانات الحالي محتوى تجريبيًا مستوردًا من مصادر مثل:

- **HadeethEnc — موسوعة الأحاديث النبوية**
- **الدرر السنية — الموسوعة الحديثية**

كما تم استخدام مادة صوتية تجريبية من:

- **IslamHouse**

ويحتفظ كل مقطع ببيانات Metadata تسمح بتتبعه، ومنها:

```text
source_id
source_name
source_url
document_title
speaker_or_author
section
chunk_index
original_text
normalized_text
```

### مبدأ مهم

يحتفظ النظام بنسختين:

```text
original_text
```

للعرض والتوثيق.

و:

```text
normalized_text
```

للبحث والمطابقة.

وبذلك لا نضطر إلى تغيير النص الأصلي من أجل تحسين الاسترجاع.

---

## API

يعمل الـBackend باستخدام **FastAPI**.

### Health Check

```http
GET /health
```

### Text Verification

```http
POST /verify/text
```

مثال:

```json
{
  "text": "إن الله لا ينظر إلى صوركم وأموالكم"
}
```

### Image Verification

```http
POST /verify/image
```

يدعم حاليًا:

```text
JPG
JPEG
PNG
WEBP
```

الحد الأقصى:

```text
5 MB
```

### Audio Verification

```http
POST /verify/audio
```

يدعم حاليًا:

```text
MP3
WAV
M4A
OGG
WEBM
```

الحد الأقصى:

```text
25 MB
```

---

## مثال على نتيجة التحقق

عند العثور على دليل مناسب يمكن أن تعيد الـAPI بنية تحتوي على:

```json
{
  "status": "evidence_found",
  "message": "تم العثور على دليل ذي صلة في مصدر معتمد.",
  "evidence_score": {
    "final_score": 0.6458,
    "margin": 0.1605
  },
  "source": {
    "source_id": "dorar-bukhari-1519",
    "document_title": "أي الأعمال أفضل؟"
  },
  "context_trace": {
    "previous": null,
    "current": {},
    "next": null
  }
}
```

---

## هيكل المشروع

```text
baseerah/
│
├── app/
│   ├── api/
│   │   ├── health.py
│   │   └── verify.py
│   │
│   ├── ingestion/
│   │   ├── text.py
│   │   ├── image.py
│   │   ├── audio.py
│   │   └── chunker.py
│   │
│   ├── models/
│   │   └── schemas.py
│   │
│   ├── rag/
│   │   ├── embeddings.py
│   │   ├── vector_store.py
│   │   └── retriever.py
│   │
│   ├── verification/
│   │   ├── confidence.py
│   │   ├── context_trace.py
│   │   ├── quote_matcher.py
│   │   └── verifier.py
│   │
│   └── main.py
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── demo/
│
├── docs/
│   ├── assets/
│   │   └── baseerah-banner.png
│   └── evidence/
│
├── scripts/
│   ├── fetch_hadeethenc.py
│   ├── prepare_hadeethenc.py
│   └── ingest_sources.py
│
├── tests/
│
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

---

## تشغيل المشروع

### 1. Clone

```bash
git clone https://github.com/Danakaabi/baseerah.git
cd baseerah
```

### 2. إنشاء Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. تثبيت Dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. تشغيل الـAPI

```bash
uvicorn app.main:app --reload
```

بعد التشغيل:

```text
http://127.0.0.1:8000
```

Swagger:

```text
http://127.0.0.1:8000/docs
```

---

## تشغيل الاختبارات

```bash
pytest -q
```

آخر نتيجة موثقة أثناء تطوير النموذج:

```text
33 passed
0 failed
```

تشمل الاختبارات:

- Arabic normalization.
- Chunking.
- Embeddings.
- Vector Store.
- Hybrid Retrieval.
- Context Trace.
- Verification Engine.
- Confidence Gate.
- Text API.
- Image API.
- Audio API.
- Failure cases.

---

## أدلة التنفيذ

يحتوي المشروع على أدلة تشغيل محفوظة في:

```text
docs/evidence/
```

ومنها:

```text
audio_evidence_found.txt
audio_safe_abstention.txt
stage11_final_api.txt
```

وهي توثق حالات مثل:

```text
Audio → Evidence Found
Audio → Safe Abstention
Text API
Image API
Audio API
33 Passing Tests
```

---

## تجهيز البيانات

يمكن تجهيز بيانات HadeethEnc الموجودة محليًا باستخدام:

```bash
python -m scripts.prepare_hadeethenc
```

ثم بناء المقاطع المفهرسة:

```bash
python -m scripts.ingest_sources
```

كما يدعم:

```bash
python -m scripts.fetch_hadeethenc
```

جلب سجلات HadeethEnc وفق المعرّفات المحددة.

> هذه الآلية توسّع ingestion حسب IDs المعروفة، وليست Crawler عامًا لكامل الموسوعة.

---

## مبادئ السلامة

صُممت بصيرة وفق مجموعة مبادئ أساسية:

### Source First

لا يتم تقديم مصدر غير موجود داخل قاعدة المعرفة على أنه دليل مؤكد.

### Traceability

كل دليل مسترجع يحتفظ ببيانات المصدر اللازمة لتتبعه.

### Context Before Judgment

وجود تطابق نصي وحده لا يكفي لفهم المحتوى، لذلك يعرض النظام السياق المرتبط به عندما يكون متاحًا.

### Safe Abstention

عند عدم كفاية الدليل، يمتنع النظام عن الادعاء.

### Separation of Scores

درجة FAISS أو Quote Matching:

```text
Technical Retrieval Score
```

وليست:

```text
Religious Authenticity Score
```

### Human Review

بصيرة أداة مساعدة للتحقق والوصول إلى الأدلة، وليست بديلًا عن المختصين أو الجهات العلمية.

---

## ما تم تنفيذه فعليًا

- [x] FastAPI backend
- [x] Arabic normalization
- [x] Trusted-source ingestion
- [x] Chunking with metadata
- [x] Multilingual embeddings
- [x] FAISS vector search
- [x] Hybrid RAG
- [x] Quote matching
- [x] Confidence Gate
- [x] Safe Abstention
- [x] Context Trace
- [x] Text verification API
- [x] Arabic image OCR
- [x] Image verification API
- [x] Arabic audio transcription
- [x] Audio verification API
- [x] Unified verification architecture
- [x] Automated tests
- [x] Evidence documentation

---

## حالة النموذج الأولي

```text
Backend Core          ✅
Text Verification     ✅
Image Verification    ✅
Audio Verification    ✅
Hybrid RAG            ✅
Context Trace         ✅
Safe Abstention       ✅
Automated Tests       ✅
Frontend Integration  ⏳
Final E2E Demo         ⏳
```

الـBackend قابل للتشغيل والاختبار حاليًا.

ربط واجهة HTML/CSS/JavaScript الخاصة بالنموذج هو مرحلة التكامل التالية.

---

## حدود النموذج الحالي

بصيرة حاليًا **Hackathon MVP / Prototype** وليست خدمة إنتاجية نهائية.

من الحدود الحالية:

- قاعدة المعرفة ما زالت محدودة لأغراض النموذج الأولي.
- دقة OCR وASR تعتمد على جودة الصورة أو التسجيل.
- التشابه الدلالي لا يثبت وحده صحة النسبة.
- النظام الحالي لا يصدر فتوى.
- النظام لا يحكم على الأشخاص أو الجماعات.
- نتائج الاسترجاع هي أدلة تقنية مساعدة وليست أحكامًا شرعية.
- يلزم توسيع التقييم على Dataset أكبر قبل أي استخدام إنتاجي.
- يلزم توسيع المصادر الموثوقة وربطها وفق حقوق الاستخدام وسياسات الجهات المالكة.

---

## التوسع المستقبلي

بعد إثبات النموذج الأولي يمكن تطوير بصيرة نحو:

```text
Trusted Source APIs
        ↓
Larger Knowledge Base
        ↓
Advanced Context Trace
        ↓
Human Review Workflow
        ↓
Source Provenance
        ↓
Multimodal Verification
```

ومن الأفكار المستقبلية أيضًا **التوثيق الاستباقي** للمحتوى الأصلي بحيث تتمكن الجهات أو أصحاب المحتوى من تسجيل الأصل والسياق وقت النشر، ثم الرجوع إليه عند انتشار نسخ مقتطعة أو منسوبة بصورة غير صحيحة.

---

## Demo

Frontend prototype:

https://melodious-shortbread-c18ef9.netlify.app/

> واجهة العرض الحالية تمثل تجربة المستخدم للنموذج الأولي، ويجري ربطها بالـBackend الموجود في هذا المستودع.

---

## الفريق

### فريق أثَر | ATHAR — #368

| العضو | المساهمة في المشروع |
|---|---|
| **دانا الكعبي** | Technical Lead — AI Architecture, Backend, RAG & Verification Engineering |
| **ريما العتيبي** | Frontend — HTML/CSS/JavaScript |
| **جنى زهير المشهراوي** | UI/UX Support |
| **لمى الحربي** | Islamic Content Research & Review |

تم تطوير بصيرة كنموذج أولي ضمن **Islamic AI Challenge Hackathon**.

---

## Tech Stack

```text
Python 3.13
FastAPI
Pydantic
Sentence Transformers
FAISS
EasyOCR
Faster-Whisper
PyTorch
Pytest
HTTPX
Uvicorn
```

---

## الخصوصية والأسرار

لا يجب رفع:

```text
.env
API Keys
Tokens
Credentials
Virtual Environments
Local Model Caches
```

إلى GitHub.

يحتوي المستودع على:

```text
.env.example
```

كمثال فقط عند الحاجة إلى متغيرات بيئية.

---

## ملاحظة للجنة التحكيم

الهدف من النموذج ليس تقديم حكم ديني آلي.

الهدف هو إثبات إمكانية بناء مسار تقني قابل للتفسير:

```text
محتوى متداول
      ↓
استخراج وفهم المدخل
      ↓
البحث داخل مصادر موثوقة
      ↓
قياس قوة الدليل
      ↓
إظهار المصدر والسياق
      ↓
أو الامتناع عند عدم كفاية الدليل
```

**بصيرة لا تطلب من المستخدم أن يثق في إجابة الذكاء الاصطناعي فقط؛ بل تعيده إلى الدليل الذي يمكنه مراجعته.**

---

<p align="center">
  <strong>بصيرة | BASEERAH</strong>
</p>

<p align="center">
  افحص المصدر • راجع السياق • ثم قرر هل تشارك
</p>

<p align="center">
  فريق أثَر | ATHAR — #368
</p>
