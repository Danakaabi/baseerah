# BASEERAH — Technical Verification Notes

## Overview

BASEERAH is an AI-assisted verification system for Islamic digital content.

The current MVP combines independent verification signals instead of relying on a single model.

For an uploaded audio clip, the full verification pipeline can perform:

1. Speech transcription
2. Trusted-source retrieval
3. Context tracing
4. Speaker identification
5. Synthetic-speech detection
6. Human-review policy

The unified API endpoint is:

POST /verify/audio/full

The frontend uses this endpoint through a single audio upload.

---

## 1. Speech-to-Text

Audio is transcribed using Whisper.

The transcription is used for content retrieval and source comparison.

Arabic transcription can contain errors, especially with:

- low-quality recordings
- background noise
- uncommon names
- classical or specialized terminology

For this reason, transcription alone is not treated as proof.

---

## 2. Trusted-Source Retrieval

BASEERAH uses multilingual sentence embeddings with FAISS retrieval.

The current embedding model is:

sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2

The system compares the extracted text against the curated knowledge base and returns the strongest available evidence.

A similarity or evidence score is not presented as a probability that the content is true.

If the evidence does not meet the verification threshold, the system returns insufficient evidence rather than forcing a source attribution.

---

## 3. Context Trace

When trusted evidence is available, BASEERAH can return:

- the matching passage
- previous context
- following context
- source metadata

This is designed to help detect quotations that may be technically real but presented without their original context.

---

## 4. Speaker Identification

Speaker embeddings are generated using:

microsoft/wavlm-base-plus-sv

The uploaded voice is compared against trusted reference profiles.

The current trusted voice registry is intentionally limited.

Current thresholds are provisional MVP thresholds and have not been calibrated on a large Arabic speaker-verification benchmark.

Speaker similarity does not prove that an audio recording is authentic.

A cloned or generated voice may imitate a real speaker, which is why speaker identity is analyzed separately from synthetic-speech detection.

---

## 5. Synthetic-Speech Detection

The experimental anti-spoofing component uses:

SpeechAntiSpoofingBenchmarks/Wav2Vec2-Small-AntiDeepfake

The ONNX model is downloaded from Hugging Face on first use and cached locally.

The detector analyzes a short audio window and returns independent natural/synthetic signal scores.

These scores are model outputs used as decision-support indicators.

They are NOT calibrated probabilities of authenticity.

The model is domain-dependent and must not be presented as forensic proof.

The model is distributed under the CC BY-NC-SA 4.0 license and is used here for a non-commercial hackathon prototype.

---

## 6. Audio Authenticity Engine

BASEERAH combines:

- speaker identity
- synthetic-speech detection

into an audio-level verification result.

Possible high-level outcomes include:

- supported
- needs_review

The system deliberately avoids claiming absolute authenticity.

---

## 7. Human-in-the-Loop Review

The unified verification pipeline includes a review policy.

Human review is requested when verification signals are incomplete, uncertain, or conflicting.

Examples include:

- insufficient trusted-source evidence
- unconfirmed speaker identity
- uncertain synthetic-speech analysis
- detected synthetic-speech indicators

Synthetic-speech indicators receive high-priority review.

This design prevents uncertain model outputs from being automatically presented as verified facts.

---

## 8. Tampering / Splice Detection

Audio tampering detection is currently experimental and is NOT enabled in the production MVP verification flow.

A signal-processing heuristic was tested against a controlled audio splice.

The heuristic did not reliably detect the known edit boundary.

Therefore BASEERAH does not currently claim reliable cut/splice detection.

A dedicated audio-forensics model and a properly designed evaluation dataset are future work.

---

## 9. Unified Verification Flow

Audio Upload
    |
    +--> Whisper
    |      |
    |      +--> Embeddings
    |             |
    |             +--> FAISS Retrieval
    |                     |
    |                     +--> Trusted Source
    |                     +--> Context Trace
    |
    +--> WavLM Speaker Identification
    |
    +--> Anti-Deepfake ONNX Model
    |
    +--> Audio Authenticity Engine
    |
    +--> Human Review Policy
    |
    +--> Unified Result

---

## 10. API

Primary audio endpoint:

POST /verify/audio/full

The endpoint returns:

- content_verification
- audio_authenticity
- review_policy
- review_status
- review_reasons

Other specialized endpoints remain available for component-level testing.

---

## 11. Input Safety

The API currently includes:

- supported audio-type validation
- empty-file rejection
- 25 MB upload limit
- temporary-file cleanup
- controlled HTTP error responses

The project is an MVP and is not presented as a production security-hardened service.

---

## 12. Testing

The repository currently contains 43 automated tests.

The tests cover areas including:

- text processing
- chunking
- embeddings
- vector retrieval
- context tracing
- text verification
- image verification
- audio verification
- deepfake API
- authenticity API
- full audio API
- human-review policy

All 43 tests pass when executed in isolated test groups.

On the current macOS / Python 3.13 development environment, running the entire suite in one Python process may terminate during interpreter teardown after all 43 tests have already passed.

The observed native error is:

recursive_mutex lock failed: Invalid argument

The isolated groups exit normally with status code 0.

This appears during native-library teardown and is not an assertion/test failure.

---

## 13. Current MVP Limitations

The current prototype has known limitations:

- trusted speaker registry is small
- retrieval is limited to the ingested knowledge base
- Whisper transcription may contain errors
- speaker thresholds are provisional
- anti-spoofing scores are not calibrated probabilities
- synthetic-speech performance is domain-dependent
- tampering detection is not enabled
- the full pipeline runs sequentially and may take time on local hardware

BASEERAH should therefore be presented as a verification assistant and evidence-tracing system, not as an infallible authenticity detector.

---

## 14. Future Work

Planned improvements include:

- larger trusted Islamic-source knowledge base
- more trusted speaker profiles
- Arabic speaker-verification calibration
- Arabic anti-spoofing evaluation dataset
- dedicated audio-forensics tampering model
- improved source provenance
- expanded human-review workflow
- proactive publisher-side digital fingerprinting
- content propagation / spread radar
