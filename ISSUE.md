# Disney Page Update Notifier - Current Issues & Risks

This document lists known issues, risks, and technical debt
in the current MVP specification (v0.3).

---

## 1. Security Issues

### 1.1 No Authentication

- API is fully open.
- Anyone can register unlimited push tokens.
- Potential abuse of notification system.

Risk Level: Medium (if publicly deployed)

Suggested Fix:
- Introduce simple API key protection
- Or JWT-based auth if SaaS direction

---

### 1.2 No Rate Limiting

- Endpoints can be called unlimited times.
- Vulnerable to abuse or accidental flooding.

Risk Level: Medium

Suggested Fix:
- Add rate limiting middleware (e.g., slowapi)
- Restrict by IP

---

### 1.3 Push Token Abuse Risk

- Malicious user could register many tokens.
- Could cause excessive push notifications.

Risk Level: Medium

Suggested Fix:
- Limit token registration frequency
- Deduplicate tokens in DB

---

## 2. Scraping Stability Risks

### 2.1 HTML Structure Dependency

- CSS selector change breaks monitoring.
- Could cause false positives or silent failures.

Risk Level: Medium

Suggested Fix:
- Add validation checks
- Add logging for selector failure
- Implement fallback strategy

---

### 2.2 False Positive Detection

- Minor formatting changes trigger update.
- Whitespace or ordering differences cause hash change.

Risk Level: Low-Medium

Suggested Fix:
- Normalize text before hashing
- Strip whitespace & dynamic elements

---

### 2.3 No Change Classification

- All changes trigger notification.
- No filtering by importance.

Risk Level: Low (MVP acceptable)

Suggested Future:
- Add semantic diff
- AI-based importance filtering

---

## 3. Operational Risks

### 3.1 No Retry Strategy

- Temporary network failure stops monitoring.
- Could produce misleading behavior.

Risk Level: Medium

Suggested Fix:
- Retry with exponential backoff
- Pause monitoring after N failures

---

### 3.2 No Observability

- No structured logging
- No monitoring dashboard
- No alert system

Risk Level: Medium (for production)

Suggested Fix:
- Add logging (structured JSON logs)
- Add health endpoint
- Integrate with monitoring tool

---

### 3.3 Single Instance Design

- Designed as single-instance scheduler.
- Horizontal scaling may cause duplicate monitoring.

Risk Level: Future concern

Suggested Fix:
- Add distributed lock if scaling
- Or separate worker service

---

## 4. Architecture Limitations

### 4.1 Single URL Only

- Hardcoded monitoring target.
- Not flexible for expansion.

Risk Level: Low (MVP intentional)

Future Improvement:
- Allow multiple URLs
- Per-user monitoring

---

### 4.2 No Admin Interface

- No way to update selector without redeploy.
- Requires code modification.

Risk Level: Low

Future Improvement:
- Admin config endpoint
- Dashboard

---

### 4.3 PostgreSQL Overhead for MVP

- PostgreSQL adds operational complexity.
- May be overkill for single-user MVP.

Risk Level: Low (intentional future-proofing)

---

## 5. Legal & Compliance Considerations

### 5.1 Scraping Policy Dependency

- Must verify robots.txt compliance.
- Future site policy changes could impact operation.

Risk Level: Medium

Suggested Fix:
- Add robots.txt check on startup
- Log compliance status

---

### 5.2 Traffic Pattern Risk

- If deployed publicly, multiple instances increase traffic.
- Could unintentionally violate fair-use principles.

Risk Level: Low (if interval ≥ 60 min)

---

## 6. Deployment Risks

### 6.1 Deployment Target Not Defined

- No CI/CD defined
- No infrastructure spec

Risk Level: Medium

Suggested Fix:
- Define deployment target (Railway, VPS, etc.)
- Add docker-compose for local testing

---

### 6.2 No Environment Separation

- No staging/production config separation defined.

Risk Level: Low (MVP stage)

---

# Summary

Current system is suitable for:
- Personal use
- Controlled small deployment
- MVP validation

Before public deployment, the following should be prioritized:

1. Add minimal authentication or API key
2. Add rate limiting
3. Add logging and observability
4. Improve scraping stability
5. Define deployment target

---

End of document.
