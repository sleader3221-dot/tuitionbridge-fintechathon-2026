/* TuitionBridge frontend. The UI never computes money or decides permissions: every number and every
   allow/deny shown here comes from the backend. The role picker only changes which demo API key is sent. */
const KEYS = { viewer: "demo-viewer-key", analyst: "demo-analyst-key", planner: "demo-planner-key", student: "demo-student-key" };
const ACCOUNT = "acct_demo_student";
const S = { role: "student", plan: null, transfer: null, account: null, providers: [] };
const $ = (id) => document.getElementById(id);
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const money = (v, ccy) => `${Number(v).toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })} ${ccy}`;

async function api(path, { method = "GET", body, params } = {}) {
  const url = new URL(path, location.origin);
  if (params) Object.entries(params).forEach(([k, v]) => url.searchParams.set(k, v));
  const res = await fetch(url, { method, headers: { "X-API-Key": KEYS[S.role], "Content-Type": "application/json" }, body: body ? JSON.stringify(body) : undefined });
  let data = null; try { data = await res.json(); } catch (_) {}
  if (!res.ok) throw { status: res.status, data };
  return data;
}
function errText(e) {
  if (e?.data?.error) return `${e.status} ${e.data.error.code}: ${e.data.error.message}`;
  if (e?.data?.detail) return `${e.status}: ${typeof e.data.detail === "string" ? e.data.detail : JSON.stringify(e.data.detail)}`;
  return e?.message || `Request failed (${e?.status ?? "network"})`;
}
let toastTimer;
function toast(msg, bad = false) { const t = $("toast"); t.textContent = msg; t.className = `toast show${bad ? " bad" : ""}`; clearTimeout(toastTimer); toastTimer = setTimeout(() => (t.className = "toast"), 5000); }
const statusClass = (s) => ({ EXECUTED_SIMULATED: "ok", APPROVED: "ok", PENDING_APPROVAL: "warn", FAILED: "bad", BLOCKED: "bad", EXPIRED: "bad", REJECTED: "neutral" }[s] || "neutral");
const badge = (s) => `<span class="badge ${statusClass(s)}">${esc(s)}</span>`;
function findingsHtml(risk) {
  if (!risk || !risk.findings.length) return `<div class="note ok">All deterministic risk checks passed.</div>`;
  return `<ul class="findings">${risk.findings.map((f) => `<li><span class="badge ${f.severity === "BLOCK" ? "bad" : "warn"}">${esc(f.code)}</span> ${esc(f.message)}</li>`).join("")}</ul>`;
}

async function loadAccount() {
  try {
    const a = await api(`/api/accounts/${ACCOUNT}`);
    S.account = a;
    $("accountBody").innerHTML = `<dl class="kv"><dt>Holder</dt><dd>${esc(a.account.holder_name)}</dd><dt>Institution</dt><dd>${esc(a.account.institution)}</dd>` +
      a.balances.map((b) => `<dt>Balance ${esc(b.currency)}</dt><dd><strong>${money(b.amount, b.currency)}</strong></dd>`).join("") +
      `<dt>Min reserve</dt><dd>${money(a.account.reserve_min, a.account.home_currency)}</dd></dl><p class="muted">Data label: ${esc(a.data_label)}</p>`;
    $("limitsBody").innerHTML = `<dl class="kv"><dt>Per transfer</dt><dd>${money(a.limits.per_transfer_cap_usd, "USD")}</dd><dt>Daily cap</dt><dd>${money(a.limits.daily_cap_usd, "USD")}</dd><dt>Executed today</dt><dd>${money(a.limits.daily_executed_usd, "USD")}</dd><dt>Quote lock</dt><dd>${a.limits.quote_ttl_seconds}s</dd></dl>`;
    $("benefBody").innerHTML = `<table><tbody>${a.beneficiaries.map((b) => `<tr><td>${esc(b.name)}<br><span class="muted mono">${esc(b.id)} · ${esc(b.currency)} · ${esc(b.account_number_masked)}</span></td><td>${b.blocked ? '<span class="badge bad">BLOCKED</span>' : '<span class="badge ok">OK</span>'}</td></tr>`).join("")}</tbody></table>`;
    $("beneficiary").innerHTML = a.beneficiaries.map((b) => `<option value="${esc(b.id)}">${esc(b.name)}</option>`).join("");
  } catch (e) {
    $("accountBody").innerHTML = `<div class="note bad">${esc(errText(e))}</div>`;
  }
}
async function loadProviders() {
  try { S.providers = await api("/api/providers"); $("provider").innerHTML = S.providers.map((p) => `<option value="${esc(p.id)}">${esc(p.name)}</option>`).join(""); } catch (e) { /* shown on account card */ }
}
async function loadTransfers() {
  try {
    const list = await api("/api/transfers", { params: { account_id: ACCOUNT } });
    $("transfersBody").innerHTML = list.length ? `<table><thead><tr><th>ID</th><th>Status</th><th class="num">Send</th><th class="num">Receive</th><th>Provider</th><th>Reference</th></tr></thead><tbody>` +
      list.map((t) => `<tr><td class="mono"><a href="#" data-id="${esc(t.id)}" class="pick">${esc(t.id)}</a></td><td>${badge(t.status)}</td><td class="num">${t.quote ? money(t.quote.send_amount, t.quote.send_currency) : "—"}</td><td class="num">${t.quote ? money(t.quote.receive_amount, t.quote.receive_currency) : "—"}</td><td>${esc(t.provider_id)}</td><td class="mono">${esc(t.provider_reference || t.failure_reason || "")}</td></tr>`).join("") + `</tbody></table>` : "None yet.";
    document.querySelectorAll("a.pick").forEach((a) => a.addEventListener("click", async (ev) => { ev.preventDefault(); try { setTransfer(await api(`/api/transfers/${a.dataset.id}`)); } catch (e) { toast(errText(e), true); } }));
  } catch (e) { $("transfersBody").innerHTML = `<div class="note bad">${esc(errText(e))}</div>`; }
}
async function loadAudit() {
  try {
    const rows = await api("/api/audit");
    $("auditBody").innerHTML = rows.length ? `<table><thead><tr><th>#</th><th>Time (UTC)</th><th>Actor</th><th>Action</th><th>Tier</th><th>Entity</th><th>Hash</th></tr></thead><tbody>` +
      rows.slice(-25).reverse().map((r) => `<tr><td>${r.seq}</td><td class="mono">${esc(r.ts.slice(0, 19))}</td><td class="mono">${esc(r.actor)}</td><td>${esc(r.action)}</td><td>${r.tier}</td><td class="mono">${esc(r.entity_id || "")}</td><td class="mono">${esc(r.hash.slice(0, 12))}…</td></tr>`).join("") + `</tbody></table><p class="muted">Showing latest ${Math.min(25, rows.length)} of ${rows.length}.</p>` : "Empty.";
  } catch (e) { $("auditBody").innerHTML = `<div class="note bad">${esc(errText(e))}</div>`; }
}

