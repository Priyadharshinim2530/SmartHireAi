// ---------------------------------------------------------------------
// Match gauge: semicircular ATS-score dial. This is the signature visual
// element reused across the whole app wherever a score is shown.
// Usage: <div class="match-gauge" data-score="78" data-size="140"></div>
// ---------------------------------------------------------------------
function renderMatchGauge(el) {
  const targetScore = Math.max(0, Math.min(100, parseFloat(el.dataset.score || "0")));
  const size = parseInt(el.dataset.size || "140", 10);
  const caption = el.dataset.caption || "ATS match";
  const shouldAnimate = el.dataset.animate === "true" || true;

  const w = size;
  const h = size * 0.62;
  const cx = w / 2;
  const cy = h - 2;
  const r = w / 2 - 12;

  const trackStart = polarToCartesian(cx, cy, r, 0);
  const trackEnd = polarToCartesian(cx, cy, r, 180);

  function polarToCartesian(cx, cy, r, angleDeg) {
    const a = ((angleDeg - 180) * Math.PI) / 180.0;
    return { x: cx + r * Math.cos(a), y: cy + r * Math.sin(a) };
  }

  function drawGauge(currentScore) {
    const color = currentScore >= 75 ? "#2F6B45" : currentScore >= 50 ? "#C97F1E" : "#B3462C";
    const startAngle = 0;
    const endAngle = 180 * (currentScore / 100);
    const start = polarToCartesian(cx, cy, r, startAngle);
    const end = polarToCartesian(cx, cy, r, endAngle);
    const largeArc = endAngle - startAngle <= 180 ? 0 : 1;

    const svg = `
      <svg viewBox="0 0 ${w} ${h + 6}" width="${w}" height="${h + 6}" role="img" aria-label="ATS match score ${targetScore} out of 100">
        <path d="M ${trackStart.x} ${trackStart.y} A ${r} ${r} 0 0 1 ${trackEnd.x} ${trackEnd.y}"
              fill="none" stroke="#DEDACD" stroke-width="12" stroke-linecap="round"/>
        <path d="M ${start.x} ${start.y} A ${r} ${r} 0 ${largeArc} 1 ${end.x} ${end.y}"
              fill="none" stroke="${color}" stroke-width="12" stroke-linecap="round"/>
        <text x="${cx}" y="${cy - r / 2.4}" text-anchor="middle" class="match-gauge-score" style="font-size:${size * 0.16}px">${Math.round(currentScore)}</text>
      </svg>
      <div class="match-gauge-caption">${caption}</div>
    `;
    el.innerHTML = svg;
  }

  if (!shouldAnimate || targetScore === 0) {
    drawGauge(targetScore);
  } else {
    let startTime = null;
    const duration = 1200; // 1.2s

    function animate(timestamp) {
      if (!startTime) startTime = timestamp;
      const elapsed = timestamp - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const ease = 1 - Math.pow(1 - progress, 3); // Cubic ease-out
      const currentScore = ease * targetScore;
      drawGauge(currentScore);

      if (progress < 1) {
        requestAnimationFrame(animate);
      } else {
        drawGauge(targetScore);
      }
    }
    requestAnimationFrame(animate);
  }
}

function renderAllGauges() {
  document.querySelectorAll(".match-gauge").forEach(renderMatchGauge);
}

function getPasswordStrength(password) {
  if (!password) {
    return { label: "Use at least 10 characters, including uppercase, lowercase, numbers, and symbols.", color: "var(--muted)" };
  }
  let score = 0;
  if (password.length >= 10) score += 1;
  if (/[a-z]/.test(password)) score += 1;
  if (/[A-Z]/.test(password)) score += 1;
  if (/[0-9]/.test(password)) score += 1;
  if (/[^A-Za-z0-9]/.test(password)) score += 1;

  if (score <= 2) {
    return { label: "Weak password — add more length, cases, numbers, and symbols.", color: "var(--danger)" };
  }
  if (score === 3 || score === 4) {
    return { label: "Fair password — one more improvement will make it stronger.", color: "var(--amber-deep)" };
  }
  return { label: "Strong password — this password is ready to protect your account.", color: "var(--success)" };
}

function attachPasswordStrength() {
  document.querySelectorAll(".password-strength").forEach((strengthContainer) => {
    const wrapper = strengthContainer.closest(".password-wrapper");
    if (!wrapper) return;
    const input = wrapper.querySelector("input[type='password']");
    if (!input) return;

    const update = () => {
      const { label, color } = getPasswordStrength(input.value);
      strengthContainer.textContent = label;
      strengthContainer.style.color = color;
    };

    input.addEventListener("input", update);
    update();
  });
}

