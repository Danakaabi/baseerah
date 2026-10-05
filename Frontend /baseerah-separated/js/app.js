const pageMap = {
  home: "../index.html",
  tools: "tools.html",
  authors: "authors.html",
  more: "more.html",
  compare: "compare.html",
  "compare-r": "compare-result.html",
  detect: "detect.html",
  "detect-r": "detect-result.html",
  quote: "quote.html",
  sources: "sources.html",
  log: "log.html",
  saved: "saved.html",
  "doc-account": "doc-account.html",
  "doc-upload": "doc-upload.html",
  "doc-confirm": "doc-confirm.html",
  radar: "radar.html",
  detail: "detail.html"
};

function isRootIndex(){
  return window.location.pathname.endsWith("/index.html") ||
         window.location.pathname.endsWith("/") ||
         !window.location.pathname.includes("/pages/");
}

function go(id){
  if(id === "home"){
    window.location.href = isRootIndex() ? "index.html" : "../index.html";
    return;
  }
  const target = pageMap[id];
  if(!target) return;
  window.location.href = isRootIndex() ? `pages/${target}` : target;
}

function goBack(){
  if(window.history.length > 1){
    window.history.back();
  } else {
    go("home");
  }
}

function toggle(id){
  const el = document.getElementById(id);
  if(el) el.classList.toggle("off");
}

function openDetail(title){
  sessionStorage.setItem("baseerahDetailTitle", title);
  go("detail");
}

function wireUploader(fieldId, inputId, defaultText){
  const field = document.getElementById(fieldId);
  const input = document.getElementById(inputId);
  if(!field || !input) return;

  field.addEventListener("click", () => input.click());

  input.addEventListener("change", () => {
    const file = input.files?.[0];
    if(file){
      if(!file.type.startsWith("audio/")){
        input.value = "";
        field.textContent = defaultText;
        alert("يرجى اختيار ملف صوتي فقط.");
        return;
      }
      field.textContent = `✓ ${file.name}`;
      field.style.color = "var(--cream)";
      field.style.borderColor = "var(--gold)";
    }else{
      field.textContent = defaultText;
      field.style.color = "var(--muted)";
      field.style.borderColor = "var(--line)";
    }
  });
}

function renderWave(id, count=50){
  const wave = document.getElementById(id);
  if(!wave) return;
  wave.innerHTML = "";
  for(let i=0;i<count;i++){
    const span = document.createElement("span");
    const height = 6 + ((i * 13) % 21);
    span.style.height = `${height}px`;
    wave.appendChild(span);
  }
}

const authorItems = [
  {t:"كيف تتحقق من مقطع منسوب لعالم؟", c:"أدلة", f:"evidence"},
  {t:"علامات قد تدل على صوت مستنسخ", c:"أدلة", f:"evidence"},
  {t:"توثيق المصدر الأصلي", c:"أدلة", f:"evidence"},
  {t:"قاعدة: السياق قبل الاقتباس", c:"قواعد", f:"rules"},
  {t:"الإسناد والنقل الأمين", c:"قواعد", f:"rules"},
  {t:"دليل المشاركة المسؤولة", c:"قواعد", f:"rules"}
];

function renderAuthors(filter="all"){
  const list = document.getElementById("alist");
  if(!list) return;

  const items = filter === "all"
    ? authorItems
    : filter === "saved"
      ? []
      : authorItems.filter(item => item.f === filter);

  if(items.length === 0){
    list.className = "empty";
    list.innerHTML = "لا توجد نتائج";
    return;
  }

  list.className = "card compact";
  list.innerHTML = "";

  items.forEach(item => {
    const row = document.createElement("div");
    row.className = "row";
    row.innerHTML = `
      <span class="chev">‹</span>
      <div class="rowtext">
        <b></b>
        <span></span>
      </div>
      <div class="ic">▤</div>
    `;
    row.querySelector("b").textContent = item.t;
    row.querySelector(".rowtext span").textContent = item.c;
    row.addEventListener("click", () => openDetail(item.t));
    list.appendChild(row);
  });
}