function renderPlan(out) {
  const p = out.plan, ex = out.explanation;
  const rec = p.recommended_provider_id;
  const rows = p.quotes.map((q) => `<tr class="${q.provider_id === rec ? "rec" : ""}"><td>${q.rank}</td><td>${esc(q.provider_name)} ${q.provider_id === rec ? '<span class="badge ok">RECOMMENDED</span>' : ""}</td><td class="num">${money(q.send_amount, q.send_currency)}</td><td class="num">${money(q.total_fees, q.send_currency)}</td><td class="num">${q.customer_rate}</td><td class="num">${money(q.cost_vs_mid, q.send_currency)} (${(Number(q.cost_pct) * 100).toFixed(2)}%)</td><td>${q.settlement_days}d ${q.settles_before_due ? '<span class="badge ok">in time</span>' : '<span class="badge warn">late</span>'}</td></tr>`).join("");
  const aff = p.affordability;
  $("planOut").innerHTML = `<table><thead><tr><th>#</th><th>Provider (SIMULATED)</th><th class="num">You send</th><th class="num">Fees</th><th class="num">Rate</th><th class="num">Cost vs mid</th><th>Settles</th></tr></thead><tbody>${rows}</tbody></table>` +
    (p.exclusions.length ? `<p class="muted">Excluded: ${p.exclusions.map((x) => `${esc(x.provider_id)} (${esc(x.reason)})`).join(", ")}</p>` : "") +
    (aff ? `<div class="note ${aff.affordable ? "ok" : "bad"}"><strong>${aff.affordable ? "Affordable" : "Not affordable"}:</strong> balance ${money(aff.balance, aff.currency)} − ${money(aff.send_amount, aff.currency)} = ${money(aff.balance_after, aff.currency)} vs reserve ${money(aff.reserve_min, aff.currency)}.</div>` : "") +
    (p.warnings.length ? `<div class="note warn">${p.warnings.map(esc).join("<br>")}</div>` : "") +
    `<div class="note"><strong>Explanation</strong> <span class="badge ${ex.source === "LLM" ? "tier" : "neutral"}">${esc(ex.source)}</span> <span class="muted">${esc(ex.validation)}${ex.model ? " · " + esc(ex.model) : ""}</span>${out.question_flagged ? ' <span class="badge bad">question flagged: ' + esc(out.question_flags.join(", ")) + "</span>" : ""}<br>${esc(ex.text)}</div>` +
    `<p class="muted">Rule: ${esc(p.recommendation_rule)} Rates: ${esc(p.data_label)}, as of ${esc(p.quotes[0]?.rate_as_of || "n/a")}.</p>`;
  if (rec) $("provider").value = rec;
}
function setTransfer(t) {
  S.transfer = t;
  const q = t.quote;
  $("prepOut").innerHTML = `<div class="rowhead"><div>Transfer <span class="mono">${esc(t.id)}</span> ${badge(t.status)} ${t.replayed ? '<span class="badge neutral">replayed (idempotent)</span>' : ""} ${t.memo_flagged ? '<span class="badge bad">memo flagged as injection-like</span>' : ""}</div><span class="badge neutral">${esc(t.execution_label)}</span></div>` +
    (q ? `<dl class="kv"><dt>Locked quote</dt><dd>send <strong>${money(q.send_amount, q.send_currency)}</strong> → deliver <strong>${money(q.receive_amount, q.receive_currency)}</strong> via ${esc(q.provider_name)}</dd><dt>Fees / cost vs mid</dt><dd>${money(q.total_fees, q.send_currency)} / ${money(q.cost_vs_mid, q.send_currency)}</dd><dt>Quote expires</dt><dd class="mono">${esc(t.quote_expires_at)}</dd><dt>Beneficiary</dt><dd>${esc(t.beneficiary?.name || t.beneficiary_id)}</dd></dl>` : `<p class="muted">No quote could be produced.</p>`) + findingsHtml(t.risk);
  const exec = $("execOut");
  if (t.status === "EXECUTED_SIMULATED") exec.innerHTML = `<div class="note ok"><strong>Executed in sandbox.</strong> Reference <span class="mono">${esc(t.provider_reference)}</span> at ${esc(t.executed_at)}. Label: ${esc(t.execution_label)}. Balance debited exactly once; re-running execute returns the same result.</div>`;
  else if (t.status === "FAILED") exec.innerHTML = `<div class="note bad"><strong>Execution failed, nothing debited.</strong> ${esc(t.failure_reason)} — you can retry; risk checks run again first.</div>`;
  else if (t.status === "APPROVED") exec.innerHTML = `<div class="note">Approved by <span class="mono">${esc(t.approved_by)}</span>. Execute to settle in the sandbox.</div>`;
  else exec.innerHTML = "";
  $("btnApprove").disabled = t.status !== "PENDING_APPROVAL";
  $("btnExecute").disabled = !(t.status === "APPROVED" || t.status === "FAILED");
  $("btnReject").disabled = !(t.status === "PENDING_APPROVAL" || t.status === "APPROVED");
  $("btnProd").disabled = false;
  loadTransfers(); loadAudit(); loadAccount();
}
async function act(path, body) {
  if (!S.transfer) return;
  try { setTransfer(await api(`/api/transfers/${S.transfer.id}/${path}`, { method: "POST", body })); toast(`${path}: ${S.transfer.status}`); }
  catch (e) { toast(errText(e), true); loadAudit(); }
}