document.addEventListener("DOMContentLoaded", () => {
  renderAllGauges();

  // ── Multi-palette theme switcher ─────────────────────────────
  const PALETTES = [
    { id: 'emerald', label: '🌿 Emerald & Amber' },
    { id: 'ocean',   label: '🌊 Midnight Ocean'  },
    { id: 'rose',    label: '🌸 Sunset Rose'      },
    { id: 'violet',  label: '✨ Deep Violet'       },
  ];

  function showThemeToast(label) {
    let toast = document.getElementById('theme-toast');
    if (!toast) {
      toast = document.createElement('div');
      toast.id = 'theme-toast';
      toast.style.cssText = `
        position:fixed; bottom:24px; left:50%; transform:translateX(-50%) translateY(20px);
        background:var(--card); color:var(--graphite); border:1.5px solid var(--line);
        border-radius:999px; padding:10px 20px; font-size:14px; font-weight:600;
        box-shadow:var(--shadow-card); z-index:9999; opacity:0;
        transition:opacity 0.3s ease, transform 0.3s ease;
        font-family:var(--font-body); white-space:nowrap;
      `;
      document.body.appendChild(toast);
    }
    toast.textContent = label;
    setTimeout(() => {
      toast.style.opacity = '1';
      toast.style.transform = 'translateX(-50%) translateY(0)';
    }, 10);
    clearTimeout(toast._timer);
    toast._timer = setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateX(-50%) translateY(20px)';
    }, 2000);
  }

  const themeToggle = document.getElementById('theme-toggle');
  if (themeToggle) {
    const currentTheme = localStorage.getItem('recruitai-theme') || 'emerald';
    const currentIdx = PALETTES.findIndex(p => p.id === currentTheme);
    let paletteIdx = currentIdx >= 0 ? currentIdx : 0;

    themeToggle.addEventListener('click', () => {
      paletteIdx = (paletteIdx + 1) % PALETTES.length;
      const next = PALETTES[paletteIdx];
      document.documentElement.setAttribute('data-theme', next.id);
      localStorage.setItem('recruitai-theme', next.id);
      showThemeToast(next.label);
    });
  }

  // Premium card hover effect tracker
  const premiumCard = document.querySelector(".premium-card");
  if (premiumCard) {
    premiumCard.addEventListener("mousemove", (e) => {
      const rect = premiumCard.getBoundingClientRect();
      const x = ((e.clientX - rect.left) / rect.width) * 100;
      const y = ((e.clientY - rect.top) / rect.height) * 100;
      premiumCard.style.setProperty("--mouse-x", `${x}%`);
      premiumCard.style.setProperty("--mouse-y", `${y}%`);
    });
  }

  // Auto-dismiss flash messages
  document.querySelectorAll(".flash").forEach((el) => {
    setTimeout(() => {
      el.style.transition = "opacity .4s ease";
      el.style.opacity = "0";
      setTimeout(() => el.remove(), 400);
    }, 4500);
  });

  // Signup role toggle
  document.querySelectorAll(".role-option").forEach((opt) => {
    opt.addEventListener("click", () => {
      document.querySelectorAll(".role-option").forEach((o) => o.classList.remove("selected"));
      opt.classList.add("selected");
      opt.querySelector("input").checked = true;
    });
  });

  attachPasswordStrength();

  // Resume builder: add/remove work history rows
  const addBtn = document.getElementById("add-work-row");
  if (addBtn) {
    addBtn.addEventListener("click", () => {
      const container = document.getElementById("work-history-rows");
      const row = document.createElement("div");
      row.className = "repeat-row";
      row.innerHTML = `
        <button type="button" class="remove-row">Remove</button>
        <label>Job title</label>
        <input type="text" name="job_title[]" placeholder="Software Engineer">
        <label>Company</label>
        <input type="text" name="job_company[]" placeholder="Acme Corp">
        <label>Duration</label>
        <input type="text" name="job_duration[]" placeholder="Jan 2022 – Present">
        <label>Description</label>
        <textarea name="job_description[]" placeholder="What did you build or own in this role?"></textarea>
      `;
      container.appendChild(row);
    });
  }

  document.body.addEventListener("click", (e) => {
    if (e.target.classList.contains("remove-row")) {
      e.target.closest(".repeat-row").remove();
    }

    const toggleBtn = e.target.closest(".password-toggle");
    if (toggleBtn) {
      const wrapper = toggleBtn.closest(".password-wrapper");
      const input = wrapper.querySelector("input");
      const eyeOpen = toggleBtn.querySelector(".eye-open");
      const eyeClosed = toggleBtn.querySelector(".eye-closed");

      if (input.type === "password") {
        input.type = "text";
        eyeOpen.style.display = "block";
        eyeClosed.style.display = "none";
      } else {
        input.type = "password";
        eyeOpen.style.display = "none";
        eyeClosed.style.display = "block";
      }
    }
  });
});
/**
 * SmartHireAI Global Preloader Dismiss Logic
 * Keep the centered logo visible for 30 seconds, then fade it out and reveal the page.
 */
const preloader = document.getElementById('preloader');
const body = document.body;

if (preloader) {
  let isFirstVisit = false;
  try {
    const storage = window.sessionStorage;
    isFirstVisit = !storage.getItem('recruitai-preloader-shown');
    if (isFirstVisit) {
      storage.setItem('recruitai-preloader-shown', 'true');
    }
  } catch (error) {
    // If sessionStorage access is blocked, fallback to localStorage for duration tracking.
    try {
      const storage = window.localStorage;
      isFirstVisit = !storage.getItem('recruitai-preloader-shown');
      if (isFirstVisit) {
        storage.setItem('recruitai-preloader-shown', 'true');
      }
    } catch (nestedError) {
      isFirstVisit = true;
    }
  }

  const hidePreloader = () => {
    preloader.style.opacity = '0';
    preloader.style.visibility = 'hidden';

    setTimeout(() => {
      preloader.style.display = 'none';
      body.classList.remove('preloader-active');
    }, 500);
  };

  if (isFirstVisit) {
    setTimeout(hidePreloader, 10000);
  } else {
    hidePreloader();
  }
}