function initAuthorFilters(){
  const pills = document.getElementById("apills");
  if(!pills) return;

  pills.addEventListener("click", event => {
    const btn = event.target.closest(".pill");
    if(!btn) return;
    pills.querySelectorAll(".pill").forEach(p => p.classList.remove("on"));
    btn.classList.add("on");
    renderAuthors(btn.dataset.f);
  });

  renderAuthors("all");
}

function initDetail(){
  const title = document.getElementById("detailTitle");
  if(title){
    title.textContent = sessionStorage.getItem("baseerahDetailTitle") || "التفاصيل";
  }
}

document.addEventListener("DOMContentLoaded", () => {
  initAuthorFilters();
  initDetail();

  renderWave("wv1");
  renderWave("wv2");
  renderWave("wv3");

  wireUploader("up-detect","file-detect","⬆ اختر مقطعًا صوتيًا للفحص");
  wireUploader("up-doc","file-doc","⬆ اسحب الملف الصوتي هنا أو اختره");
  wireUploader("up-cmp1","file-cmp1","⬆ اختر المقطع الأول");
  wireUploader("up-cmp2","file-cmp2","⬆ اختر المقطع الثاني");
});

/* ==============================
   BASEERAH AUDIO VERIFICATION API
   ============================== */

async function verifyAudio() {
  const input = document.getElementById("file-detect");
  const button = document.getElementById("verifyAudioBtn");
  const status = document.getElementById("audioStatus");

  if (!input || !button || !status) return;

  const file = input.files?.[0];

  if (!file) {
    status.style.display = "block";
    status.textContent = "اختاري مقطعًا صوتيًا أولًا.";
    return;
  }

  const allowedExtensions = /\.(mp3|wav|m4a|ogg|webm)$/i;

  if (!allowedExtensions.test(file.name)) {
    status.style.display = "block";
    status.textContent = "صيغة الملف غير مدعومة.";
    return;
  }

  const maxSize = 25 * 1024 * 1024;

  if (file.size > maxSize) {
    status.style.display = "block";
    status.textContent = "حجم الملف أكبر من 25MB.";
    return;
  }

  const formData = new FormData();
  formData.append("audio", file);

  button.disabled = true;
  button.textContent = "جاري التحليل...";

  status.style.display = "block";
  status.textContent = "يتم الآن تحليل المقطع الصوتي...";

  try {
    const response = await fetch(
      "http://127.0.0.1:8000/verify/audio/full",
      {
        method: "POST",
        body: formData
      }
    );

    if (!response.ok) {
      let message = `خطأ من الخادم: ${response.status}`;

      try {
        const data = await response.json();
        message = data.detail || data.message || message;
      } catch (_) {}

      throw new Error(message);
    }

    const result = await response.json();

    sessionStorage.setItem(
      "baseerahAudioResult",
      JSON.stringify(result)
    );

    window.location.href = "detect-result.html";

  } catch (error) {
    console.error("Baseerah audio verification error:", error);

    status.textContent =
      "تعذر الاتصال بمحرك بصيرة. تأكدي أن Backend يعمل على المنفذ 8000.";

  } finally {
    button.disabled = false;
    button.textContent = "ابدأ التحقق";
  }
}


document.addEventListener("DOMContentLoaded", () => {
  const button = document.getElementById("verifyAudioBtn");

  if (button) {
    button.addEventListener("click", verifyAudio);
  }
});


/* ==========================================
   BASEERAH REAL AUDIO RESULT RENDERING
   ========================================== */

