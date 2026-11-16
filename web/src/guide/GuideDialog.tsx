import { useEffect, useRef, useState, type KeyboardEvent } from "react";
import { createPortal } from "react-dom";
import { GUIDE_STEPS, GUIDE_TERMS } from "./content";
import "./guide.css";

const TERMS = GUIDE_STEPS.length; // the page after the last step explains the labels
const PAGES = TERMS + 1;

/** A step-by-step walkthrough for first-time users. Opens itself on the first visit; the header "Guide" button reopens it. */
export function GuideDialog({ open, onClose }: { open: boolean; onClose: () => void }) {
  const [page, setPage] = useState(0);
  const dialog = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    setPage(0);
    const opener = document.activeElement as HTMLElement | null;
    dialog.current?.focus();
    const onEscape = (e: globalThis.KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    document.addEventListener("keydown", onEscape);
    return () => { document.removeEventListener("keydown", onEscape); opener?.focus(); };
  }, [open, onClose]);

  if (!open) return null;
  const go = (p: number) => { setPage(Math.max(0, Math.min(PAGES - 1, p))); dialog.current?.focus(); };
  const last = page === PAGES - 1;

  const onKeyDown = (e: KeyboardEvent) => {
    if (e.key === "ArrowRight" && !(e.target instanceof HTMLInputElement)) { go(page + 1); return; }
    if (e.key === "ArrowLeft") { go(page - 1); return; }
    if (e.key !== "Tab") return;
    // Keep keyboard focus inside the dialog while it is open.
    const items = dialog.current!.querySelectorAll<HTMLElement>("button:not(:disabled)");
    const first = items[0], end = items[items.length - 1], active = document.activeElement;
    if (e.shiftKey && (active === first || active === dialog.current)) { e.preventDefault(); end.focus(); }
    else if (!e.shiftKey && active === end) { e.preventDefault(); first.focus(); }
  };

  const step = GUIDE_STEPS[page];
  return createPortal(
    <div className="guide-scrim" onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}>
      <div className="guide" role="dialog" aria-modal="true" aria-labelledby="guide-title" aria-describedby="guide-body"
        tabIndex={-1} ref={dialog} onKeyDown={onKeyDown}>
        <div className="guide-head">
          <p className="section-label">New here? · {page + 1} of {PAGES}</p>
          <button type="button" className="btn guide-close" onClick={onClose}>Close guide</button>
        </div>

        {page < TERMS ? (
          <div id="guide-body" aria-live="polite">
            <h2 id="guide-title" className="guide-title">{step.title}</h2>
            <h3 className="guide-sub">{step.doLabel ?? "What to do"}</h3>
            <ul className="guide-list">{step.doThis.map((line) => <li key={line}>{line}</li>)}</ul>
            <h3 className="guide-sub">Why it matters</h3>
            <p className="guide-why">{step.why}</p>
          </div>
        ) : (
          <div id="guide-body" aria-live="polite">
            <h2 id="guide-title" className="guide-title">Reading the screen</h2>
            <dl className="guide-terms">
              {GUIDE_TERMS.map((t) => <div key={t.term}><dt>{t.term}</dt><dd>{t.meaning}</dd></div>)}
            </dl>
            <p className="caption">Reopen this guide any time with the “Guide” button at the top.</p>
          </div>
        )}

        <div className="guide-dots" role="group" aria-label="Guide pages">
          {Array.from({ length: PAGES }, (_, i) => (
            <button key={i} type="button" aria-label={i < TERMS ? GUIDE_STEPS[i].title : "Reading the screen"}
              aria-current={i === page ? "step" : undefined} onClick={() => go(i)} />
          ))}
        </div>

        <div className="guide-nav">
          <button type="button" className="btn" disabled={page === 0} onClick={() => go(page - 1)}>Back</button>
          {last
            ? <button type="button" className="btn btn-primary" onClick={onClose}>Start planning</button>
            : <button type="button" className="btn btn-primary" onClick={() => go(page + 1)}>Next</button>}
        </div>
      </div>
    </div>,
    document.body,
  );
}
