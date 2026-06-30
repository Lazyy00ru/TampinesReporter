/**
 * base.js — Shared Navbar
 *
 * HOW TO USE
 * ──────────────────────────────────────────────────
 * Drop this ONE line in your <head> (before your own CSS):
 *
 *   <script src="/base.js"
 *           data-page="home"
 *           data-title="Agency Home"
 *           data-sub="Case Management · Tampines Estate">
 *   </script>
 *
 * data-page values: "home" | "cases" | "profile"
 *
 * What gets injected:
 *   · Inter font <link>
 *   · <style id="base-navbar-css"> — all shared CSS tokens + header + bottom-nav
 *   · <header class="b-header"> — sticky top bar
 *   · <nav class="b-bottom-nav"> — mobile bottom tabs (hidden at ≥900px)
 *   · Agency name + icon from sessionStorage.agency_session
 */

(function () {
  /* ── 1. Read config from the <script> tag that loaded this file ── */
  const me = document.currentScript ||
    (function () {
      const tags = document.getElementsByTagName('script');
      return tags[tags.length - 1];
    })();

  const PAGE  = (me && me.getAttribute('data-page'))  || 'home';
  const TITLE = (me && me.getAttribute('data-title')) || 'Agency';
  const SUB   = (me && me.getAttribute('data-sub'))   || '';

  /* ── 2. Inject Inter font ── */
  if (!document.querySelector('link[href*="fonts.googleapis.com/css2?family=Inter"]')) {
    const fontLink = document.createElement('link');
    fontLink.rel  = 'stylesheet';
    fontLink.href = 'https://fonts.googleapis.com/css2?family=Inter:opsz,wght@14..32,300;14..32,400;14..32,500;14..32,600;14..32,700;14..32,800;14..32,900&display=swap';
    document.head.appendChild(fontLink);
  }
  /* Inject Font Awesome icons */
if (!document.querySelector('link[href*="font-awesome"]')) {
  const faLink = document.createElement('link');
  faLink.rel = 'stylesheet';
  faLink.href = 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.2/css/all.min.css';
  document.head.appendChild(faLink);
}
  /* ── 3. Inject shared CSS ── */
  if (!document.getElementById('base-navbar-css')) {
    const style = document.createElement('style');
    style.id = 'base-navbar-css';
    style.textContent = `

    .b-hdr-logo{
  width: 100%;
  height: 100%;
  object-fit: contain;
  display: block;
  background: transparent;
}

/* ════════════════════════════════════════════
   BASE DESIGN TOKENS  — use var(--b-*) anywhere
   ════════════════════════════════════════════ */
:root {
  --b-font:      'Inter', system-ui, -apple-system, 'Segoe UI', Roboto, Helvetica, sans-serif;

  --b-white:     #ffffff;
  --b-surface:   #e6fbff;

  --b-border:    #b8edf3;
  --b-border2:   #89d6df;

  --b-text:      #073b47;
  --b-text2:     #003747;

  --b-muted:     #4f7f87;
  --b-muted2:    #78aeb6;

  --b-navy:      #00b7eb;
  --b-navy-lt:   #d9fbff;
  --b-navy-mid:  #007a99;

  --b-hdr-h:     68px;
  --b-bnav-h:    calc(58px + env(safe-area-inset-bottom));
  --b-r:         12px;
}

/* ════════════════════════════════════════════
   TOP HEADER
   ════════════════════════════════════════════ */
.b-header {
  background: linear-gradient(135deg, #dff8ff, #bfefff);
  padding: 0 24px;
  height: 68px;
  display: flex;
  align-items: center;
  gap: 14px;
  position: sticky;
  top: 0;
  left: 0;
  right: 0;
  width: 100%;
  z-index: 1000;
  border-bottom: 1px solid #9edfea;
  box-shadow: 0 1px 0 rgba(0,0,0,0.02);
  box-sizing: border-box;
}

.b-hdr-icon {
  width: 58px;
  height: 58px;
  border-radius: 16px;
  overflow: hidden;
  flex-shrink: 0;

  display: flex;
  align-items: center;
  justify-content: center;

  background: transparent;
  border: none;
  padding: 0;
}
.b-hdr-icon:hover { transform: scale(1.06); }

.b-hdr-brand { flex: 1; min-width: 0; }

.b-hdr-name {
  font-family: var(--b-font);
  font-size: 17px;
  font-weight: 800;
  color: #003747;;
  line-height: 1.2;
  letter-spacing: -0.02em;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.b-hdr-name span { color: #00556b; font-weight: 700; }

.b-hdr-sub {
  font-family: var(--b-font);
  font-size: 10px;
  font-weight: 600;
  color: #6B7A8F;
  text-transform: uppercase;
  letter-spacing: 0.4px;
  margin-top: 2px;
}

/* Desktop nav pills */
.b-hdr-nav {
  display: none;
  gap: 2px;
  background: rgba(255,255,255,0.78);
  padding: 4px;
  border-radius: 999px;
  border: 1px solid rgba(255,255,255,0.9);
  box-shadow: 0 8px 24px rgba(0, 55, 71, 0.08);
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
}

.b-navbtn {
  background: transparent;
  border: none;
  padding: 8px 12px;
  font-family: var(--b-font);
  font-weight: 700;
  font-size: 13px;
  color: #5f6f82;
  border-radius: 999px;
  cursor: pointer;
  transition: all 0.2s ease;
  white-space: nowrap;
}
.b-navbtn i {
  margin-right: 5px;
  font-size: 12px;
}
.b-navbtn:hover {
  background: rgba(0,183,235,0.10);
  color: #003747;
}

.b-navbtn.b-active {
  background: #e9ffff;
  color: #009c9a;
  box-shadow: inset 0 0 0 1px rgba(0,183,235,0.12);
}

/* Sign Out button */
.b-logout {
  width: 46px;
  height: 46px;
  border-radius: 50%;
  border: 1px solid rgba(255,255,255,0.9);
  background: rgba(255,255,255,0.82);
  color: #5f6f82;
  cursor: pointer;
  transition: all 0.2s ease;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8px 20px rgba(0, 55, 71, 0.08);
}

.b-logout:hover {
  background: #ffffff;
  color: #003747;
  transform: translateY(-1px);
}

/* ════════════════════════════════════════════
   MOBILE BOTTOM NAV
   ════════════════════════════════════════════ */
.b-bottom-nav {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: rgba(240,252,255,0.96);
  border-top: 1px solid #b8edf3;
  backdrop-filter: blur(18px);
  backdrop-filter: blur(18px);
  -webkit-backdrop-filter: blur(18px);
  border-top: 1px solid #E9EDF2;
  display: flex;
  align-items: center;
  justify-content: space-around;
  padding: 8px 16px calc(10px + env(safe-area-inset-bottom));
  z-index: 900;
  box-shadow: 0 -4px 12px rgba(0,0,0,0.02);
}

.b-bnav-btn {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  background: none;
  border: none;
  font-family: var(--b-font);
  font-size: 11px;
  font-weight: 600;
  color: #8E9BB0;
  cursor: pointer;
  border-radius: 30px;
  padding: 8px 6px;
  transition: all 0.2s;
  -webkit-tap-highlight-color: transparent;
}
.b-bnav-btn svg {
  width: 22px;
  height: 22px;
  stroke: #8E9BB0;
  stroke-width: 1.8;
  fill: none;
  transition: all 0.2s;
}
.b-bnav-btn.b-active       { background: rgba(0,183,235,0.12); color: #003747; font-weight: 700; }
.b-bnav-btn.b-active svg   { stroke: #1A3A6B; stroke-width: 2.2; }
.b-bnav-btn.b-active span  { font-weight: 800; }

/* ════════════════════════════════════════════
   DESKTOP (≥ 900px)
   ════════════════════════════════════════════ */
@media (min-width: 900px) {
  .b-header        { padding: 0 32px; }
  .b-hdr-nav       { display: flex; }
  .b-bottom-nav    { display: none; }
}

/* ════════════════════════════════════════════
   AI FLOATING BUTTON
   ════════════════════════════════════════════ */
.b-ai-fab {
  position: fixed;
  bottom: calc(70px + env(safe-area-inset-bottom));
  right: 16px;
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: linear-gradient(135deg, #00c8ff 0%, #007fa8 100%);
  border: 2px solid rgba(255,255,255,0.75);
  cursor: pointer;
  z-index: 800;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow:
    0 0 0 8px rgba(0,183,235,0.14),
    0 0 28px rgba(0,183,235,0.65),
    0 12px 30px rgba(0,55,71,0.32);
  transition: transform 0.2s, box-shadow 0.2s;
  animation: b-ai-fab-breathe 1.7s ease-in-out infinite;
  -webkit-tap-highlight-color: transparent;
  outline: none;
}
.b-ai-fab:hover {
  transform: scale(1.1);
  box-shadow:
    0 0 0 10px rgba(0,183,235,0.18),
    0 0 38px rgba(0,183,235,0.85),
    0 14px 34px rgba(0,55,71,0.38);
}

.b-ai-fab:active {
  transform: scale(0.95);
}

.b-ai-fab-icon {
  font-size: 30px;
  line-height: 1;
  color: #001f2a;
  text-shadow:
    0 0 8px rgba(255,255,255,0.9),
    0 0 18px rgba(255,255,255,0.65);
  animation: b-ai-star-pop 1.15s ease-in-out infinite;
}

.b-ai-fab.b-ai-open .b-ai-fab-icon {
  transform: rotate(20deg) scale(0.9);
}

/* stronger repeated pulse rings */
.b-ai-fab::before,
.b-ai-fab::after {
  content: '';
  position: absolute;
  inset: -8px;
  border-radius: 50%;
  border: 3px solid rgba(0,183,235,0.65);
  animation: b-ai-ring 1.55s ease-out infinite;
  pointer-events: none;
}
.b-ai-fab::after {
  inset: -15px;
  border-color: rgba(0,149,200,0.38);
  animation-delay: 0.45s;
}

@keyframes b-ai-ring {
  0% {
    transform: scale(0.78);
    opacity: 0.95;
  }
  70% {
    transform: scale(1.45);
    opacity: 0;
  }
  100% {
    transform: scale(1.45);
    opacity: 0;
  }
}
@keyframes b-ai-fab-breathe {
  0%, 100% {
    transform: translateY(0) scale(1);
  }
  50% {
    transform: translateY(-4px) scale(1.04);
  }
}


@keyframes b-ai-star-pop {
  0%, 100% {
    transform: scale(1) rotate(0deg);
  }
  45% {
    transform: scale(1.28) rotate(12deg);
  }
}

@media (min-width: 900px) {
  .b-ai-fab {
    bottom: 30px;
    right: 28px;
    width: 72px;
    height: 72px;
  }

  .b-ai-fab-icon {
    font-size: 34px;
  }
}

/* Unread badge */
.b-ai-badge {
  position: absolute;
  top: 2px; right: 2px;
  width: 14px; height: 14px;
  border-radius: 50%;
  background: #ef4444;
  border: 2px solid #fff;
  display: none;
}
.b-ai-badge.show { display: block; }

@media (min-width: 900px) {
  .b-ai-fab {
    bottom: 28px;
    right: 28px;
    width: 56px;
    height: 56px;
  }
}

/* ════════════════════════════════════════════
   AI CHAT DRAWER
   ════════════════════════════════════════════ */
.b-ai-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0);
  z-index: 940;
  pointer-events: none;
  transition: background 0.3s;
}
.b-ai-backdrop.open {
  background: rgba(0,0,0,0.25);
  pointer-events: auto;
}

.b-ai-drawer {
  position: fixed;
  bottom: calc(58px + env(safe-area-inset-bottom));
  left: 0; right: 0;
  height: calc(100dvh - 68px - 58px - env(safe-area-inset-bottom));
  max-height: calc(100dvh - 68px - 58px - env(safe-area-inset-bottom));
  background: #ffffff;
  border-radius: 20px 20px 0 0;
  z-index: 950;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  transform: translateY(110%);
  transition: transform 0.38s cubic-bezier(0.32, 0.72, 0, 1);
  box-shadow: 0 -8px 40px rgba(0,0,0,0.15);
}
.b-ai-drawer.open { transform: translateY(0); }

@media (min-width: 900px) {
  .b-ai-drawer {
    left: auto;
    right: 28px;
    bottom: 95px;
    width: 420px;
    max-width: calc(100vw - 56px);
    height: 560px;
    max-height: calc(100vh - 150px);
    border-radius: 16px;
    transform: translateY(20px) scale(0.96);
    opacity: 0;
    transition: transform 0.28s cubic-bezier(0.32, 0.72, 0, 1), opacity 0.28s;
  }
  .b-ai-drawer.open {
    transform: translateY(0) scale(1);
    opacity: 1;
  }
  .b-ai-backdrop.open { background: transparent; }
}

/* Drawer handle (mobile) */
.b-ai-handle {
  width: 36px; height: 4px;
  background: #e0e0e0;
  border-radius: 2px;
  margin: 10px auto 0;
  flex-shrink: 0;
}
@media (min-width: 900px) { .b-ai-handle { display: none; } }

/* Drawer header */
.b-ai-dhead {
  display: flex; align-items: center; gap: 10px;
  padding: 12px 16px 10px;
  border-bottom: 1px solid #e8e6e1;
  flex-shrink: 0;
}
.b-ai-dhead-avatar {
  width: 36px; height: 36px; border-radius: 50%;
  background: linear-gradient(135deg, #00b7eb, #0095c8);
  display: flex; align-items: center; justify-content: center;
  font-size: 18px; flex-shrink: 0;
  box-shadow: 0 2px 8px rgba(26,58,107,0.3);
}
.b-ai-dhead-info { flex: 1; min-width: 0; }
.b-ai-dhead-title {
  font-family: var(--b-font);
  font-size: 14px; font-weight: 800;
  color: #0B1A33; letter-spacing: -0.02em;
}
.b-ai-dhead-title span { color: #2C3E6D; }
.b-ai-dhead-sub {
  font-size: 10px; font-weight: 600;
  color: #6B7A8F; text-transform: uppercase; letter-spacing: 0.8px;
  margin-top: 1px;
}
.b-ai-dhead-status {
  display: flex; align-items: center; gap: 5px;
  background: #f0fdf4; border: 1px solid #bbf7d0;
  border-radius: 20px; padding: 4px 9px; flex-shrink: 0;
}
.b-ai-dhead-dot {
  width: 6px; height: 6px; border-radius: 50%;
  background: #16a34a;
  animation: b-pulse 2s infinite;
}
.b-ai-dhead-status span { font-size: 10px; font-weight: 700; color: #15803d; }
.b-ai-close {
  width: 28px; height: 28px; border-radius: 50%;
  background: #f5f4f1; border: 1px solid #e8e6e1;
  display: flex; align-items: center; justify-content: center;
  cursor: pointer; font-size: 13px; color: #79776e;
  flex-shrink: 0; transition: background 0.15s;
  font-family: var(--b-font);
}
.b-ai-close:hover { background: #e8e6e1; color: #111110; }

/* Quick chips */
.b-ai-chips {
  display: flex; gap: 6px; padding: 6px 12px;
  overflow-x: auto; scrollbar-width: none;
  border-bottom: 1px solid #e8e6e1; flex-shrink: 0;
  background: #fafaf9;
}
.b-ai-chips::-webkit-scrollbar { display: none; }

/* On short mobile screens, hide chips to save space */
@media (max-height: 650px) {
  .b-ai-chips { display: none; }
  .b-ai-datastrip { display: none; }
  .b-ai-handle { margin: 6px auto 0; }
}
.b-ai-chip {
  display: flex; align-items: center; gap: 4px;
  background: #ffffff; border: 1px solid #e8e6e1;
  border-radius: 20px; padding: 5px 11px;
  font-family: var(--b-font);
  font-size: 11px; font-weight: 600; color: #111110;
  white-space: nowrap; flex-shrink: 0; cursor: pointer;
  transition: all 0.15s;
}
.b-ai-chip i {
  font-size: 11px;
  margin-right: 4px;
}

.b-ai-welcome-cap i {
  margin-right: 4px;
}
.b-ai-chip:hover { background: #00b7eb; border-color: #00b7eb; color: #fff; }

/* Messages */
.b-ai-msgs {
  flex: 1; min-height: 0; overflow-y: auto; overflow-x: hidden;
  padding: 14px 13px 8px;
  scroll-behavior: smooth;
  -webkit-overflow-scrolling: touch;
}
.b-ai-msg { margin-bottom: 13px; display: flex; flex-direction: column; }
.b-ai-msg.user { align-items: flex-end; }
.b-ai-msg.ai   { align-items: flex-start; }

.b-ai-row { display: flex; align-items: flex-end; gap: 7px; max-width: 100%; }
.b-ai-ava {
  width: 26px; height: 26px; border-radius: 50%;
  background: #00b7eb; display: flex; align-items: center;
  justify-content: center; font-size: 12px; flex-shrink: 0;
  box-shadow: 0 2px 6px rgba(26,58,107,0.25);
}
.b-ai-bubble {
  padding: 9px 13px; border-radius: 14px;
  font-family: var(--b-font); font-size: 13px; line-height: 1.55;
  word-break: break-word; max-width: 100%;
}
.b-ai-bubble.user {
  background: linear-gradient(135deg, #00b7eb, #0095c8);
  color: #fff;
  border-bottom-right-radius: 3px; max-width: 82%;
}
.b-ai-bubble.ai {
  background: #f8fdff;
  color: #0b1a33;
  border: 1px solid #b8edf3;
  border-bottom-left-radius: 3px;
}
.b-ai-bubble.ai strong { font-weight: 700; color: #0095c8; }
.b-ai-bubble.ai p { margin-bottom: 6px; }
.b-ai-bubble.ai p:last-child { margin-bottom: 0; }
.b-ai-bubble.ai ul { padding-left: 16px; margin: 4px 0; }
.b-ai-bubble.ai li { margin-bottom: 3px; }
.b-ai-time {
  font-size: 9px; font-weight: 600; color: #a8a39a;
  margin-top: 3px; letter-spacing: 0.4px;
}
.b-ai-msg.user .b-ai-time { text-align: right; margin-right: 2px; }
.b-ai-msg.ai  .b-ai-time  { margin-left: 33px; }

/* Typing dots */
.b-ai-typing {
  display: flex; gap: 4px; align-items: center;
  padding: 10px 13px;
  background: #f8fdff; border: 1px solid #c7d4f5;
  border-radius: 14px; border-bottom-left-radius: 3px;
}
.b-ai-typing span {
  width: 6px; height: 6px; border-radius: 50%;
  background: #00b7eb; opacity: 0.35;
  animation: b-tdot 1.2s infinite;
}
.b-ai-typing span:nth-child(2) { animation-delay: 0.18s; }
.b-ai-typing span:nth-child(3) { animation-delay: 0.36s; }
@keyframes b-tdot {
  0%,80%,100% { opacity:.2; transform:scale(.65); }
  40%          { opacity:1;  transform:scale(1); }
}

/* Welcome card */
.b-ai-welcome {
  background: linear-gradient(135deg, #00b7eb 0%, #0095c8 100%);
  border-radius: 12px; padding: 16px 14px; margin-bottom: 14px; color: #fff;
}
.b-ai-welcome-title {
  font-family: var(--b-font);
  font-size: 14px; font-weight: 800; line-height: 1.25; margin-bottom: 6px;
}
.b-ai-welcome-body { font-size: 11px; opacity: 0.72; line-height: 1.55; }
.b-ai-welcome-caps { display: flex; flex-wrap: wrap; gap: 5px; margin-top: 10px; }
.b-ai-welcome-cap {
  background: rgba(255,255,255,0.12); border: 1px solid rgba(255,255,255,0.18);
  border-radius: 5px; padding: 3px 8px;
  font-size: 10px; font-weight: 600; color: rgba(255,255,255,0.88);
}

/* Mini chart card */
.b-ai-chart-card {
  background: #fff; border: 1px solid #e8e6e1;
  border-radius: 9px; padding: 12px; margin-top: 10px; overflow: hidden;
}
.b-ai-chart-title {
  font-size: 10px; font-weight: 700; text-transform: uppercase;
  letter-spacing: 0.8px; color: #79776e; margin-bottom: 10px;
}

/* Agency table */
.b-ai-tbl { width: 100%; border-collapse: collapse; font-size: 11px; }
.b-ai-tbl th {
  font-size: 8px; font-weight: 700; text-transform: uppercase;
  letter-spacing: 0.8px; color: #79776e; padding: 4px 6px;
  text-align: left; border-bottom: 1px solid #e8e6e1;
}
.b-ai-tbl td { padding: 6px 6px; border-bottom: 1px solid #f5f4f1; vertical-align: middle; }
.b-ai-tbl tr:last-child td { border-bottom: none; }
.b-ai-sla {
  display: inline-block; border-radius: 20px; padding: 2px 7px;
  font-size: 9px; font-weight: 700;
}
.b-ai-sla.fast { background: #dcfce7; color: #15803d; }
.b-ai-sla.med  { background: #fef3c7; color: #b45309; }
.b-ai-sla.slow { background: #fee2e2; color: #b91c1c; }

/* Input bar */
.b-ai-inputbar {
  padding: 9px 11px calc(9px + env(safe-area-inset-bottom));
  border-top: 1px solid #e8e6e1; flex-shrink: 0;
  background: #fff;
  position: sticky;
  bottom: 0;
  z-index: 5;
}
.b-ai-inputrow { display: flex; gap: 7px; align-items: flex-end; }
.b-ai-inputbox {
  flex: 1; display: flex; align-items: flex-end;
  background: #f5f4f1; border: 1.5px solid #e8e6e1;
  border-radius: 18px; padding: 6px 12px;
  transition: border-color 0.15s;
}
.b-ai-inputbox:focus-within {
  border-color: #00b7eb;
  box-shadow: 0 0 0 3px rgba(0,183,235,0.12);
}
.b-ai-textarea {
  flex: 1; background: none; border: none; outline: none; resize: none;
  font-family: var(--b-font); font-size: 13px; color: #111110;
  line-height: 1.45; max-height: 100px; overflow-y: auto;
  padding: 3px 0; scrollbar-width: none;
}
.b-ai-textarea::-webkit-scrollbar { display: none; }
.b-ai-textarea::placeholder { color: #a8a39a; }
.b-ai-sendbtn {
  width: 36px; height: 36px; border-radius: 50%;
  background: linear-gradient(135deg, #00b7eb, #0095c8);border: none; cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0; transition: all 0.15s;
}
.b-ai-sendbtn:hover  {
  background: linear-gradient(135deg, #00c8ff, #00a6db);
  transform: scale(1.06);
}
.b-ai-sendbtn:active { transform: scale(0.93); }
.b-ai-sendbtn:disabled { background: #e8e6e1; cursor: not-allowed; transform: none; }
.b-ai-sendbtn svg { width: 15px; height: 15px; stroke: #fff; stroke-width: 2; fill: none; }

/* Data context strip */
.b-ai-datastrip {
  display: flex; gap: 5px; padding: 6px 12px;
  overflow-x: auto; scrollbar-width: none;
  border-bottom: 1px solid #e8e6e1; flex-shrink: 0; background: #fafaf9;
}
.b-ai-datastrip::-webkit-scrollbar { display: none; }
.b-ai-dchip {
  display: flex; align-items: center; gap: 4px;
  background: #fff; border: 1px solid #e8e6e1;
  border-radius: 6px; padding: 4px 8px;
  font-family: var(--b-font);
  font-size: 10px; font-weight: 700; color: #111110;
  white-space: nowrap; flex-shrink: 0;
}
.b-ai-dchip-dot { width: 5px; height: 5px; border-radius: 50%; }

`;
    document.head.appendChild(style);
  }

  /* ── 4. Nav link definitions ── */
  const NAV_LINKS = [
  {
    key: 'home',
    label: '<i class="fa-solid fa-house"></i> Home',
    href: '/agency_home.html',
    tabLabel: 'Home',
  },
  {
    key: 'cases',
    label: '<i class="fa-solid fa-folder-open"></i> Cases',
    href: '/agency_dashboard.html',
    tabLabel: 'Cases',
  },
  {
    key: 'analytics',
    label: '<i class="fa-solid fa-chart-line"></i> Analytics',
    href: '/agency_analytics.html',
    tabLabel: 'Analytics',
  },
  {
    key: 'workforce',
    label: '<i class="fa-solid fa-users"></i> Workforce',
    href: '/agency_workforce.html',
    tabLabel: 'Workforce',
  },
  {
    key: 'profile',
    label: '<i class="fa-solid fa-user"></i> Profile',
    href: '/agency_profile.html',
    tabLabel: 'Profile',
  },
];

  /* ── 5. Build & insert <header> ── */
  function buildHeader() {
    if (document.getElementById('b-header')) return; // prevent duplicates

    const hdr = document.createElement('header');
    hdr.className = 'b-header';
    hdr.id = 'b-header';

    /* Icon */
    const icon = document.createElement('div');
    icon.className = 'b-hdr-icon';
    icon.id = 'b-hdr-icon';

    icon.innerHTML = `
  <img src="/static/agent_icon.png"
       alt="Zentra Logo"
       class="b-hdr-logo">
`;

hdr.appendChild(icon);

    /* Brand */
    const brand = document.createElement('div');
    brand.className = 'b-hdr-brand';
    brand.innerHTML =
      '<div class="b-hdr-name" id="b-hdr-name">' + TITLE + '</div>' +
      '<div class="b-hdr-sub">' + SUB + '</div>';
    hdr.appendChild(brand);

    /* Desktop nav pills */
    const nav = document.createElement('div');
    nav.className = 'b-hdr-nav';
    NAV_LINKS.forEach(function (link) {
      const btn = document.createElement('button');
      btn.className = 'b-navbtn' + (link.key === PAGE ? ' b-active' : '');
      btn.innerHTML = link.label;
      if (link.key !== PAGE) {
        btn.onclick = function () { window.location.href = link.href; };
      }
      nav.appendChild(btn);
    });
    hdr.appendChild(nav);

    /* Sign Out */
    const signout = document.createElement('button');
    signout.className = 'b-logout';
    signout.id = 'b-logout-btn';
    signout.innerHTML = `
  <svg viewBox="0 0 24 24" width="22" height="22" fill="none">
    <path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
    <path d="M10 17l5-5-5-5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
    <path d="M15 12H3" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
  </svg>
`;
    signout.onclick = function () {
      sessionStorage.removeItem('agency_session');
      window.location.replace('/agency_login.html');
    };
    hdr.appendChild(signout);

    /* Prepend to <body> */
    document.body.insertBefore(hdr, document.body.firstChild);
  }

  /* ── 6. Build & append <nav class="b-bottom-nav"> ── */
  function buildBottomNav() {
    if (document.getElementById('b-bottom-nav')) return;

    const nav = document.createElement('nav');
    nav.className = 'b-bottom-nav';
    nav.id = 'b-bottom-nav';

    NAV_LINKS.forEach(function (link) {
      const btn = document.createElement('button');
      btn.className = 'b-bnav-btn' + (link.key === PAGE ? ' b-active' : '');
      btn.innerHTML =
        '<svg viewBox="0 0 24 24" fill="none">' + link.svgInner + '</svg>' +
        '<span>' + link.tabLabel + '</span>';
      if (link.key !== PAGE) {
        btn.onclick = function () { window.location.href = link.href; };
      }
      nav.appendChild(btn);
    });

    document.body.appendChild(nav);
  }

  /* ── 7. Sync agency icon from sessionStorage (badge removed) ── */
  function syncAgency() {
    try {
      const raw = sessionStorage.getItem('agency_session');
      if (!raw) return;
      const session = JSON.parse(raw);
      if (!session || !session.agency) return;

      const ICONS = {
        'NEA / Town Council':      '♻️',
        'Town Council / HDB':      '🏗️',
        'SP Group / Town Council': '⚡',
        'PUB / Town Council':      '💧',
        'SCDF / HDB / Police':     '🚒',
        'NEA / Police / CMC':      '🚔',
        'NEA / NParks / AVS':      '🌿',
        'LTA / HDB / URA':         '🚗',
        'NParks / Town Council':   '🌳',
      };

      const iconEl  = document.getElementById('b-hdr-icon');
      if (iconEl) {
  iconEl.innerHTML = `
    <img src="/static/agent_icon.png"
         alt="Zentra Logo"
         class="b-hdr-logo">
  `;
}
    } catch (_) {}
  }

  /* ── 8. Build AI floating button + chat drawer ── */
  function buildAIFloat() {
    if (document.getElementById('b-ai-fab')) return;

    /* ── FAB button ── */
    const fab = document.createElement('button');
    fab.id = 'b-ai-fab';
    fab.className = 'b-ai-fab';
    fab.setAttribute('aria-label', 'Open AI Assistant');
    fab.innerHTML = '<span class="b-ai-fab-icon">✦</span><span class="b-ai-badge" id="b-ai-badge"></span>';
    fab.onclick = toggleAIDrawer;
    document.body.appendChild(fab);

    /* ── Backdrop ── */
    const backdrop = document.createElement('div');
    backdrop.id = 'b-ai-backdrop';
    backdrop.className = 'b-ai-backdrop';
    backdrop.onclick = closeAIDrawer;
    document.body.appendChild(backdrop);

    /* ── Drawer ── */
    const drawer = document.createElement('div');
    drawer.id = 'b-ai-drawer';
    drawer.className = 'b-ai-drawer';
    drawer.innerHTML = `
      <div class="b-ai-handle"></div>

      <div class="b-ai-dhead">
        <div class="b-ai-dhead-avatar">✦</div>
        <div class="b-ai-dhead-info">
          <div class="b-ai-dhead-title"><span>AI</span> Intelligence</div>
          <div class="b-ai-dhead-sub">Agency Assistant · Tampines</div>
        </div>
        <div class="b-ai-dhead-status">
          <div class="b-ai-dhead-dot"></div>
          <span>Online</span>
        </div>
        <div class="b-ai-close" onclick="window.__bAiClose()">✕</div>
      </div>

      <div class="b-ai-datastrip">
        <div class="b-ai-dchip"><span class="b-ai-dchip-dot" style="background:#dc2626"></span><span id="b-ai-d-crit">—</span> Critical</div>
        <div class="b-ai-dchip"><span class="b-ai-dchip-dot" style="background:#ea580c"></span><span id="b-ai-d-open">—</span> Open</div>
        <div class="b-ai-dchip"><span class="b-ai-dchip-dot" style="background:#16a34a"></span><span id="b-ai-d-res">—</span> Resolved</div>
        <div class="b-ai-dchip"><span class="b-ai-dchip-dot" style="background:#2563eb"></span><span id="b-ai-d-tot">—</span> Total</div>
      </div>

      <div class="b-ai-chips" id="b-ai-chips">
        <div class="b-ai-chip" onclick="window.__bAiQuick('Which department handles flooding?')"><i class="fa-solid fa-droplet" style="color:#00b7eb"></i> Flooding dept</div>
        <div class="b-ai-chip" onclick="window.__bAiQuick('Show agency case chart')"><i class="fa-solid fa-chart-column" style="color:#8b5cf6"></i> Agency chart</div>
        <div class="b-ai-chip" onclick="window.__bAiQuick('How long to fix a broken lift?')"><i class="fa-solid fa-elevator" style="color:#1591EA"></i> Lift SLA</div>
        <div class="b-ai-chip" onclick="window.__bAiQuick('Summarise open critical cases')"><i class="fa-solid fa-land-mine-on" style="color: red"></i>Critical cases</div>
        <div class="b-ai-chip" onclick="window.__bAiQuick('Show priority breakdown chart')"><i class="fa-solid fa-layer-group" style="color:#8b5cf6"></i> Priority chart</div>
        <div class="b-ai-chip" onclick="window.__bAiQuick('What handles pest issues?')"><i class="fa-solid fa-bug" style="color:#f59e0b"></i> Pest routing</div>
      </div>

      <div class="b-ai-msgs" id="b-ai-msgs">
        <div id="b-ai-welcome" class="b-ai-welcome">
          <div class="b-ai-welcome-title">Ask anything about your estate cases</div>
          <div class="b-ai-welcome-body">I have live access to your database — ask which agency handles a problem, expected SLAs, case summaries, or request a live chart.</div>
          <div class="b-ai-welcome-caps">
            <span class="b-ai-welcome-cap"><i class="fa-solid fa-city" style="color:#ffffff"></i>Agency routing</span>
            <span class="b-ai-welcome-cap"><i class="fa-solid fa-clock" style="color:#ffe082"></i> SLA lookup</span>
            <span class="b-ai-welcome-cap"><i class="fa-solid fa-chart-column" style="color:#ffe082"></i> Agency chart</span>
            <span class="b-ai-welcome-cap"><i class="fa-solid fa-chart-column" style="color:#c4b5fd"></i>Live charts</span>
            <span class="b-ai-welcome-cap"><i class="fa-solid fa-magnifying-glass-chart" style="color:#c4b5fd"></i> Case analysis</span>
          </div>
        </div>
        <div id="b-ai-msglist"></div>
      </div>

      <div class="b-ai-inputbar">
        <div class="b-ai-inputrow">
          <div class="b-ai-inputbox">
            <textarea class="b-ai-textarea" id="b-ai-textarea" rows="1"
              placeholder="Ask about agencies, SLAs, cases…"
              onkeydown="window.__bAiKey(event)"
              oninput="window.__bAiResize(this)"></textarea>
          </div>
          <button class="b-ai-sendbtn" id="b-ai-sendbtn" onclick="window.__bAiSend()">
            <svg viewBox="0 0 24 24"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
          </button>
        </div>
      </div>
    `;
    document.body.appendChild(drawer);

    /* ── AI state ── */
    var aiConvo    = [];
    var aiLoading  = false;
    var aiAnalytics = null;
    var aiLiveCases = [];
    var aiChartCount = 0;

    /* ── Agency routing table (embedded for instant answers) ── */
    var AI_ROUTING = {
      plastic_litter:{agency:'NEA',sla:'24 hours',category:'cleanliness'},
      food_waste:{agency:'NEA',sla:'24 hours',category:'cleanliness'},
      overflowing_bin:{agency:'NEA',sla:'4 hours',category:'cleanliness'},
      illegal_dump:{agency:'NEA',sla:'24 hours',category:'cleanliness'},
      bulky_item:{agency:'NEA',sla:'48 hours',category:'cleanliness'},
      broken_pipe:{agency:'Town Council',sla:'4 hours',category:'structural'},
      broken_wire:{agency:'Town Council',sla:'4 hours',category:'structural'},
      lift_fault:{agency:'Town Council',sla:'4 hours',category:'structural'},
      broken_drain:{agency:'Town Council',sla:'24 hours',category:'structural'},
      broken_playground:{agency:'Town Council',sla:'24 hours',category:'structural'},
      road_crack:{agency:'Town Council',sla:'3 working days',category:'structural'},
      footpath_crack:{agency:'Town Council',sla:'3 working days',category:'structural'},
      streetlight_fault:{agency:'Town Council',sla:'24 hours',category:'electrical'},
      carpark_light:{agency:'Town Council',sla:'24 hours',category:'electrical'},
      flooding:{agency:'PUB',sla:'IMMEDIATE',category:'water'},
      choked_drain:{agency:'PUB',sla:'4 hours',category:'water'},
      manhole_overflow:{agency:'PUB',sla:'4 hours',category:'water'},
      ceiling_leak:{agency:'PUB',sla:'24 hours',category:'water'},
      stagnant_water:{agency:'PUB',sla:'24 hours',category:'water'},
      blocked_exit:{agency:'SCDF',sla:'IMMEDIATE',category:'safety'},
      fire_hazard:{agency:'SCDF',sla:'IMMEDIATE',category:'safety'},
      fallen_tree:{agency:'NParks',sla:'4 hours',category:'safety'},
      graffiti:{agency:'Police',sla:'3 working days',category:'safety'},
      renovation_noise:{agency:'Police',sla:'2 working days',category:'noise'},
      neighbour_noise:{agency:'Police',sla:'2 working days',category:'noise'},
      smoking_prohibited:{agency:'NEA',sla:'24 hours',category:'noise'},
      rat:{agency:'NEA',sla:'2 working days',category:'pest'},
      mosquito_breeding:{agency:'NEA',sla:'24 hours',category:'pest'},
      bee_nest:{agency:'NEA',sla:'4 hours',category:'pest'},
      stray_cat:{agency:'NEA',sla:'2 working days',category:'pest'},
      illegal_parking:{agency:'LTA',sla:'24 hours',category:'vehicles'},
      abandoned_vehicle:{agency:'LTA',sla:'3 working days',category:'vehicles'},
      pmd:{agency:'LTA',sla:'24 hours',category:'vehicles'},
      overgrown_grass:{agency:'NParks',sla:'3 working days',category:'greenery'},
      fallen_uprooted_tree:{agency:'NParks',sla:'4 hours',category:'greenery'},
      dead_tree:{agency:'NParks',sla:'3 working days',category:'greenery'},
    };

    var AI_AGENCY_META = {
      'NEA':          {icon:'🌿', color:'#10b981'},
      'Town Council': {icon:'🏘️', color:'#3b82f6'},
      'PUB':          {icon:'💧', color:'#06b6d4'},
      'SCDF':         {icon:'🚒', color:'#ef4444'},
      'LTA':          {icon:'🚗', color:'#f59e0b'},
      'NParks':       {icon:'🌳', color:'#22c55e'},
      'Police':       {icon:'🚔', color:'#8b5cf6'},
    };

    /* ── Load live analytics ── */
    function loadAnalytics() {
      fetch('/analytics?days=365')
        .then(function(r){ return r.ok ? r.json() : null; })
        .then(function(d){
          if (!d) d = {total:87,critical:3,open:24,resolved:63,
            agency:{'NEA':28,'Town Council':22,'PUB':12,'SCDF':4,'LTA':11,'NParks':6,'Police':4},
            priority:{CRITICAL:3,HIGH:14,MEDIUM:38,LOW:32}};
          aiAnalytics = d;
          var el = function(id){ return document.getElementById(id); };
          if(el('b-ai-d-tot'))  el('b-ai-d-tot').textContent  = d.total    || 0;
          if(el('b-ai-d-crit')) el('b-ai-d-crit').textContent = d.critical || 0;
          if(el('b-ai-d-open')) el('b-ai-d-open').textContent = d.open     || 0;
          if(el('b-ai-d-res'))  el('b-ai-d-res').textContent  = d.resolved || 0;
        })
        .catch(function(){
          aiAnalytics = {total:87,critical:3,open:24,resolved:63,
            agency:{'NEA':28,'Town Council':22,'PUB':12,'SCDF':4,'LTA':11,'NParks':6,'Police':4},
            priority:{CRITICAL:3,HIGH:14,MEDIUM:38,LOW:32}};
        });
    }
    loadAnalytics();

    /* ── Load live cases ── */
    function loadLiveCases() {
      fetch('/cases')
        .then(function(r){ return r.ok ? r.json() : null; })
        .then(function(d){
          if (d && d.cases) aiLiveCases = d.cases;
        })
        .catch(function(){});
    }
    loadLiveCases();

    /* ── System prompt ── */
    function buildSysPrompt() {
      return 'You are an AI assistant for the Tampines Estate Reporter agency portal in Singapore. You help agency staff with:\n'
        + '1. Which agency/department handles which issue type\n'
        + '2. Expected SLA response times\n'
        + '3. Analysis of live case data\n\n'
        + 'AGENCY ROUTING:\n' + JSON.stringify(AI_ROUTING) + '\n\n'
        + 'LIVE SUMMARY:\n' + JSON.stringify(aiAnalytics || {}) + '\n\n'
        + 'LIVE CASES (full list — use this to answer questions about specific cases, locations, summaries, reporters, SLAs, status):\n' + JSON.stringify(aiLiveCases || []) + '\n\n'
        + 'AGENCIES:\n'
        + '- NEA = National Environment Agency (cleanliness, pest, waste, smoking)\n'
        + '- Town Council = Tampines Town Council (structural, electrical, maintenance)\n'
        + '- PUB = Public Utilities Board (flooding, drainage, water leaks)\n'
        + '- SCDF = Singapore Civil Defence Force (fire, blocked exits — IMMEDIATE)\n'
        + '- LTA = Land Transport Authority (vehicles, parking, roads)\n'
        + '- NParks = National Parks Board (trees, greenery)\n'
        + '- Police = Singapore Police Force (noise, graffiti, vandalism)\n\n'
        + 'STYLE: Be concise. Use **bold** for agency names. Bullet points for lists.\n'
        + 'CHARTS: When asked to show a chart, include exactly [CHART:agency] or [CHART:priority] or [CHART:sla] in your response.\n'
        + 'Always confirm which agency handles what clearly.';
    }

    /* ── Chart renderers (Chart.js loaded lazily) ── */
    function ensureChartJS(cb) {
      if (window.Chart) { cb(); return; }
      var s = document.createElement('script');
      s.src = 'https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js';
      s.onload = cb;
      document.head.appendChild(s);
    }

    function renderAgencyChart(container) {
      var id = 'baic_' + (++aiChartCount);
      container.innerHTML = '<div class="b-ai-chart-card"><div class="b-ai-chart-title">Agency Case Distribution</div><canvas id="' + id + '" height="160"></canvas></div>';
      ensureChartJS(function(){
        var d = aiAnalytics || {};
        var entries = Object.entries(d.agency || {}).sort(function(a,b){return b[1]-a[1];});
        new Chart(document.getElementById(id), {
          type: 'bar',
          data: {
            labels: entries.map(function(e){return e[0];}),
            datasets: [{
              data: entries.map(function(e){return e[1];}),
              backgroundColor: entries.map(function(e){ return (AI_AGENCY_META[e[0]] ? AI_AGENCY_META[e[0]].color : '#94a3b8') + 'cc'; }),
              borderColor:     entries.map(function(e){ return AI_AGENCY_META[e[0]] ? AI_AGENCY_META[e[0]].color : '#94a3b8'; }),
              borderWidth: 1.5, borderRadius: 4, borderSkipped: false,
            }]
          },
          options: {
            animation: false, plugins: { legend: { display: false } },
            scales: {
              x: { grid:{display:false}, ticks:{font:{size:9},color:'#79776e'} },
              y: { grid:{color:'#e8e6e1'}, ticks:{font:{size:9},color:'#79776e'}, beginAtZero:true }
            }
          }
        });
      });
    }

    function renderPriorityChart(container) {
      var id = 'baic_' + (++aiChartCount);
      var p = (aiAnalytics && aiAnalytics.priority) || {};
      container.innerHTML = '<div class="b-ai-chart-card"><div class="b-ai-chart-title">Priority Breakdown</div><canvas id="' + id + '" height="160"></canvas></div>';
      ensureChartJS(function(){
        new Chart(document.getElementById(id), {
          type: 'doughnut',
          data: {
            labels: ['Critical','High','Medium','Low'],
            datasets: [{
              data: [p.CRITICAL||0, p.HIGH||0, p.MEDIUM||0, p.LOW||0],
              backgroundColor: ['#ef4444cc','#f59e0bcc','#3b82f6cc','#9ca3afcc'],
              borderColor:     ['#ef4444',  '#f59e0b',  '#3b82f6',  '#9ca3af'],
              borderWidth: 2,
            }]
          },
          options: {
            cutout: '60%', animation: false,
            plugins: { legend: { position:'bottom', labels:{font:{size:10},padding:10} } }
          }
        });
      });
    }

    function renderSLATable(container) {
      var byAgency = {};
      Object.values(AI_ROUTING).forEach(function(v){
        if (!byAgency[v.agency]) byAgency[v.agency] = [];
        byAgency[v.agency].push(v.sla);
      });
      var rows = Object.entries(byAgency).map(function(e){
        var agency = e[0], slas = e[1];
        var fast = slas.includes('IMMEDIATE') ? 'IMMEDIATE'
          : slas.find(function(s){return s.includes('hours') && parseInt(s)<=4;}) ? '≤ 4 hrs'
          : slas.find(function(s){return s.includes('hours');}) ? '24 hrs'
          : '2–5 days';
        var cls = fast==='IMMEDIATE'||fast==='≤ 4 hrs' ? 'fast' : fast==='24 hrs' ? 'med' : 'slow';
        var meta = AI_AGENCY_META[agency] || {};
        return '<tr><td>'+(meta.icon||'🏢')+' '+agency+'</td><td>'+slas.length+' types</td><td><span class="b-ai-sla '+cls+'">'+fast+'</span></td></tr>';
      }).join('');
      container.innerHTML = '<div class="b-ai-chart-card"><div class="b-ai-chart-title">Agency SLA Reference</div>'
        + '<table class="b-ai-tbl"><thead><tr><th>Agency</th><th>Types</th><th>Fastest SLA</th></tr></thead><tbody>'+rows+'</tbody></table></div>';
    }

    /* ── Append messages ── */
    function nowStr() {
      return new Date().toLocaleTimeString('en-SG',{hour:'2-digit',minute:'2-digit',hour12:false});
    }
    function scrollBottom() {
      var el = document.getElementById('b-ai-msgs');
      if (el) requestAnimationFrame(function(){ el.scrollTop = el.scrollHeight; });
    }

    function appendUser(text) {
      var list = document.getElementById('b-ai-msglist');
      var d = document.createElement('div');
      d.className = 'b-ai-msg user';
      d.innerHTML = '<div class="b-ai-bubble user">'+text.replace(/</g,'&lt;').replace(/>/g,'&gt;')+'</div>'
        + '<div class="b-ai-time">'+nowStr()+'</div>';
      list.appendChild(d);
      scrollBottom();
    }

    function appendAI(raw, provider) {
      provider = provider || 'ai';
      var list = document.getElementById('b-ai-msglist');
      var d = document.createElement('div');
      d.className = 'b-ai-msg ai';

      /* Strip chart markers for display text */
      var text = raw.replace(/\[CHART:(agency|priority|sla)\]/g,'').trim();

      /* Markdown-lite: bold, bullets, paragraphs */
      text = text.replace(/\*\*(.+?)\*\*/g,'<strong>$1</strong>');
      text = text.replace(/^[-•]\s+(.+)$/gm,'<li>$1</li>');
      var paras = text.split(/\n\n+/).filter(function(p){return p.trim();});
      text = paras.length > 1
        ? paras.map(function(p){ return p.startsWith('<li>') ? '<ul>'+p+'</ul>' : '<p>'+p.replace(/\n/g,'<br>')+'</p>'; }).join('')
        : text.replace(/\n/g,'<br>');

      d.innerHTML = '<div class="b-ai-row">'
        + '<div class="b-ai-ava">✦</div>'
        + '<div style="flex:1;min-width:0">'
        + '<div class="b-ai-bubble ai" id="b-ai-bub-'+aiChartCount+'">'+text+'</div>'
        + '</div></div>'
        + '<div class="b-ai-time" style="margin-left:33px">'+nowStr()+' · <span style="color:'+(provider==='groq'?'#f97316':'#2C3E6D')+';font-weight:700">'+(provider==='groq'?'Groq ⚡':'Gemini ✦')+'</span></div>';
      list.appendChild(d);

      /* Inject charts after bubble is in DOM */
      var bubbleEl = d.querySelector('.b-ai-bubble.ai');
      if (raw.includes('[CHART:agency]')) {
        var cd = document.createElement('div'); bubbleEl.appendChild(cd); renderAgencyChart(cd);
      }
      if (raw.includes('[CHART:priority]')) {
        var cp = document.createElement('div'); bubbleEl.appendChild(cp); renderPriorityChart(cp);
      }
      if (raw.includes('[CHART:sla]')) {
        var cs = document.createElement('div'); bubbleEl.appendChild(cs); renderSLATable(cs);
      }

      scrollBottom();
    }

    function appendTyping() {
      var list = document.getElementById('b-ai-msglist');
      var d = document.createElement('div');
      var id = 'b-ai-typ-' + Date.now();
      d.id = id; d.className = 'b-ai-msg ai';
      d.innerHTML = '<div class="b-ai-row"><div class="b-ai-ava">✦</div>'
        + '<div class="b-ai-typing"><span></span><span></span><span></span></div></div>';
      list.appendChild(d);
      scrollBottom();
      return id;
    }

    function removeTyping(id) {
      var el = document.getElementById(id);
      if (el) el.remove();
    }

    /* ── Send to Claude ── */
    function aiSend() {
      var ta = document.getElementById('b-ai-textarea');
      var text = ta.value.trim();
      if (!text || aiLoading) return;

      /* Hide welcome card */
      var wc = document.getElementById('b-ai-welcome');
      if (wc) wc.style.display = 'none';

      ta.value = ''; aiResize(ta); setAiLoading(true);
      appendUser(text);
      var typId = appendTyping();
      aiConvo.push({role:'user', content:text});

      fetch('/api/gemini-chat', {
        method: 'POST',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify({
          system: buildSysPrompt(),
          messages: aiConvo.slice(-12),
        })
      })
      .then(function(r){ return r.json(); })
      .then(function(data){
        var text = data.content || '⚠️ No response received.';
        var provider = data.provider || 'ai';
        aiConvo.push({role:'assistant', content:text});
        removeTyping(typId);
        appendAI(text, provider);
        /* Show badge if drawer is closed */
        if (!document.getElementById('b-ai-drawer').classList.contains('open')) {
          var badge = document.getElementById('b-ai-badge');
          if (badge) badge.classList.add('show');
        }
      })
      .catch(function(){
        removeTyping(typId);
        appendAI('⚠️ Could not reach AI service. Check your connection and try again.');
      })
      .finally(function(){ setAiLoading(false); });
    }

    function setAiLoading(v) {
      aiLoading = v;
      var btn = document.getElementById('b-ai-sendbtn');
      if (btn) { btn.disabled = v; btn.style.opacity = v ? '0.45' : '1'; }
    }

    function aiResize(el) {
      el.style.height = 'auto';
      el.style.height = Math.min(el.scrollHeight, 100) + 'px';
    }

    /* ── Expose globals for inline handlers (avoid closure issues) ── */
    window.__bAiSend  = aiSend;
    window.__bAiKey   = function(e){ if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();aiSend();} };
    window.__bAiResize = aiResize;
    window.__bAiQuick = function(text){
      var ta = document.getElementById('b-ai-textarea');
      if(ta){ ta.value=text; aiResize(ta); }
      aiSend();
    };
    window.__bAiClose = closeAIDrawer;
  }

  /* ── Open / close helpers ── */
  function openAIDrawer() {
    var drawer   = document.getElementById('b-ai-drawer');
    var backdrop = document.getElementById('b-ai-backdrop');
    var fab      = document.getElementById('b-ai-fab');
    var badge    = document.getElementById('b-ai-badge');
    if (drawer)   drawer.classList.add('open');
    if (backdrop) backdrop.classList.add('open');
    if (fab)      fab.classList.add('b-ai-open');
    if (badge)    badge.classList.remove('show');
    /* Focus input */
    setTimeout(function(){
      var ta = document.getElementById('b-ai-textarea');
      if (ta) ta.focus();
    }, 350);
  }

  function closeAIDrawer() {
    var drawer   = document.getElementById('b-ai-drawer');
    var backdrop = document.getElementById('b-ai-backdrop');
    var fab      = document.getElementById('b-ai-fab');
    if (drawer)   drawer.classList.remove('open');
    if (backdrop) backdrop.classList.remove('open');
    if (fab)      fab.classList.remove('b-ai-open');
  }

  function toggleAIDrawer() {
    var drawer = document.getElementById('b-ai-drawer');
    if (drawer && drawer.classList.contains('open')) closeAIDrawer();
    else openAIDrawer();
  }

  /* ── 9. Init ── */
  function init() {
    buildHeader();
    buildBottomNav();
    buildAIFloat();
    syncAgency();
    // re-sync after page's own JS may have written the session
    setTimeout(syncAgency, 400);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

})();