function renderAudioResult() {
  const title = document.getElementById("resultTitle");

  if (!title) return;

  const raw = sessionStorage.getItem(
    "baseerahAudioResult"
  );

  if (!raw) {
    title.textContent = "لا توجد نتيجة محفوظة";

    const message =
      document.getElementById("resultMessage");

    if (message) {
      message.textContent =
        "ارجعي إلى صفحة التحقق وارفعِي مقطعًا صوتيًا أولًا.";
    }

    return;
  }

  try {
    const report = JSON.parse(raw);

    /*
     * /verify/audio/full returns the content result
     * separately from the audio-authenticity signals.
     *
     * Fallback to report itself keeps compatibility
     * with older saved BASEERAH results.
     */
    const result =
      report.content_verification || report;

    const authenticity =
      report.audio_authenticity || {};

    const policy =
      report.review_policy || {};

    const score = Number(
      result?.evidence_score?.final_score || 0
    );

    const percentage =
      Math.round(score * 100);

    // -----------------------------
    // Overall result
    // -----------------------------

    if (report.review_status === "supported") {
      title.textContent =
        "النتيجة مدعومة بالأدلة المتاحة";
    } else if (
      report.review_status === "needs_review"
    ) {
      title.textContent =
        "النتيجة تحتاج إلى مراجعة";
    } else if (
      result.status === "evidence_found"
    ) {
      title.textContent =
        "تم العثور على دليل ذي صلة";
    } else {
      title.textContent =
        "اكتمل التحليل";
    }

    const message =
      document.getElementById("resultMessage");

    if (message) {
      message.textContent =
        result.message ||
        "اكتمل تحليل المحتوى والإشارة الصوتية.";
    }

    const scoreBox =
      document.getElementById("scoreBox");

    if (scoreBox) {
      if (result.status === "evidence_found") {
        scoreBox.textContent =
          `درجة قوة الدليل: ${percentage}%`;
      } else {
        scoreBox.textContent =
          `أعلى تطابق: ${percentage}% — لم يصل إلى حد التحقق`;
      }
    }

    // -----------------------------
    // Transcript
    // -----------------------------

    const transcript =
      document.getElementById("transcript");

    if (transcript) {
      transcript.textContent =
        result.query ||
        "لم يتم استخراج نص.";
    }

    // -----------------------------
    // Trusted source
    // -----------------------------

    const sourceName =
      document.getElementById("sourceName");

    if (sourceName) {
      sourceName.textContent =
        result?.source?.source_name ||
        "لم يتم تأكيد مصدر موثوق";
    }

    const documentTitle =
      document.getElementById("documentTitle");

    if (documentTitle) {
      documentTitle.textContent =
        result?.source?.document_title || "";
    }

    // -----------------------------
    // Context Trace
    // -----------------------------

    const previous =
      document.getElementById("contextPrevious");

    if (previous) {
      previous.textContent =
        result?.context_trace?.previous
          ?.original_text ||
        "لا يوجد سياق سابق.";
    }

    const current =
      document.getElementById("contextCurrent");

    if (current) {
      current.textContent =
        result?.context_trace?.current
          ?.original_text ||
        result?.source?.original_text ||
        "غير متاح.";
    }

    const next =
      document.getElementById("contextNext");

    if (next) {
      next.textContent =
        result?.context_trace?.next
          ?.original_text ||
        "لا يوجد سياق لاحق.";
    }

    const sourceButton =
      document.getElementById("sourceLinkBtn");

    if (sourceButton) {
      const url =
        result?.source?.source_url;

      if (url) {
        sourceButton.style.display = "";

        sourceButton.onclick = () => {
          window.open(
            url,
            "_blank",
            "noopener,noreferrer"
          );
        };
      } else {
        sourceButton.style.display = "none";
      }
    }

    // -----------------------------
    // Speaker identity
    // -----------------------------

    const speaker =
      authenticity.speaker_identity || {};

    const speakerStatus =
      document.getElementById("speakerStatus");

    const speakerName =
      document.getElementById("speakerName");

    const speakerScore =
      document.getElementById("speakerScore");

    const speakerPercentage =
      Math.round(
        Number(speaker.best_score || 0) * 100
      );

    if (speakerStatus) {
      if (
        speaker.interpretation ===
        "trusted_match"
      ) {
        speakerStatus.textContent =
          "تطابق مع صوت مرجعي موثوق";
      } else if (
        speaker.interpretation === "uncertain"
      ) {
        speakerStatus.textContent =
          "هوية المتحدث غير مؤكدة";
      } else {
        speakerStatus.textContent =
          "المتحدث غير موجود في السجل الموثوق";
      }
    }

    if (speakerName) {
      speakerName.textContent =
        speaker?.best_match?.speaker_name ||
        "لم يتم تأكيد هوية المتحدث";
    }

    if (speakerScore) {
      speakerScore.textContent =
        `مؤشر تشابه البصمة الصوتية: ${speakerPercentage}% — درجة تشابه وليست احتمالًا للهوية.`;
    }

    // -----------------------------
    // Synthetic speech analysis
    // -----------------------------

    const synthetic =
      authenticity.synthetic_voice || {};

    const syntheticStatus =
      document.getElementById(
        "syntheticStatus"
      );

    const syntheticScore =
      document.getElementById(
        "syntheticScore"
      );

    const naturalPercentage =
      Math.round(
        Number(
          synthetic.natural_score || 0
        ) * 100
      );

    const fakePercentage =
      Math.round(
        Number(
          synthetic.synthetic_score || 0
        ) * 100
      );

    if (syntheticStatus) {
      if (
        synthetic.interpretation ===
        "likely_natural"
      ) {
        syntheticStatus.textContent =
          "لم تظهر مؤشرات قوية على صوت صناعي";
      } else if (
        synthetic.interpretation ===
        "likely_synthetic"
      ) {
        syntheticStatus.textContent =
          "رُصدت مؤشرات على صوت صناعي";
      } else {
        syntheticStatus.textContent =
          "تحليل الصوت الصناعي غير حاسم";
      }
    }

    if (syntheticScore) {
      syntheticScore.textContent =
        `مؤشر الإشارة الطبيعية: ${naturalPercentage}% — مؤشر الإشارة الصناعية: ${fakePercentage}%`;
    }

    // -----------------------------
    // Human review policy
    // -----------------------------

    const reviewDecision =
      document.getElementById(
        "reviewDecision"
      );

    const reviewPriority =
      document.getElementById(
        "reviewPriority"
      );

    const reviewReasons =
      document.getElementById(
        "reviewReasons"
      );

    if (reviewDecision) {
      if (
        policy.decision ===
        "auto_supported"
      ) {
        reviewDecision.textContent =
          "مدعوم وفق الإشارات المتاحة";
      } else if (
        policy.decision ===
        "high_priority_review"
      ) {
        reviewDecision.textContent =
          "تحتاج الحالة إلى مراجعة بشرية عاجلة";
      } else {
        reviewDecision.textContent =
          "تحتاج الحالة إلى مراجعة بشرية";
      }
    }

    if (reviewPriority) {
      if (policy.priority === "high") {
        reviewPriority.textContent =
          "أولوية المراجعة: عالية";
      } else if (
        policy.human_review_required === true
      ) {
        reviewPriority.textContent =
          "أولوية المراجعة: عادية";
      } else {
        reviewPriority.textContent =
          "لا تتطلب مراجعة بشرية حاليًا";
      }
    }

    if (reviewReasons) {
      const reasons =
        Array.isArray(policy.reasons)
          ? policy.reasons
          : [];

      const reasonTranslations = {
        "Synthetic-speech indicators were detected.":
          "تم رصد مؤشرات على صوت صناعي.",
        "Synthetic-speech analysis is uncertain.":
          "تحليل الصوت الصناعي غير حاسم.",
        "Speaker identity is not confirmed.":
          "لم يتم تأكيد هوية المتحدث.",
        "Trusted-source evidence is insufficient.":
          "الأدلة من المصادر الموثوقة غير كافية.",
        "Audio-level verification is not fully supported.":
          "نتيجة التحقق على مستوى الصوت غير مدعومة بالكامل.",
        "Available verification signals are mutually supportive.":
          "إشارات التحقق المتاحة متوافقة وتدعم النتيجة."
      };

      const translatedReasons =
        reasons.map(
          reason =>
            reasonTranslations[reason] || reason
        );

      reviewReasons.textContent =
        translatedReasons.length
          ? translatedReasons.join(" • ")
          : "لا توجد أسباب إضافية للمراجعة.";
    }

  } catch (error) {
    console.error(
      "Unable to render BASEERAH full result:",
      error
    );

    title.textContent =
      "تعذر قراءة نتيجة التحليل";
  }
}