$("role").addEventListener("change", (ev) => { S.role = ev.target.value; $("tierBadge").textContent = `Tier ${{ viewer: 0, analyst: 1, planner: 2, student: 3 }[S.role]}`; loadAccount(); loadTransfers(); loadAudit(); });
$("planForm").addEventListener("submit", async (ev) => {
  ev.preventDefault(); $("planOut").innerHTML = `<p class="muted skeleton">Comparing…</p>`;
  try { S.plan = await api("/api/quotes/compare", { method: "POST", body: { account_id: ACCOUNT, target_receive_amount: $("amount").value.trim(), receive_currency: $("recvCcy").value, due_date: $("dueDate").value, question: $("question").value || null } }); renderPlan(S.plan); }
  catch (e) { $("planOut").innerHTML = `<div class="note bad">${esc(errText(e))}</div>`; loadAudit(); }
});
$("prepForm").addEventListener("submit", async (ev) => {
  ev.preventDefault(); $("prepOut").innerHTML = `<p class="muted skeleton">Preparing…</p>`;
  try {
    const t = await api("/api/transfers/prepare", { method: "POST", body: { account_id: ACCOUNT, beneficiary_id: $("beneficiary").value, provider_id: $("provider").value, target_receive_amount: $("amount").value.trim(), receive_currency: $("recvCcy").value, due_date: $("dueDate").value, memo: $("memo").value || null, idempotency_key: $("idem").value } });
    setTransfer(t); toast(`Prepared: ${t.status}`, t.status === "BLOCKED");
  } catch (e) { $("prepOut").innerHTML = `<div class="note bad">${esc(errText(e))}</div>`; loadAudit(); }
});
$("btnApprove").addEventListener("click", () => act("approve", { note: "Approved in UI" }));
$("btnExecute").addEventListener("click", () => act("execute"));
$("btnReject").addEventListener("click", () => act("reject", { note: "Rejected in UI" }));
$("btnProd").addEventListener("click", () => act("production-execute"));
$("btnVerify").addEventListener("click", async () => { try { const v = await api("/api/audit/verify"); $("auditVerify").innerHTML = `<div class="note ${v.valid ? "ok" : "bad"}">Chain ${v.valid ? "VALID" : "BROKEN"} · ${v.entries_checked} entries checked${v.head_hash ? " · head " + esc(v.head_hash.slice(0, 16)) + "…" : " · first bad seq " + v.first_bad_seq}</div>`; } catch (e) { toast(errText(e), true); } });

$("idem").value = `idem-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
loadAccount(); loadProviders(); loadTransfers(); loadAudit();