document.addEventListener(
  "DOMContentLoaded",
  renderAudioResult
);

// BASEERAH Trusted Speaker Identification UI
async function verifySpeakerFromUI() {
  const candidateInput =
    document.getElementById("speaker-candidate");

  const button =
    document.getElementById("verifySpeakerBtn");

  const resultBox =
    document.getElementById("speakerResult");

  if (!candidateInput || !button || !resultBox) {
    return;
  }

  const candidate = candidateInput.files?.[0];

  if (!candidate) {
    resultBox.style.display = "block";
    resultBox.textContent =
      "اختاري المقطع الصوتي المراد التحقق منه.";
    return;
  }

  const formData = new FormData();
  formData.append("audio", candidate);

  button.disabled = true;
  button.textContent = "جاري تحليل البصمة الصوتية...";

  resultBox.style.display = "block";
  resultBox.textContent =
    "يتم الآن البحث في الأصوات المرجعية الموثوقة.";

  try {
    const response = await fetch(
      "http://127.0.0.1:8000/verify/speaker/identify",
      {
        method: "POST",
        body: formData,
      }
    );

    if (!response.ok) {
      const error = await response.json()
        .catch(() => ({}));

      throw new Error(
        error.detail ||
        "تعذر التحقق من هوية المتحدث."
      );
    }

    const data = await response.json();

    const score = Number(data.best_score ?? 0);
    const percentage = Math.round(score * 100);
    const best = data.best_match || {};

    if (
      data.match_found === true &&
      data.interpretation === "trusted_match"
    ) {
      resultBox.innerHTML = `
        <div style="font-weight:700;margin-bottom:8px;">
          تطابق مع صوت مرجعي موثوق
        </div>

        <div style="font-size:18px;font-weight:700;">
          ${best.speaker_name || "متحدث موثوق"}
        </div>

        <div style="margin-top:8px;">
          مؤشر تشابه البصمة الصوتية:
          <strong>${percentage}%</strong>
        </div>

        <div style="color:var(--muted);font-size:12px;margin-top:8px;">
          المؤشر درجة تشابه وليس احتمالًا إحصائيًا للهوية.
        </div>
      `;
    } else {
      resultBox.innerHTML = `
        <div style="font-weight:700;margin-bottom:8px;">
          لم يتم تأكيد هوية المتحدث
        </div>

        <div>
          لم يحقق المقطع حد المطابقة مع الأصوات المرجعية الموثوقة.
        </div>

        <div style="margin-top:8px;">
          أعلى مؤشر تشابه:
          <strong>${percentage}%</strong>
        </div>

        <div style="color:var(--muted);font-size:12px;margin-top:8px;">
          لا يعني ذلك أن الصوت مزيف؛ الهوية فقط غير مؤكدة.
        </div>
      `;
    }
  } catch (error) {
    resultBox.textContent =
      error.message ||
      "حدث خطأ أثناء التحقق من الصوت.";
  } finally {
    button.disabled = false;
    button.textContent = "تحقق من هوية المتحدث";
  }
}

document.addEventListener("DOMContentLoaded", () => {
  const candidate =
    document.getElementById("speaker-candidate");

  const button =
    document.getElementById("verifySpeakerBtn");

  candidate?.addEventListener("change", () => {
    const label =
      document.getElementById(
        "speaker-candidate-picker"
      );

    if (label && candidate.files?.[0]) {
      label.textContent =
        `✓ ${candidate.files[0].name}`;
    }
  });

  button?.addEventListener(
    "click",
    verifySpeakerFromUI
  );
});

// Preview uploaded speaker audio
document.addEventListener("DOMContentLoaded", () => {
  const setupAudioPreview = (inputId, playerId) => {
    const input = document.getElementById(inputId);
    const player = document.getElementById(playerId);

    input?.addEventListener("change", () => {
      const file = input.files?.[0];

      if (!file || !player) return;

      if (player.dataset.objectUrl) {
        URL.revokeObjectURL(player.dataset.objectUrl);
      }

      const objectUrl = URL.createObjectURL(file);

      player.dataset.objectUrl = objectUrl;
      player.src = objectUrl;
      player.style.display = "block";
    });
  };
setupAudioPreview(
    "speaker-candidate",
    "speaker-candidate-player"
  );
});
