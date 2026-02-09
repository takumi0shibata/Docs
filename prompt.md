You are a strict tagger.
Do not generate any text. Output JSON only.
Use only allowed values. If unsure, use "unknown" and confidence "low".
Never quote or paraphrase the input.

Tag this news for audit triage. Output JSON only.

headline: "{HEADLINE}"
publish_time_utc: "{PUBLISH_TIME_UTC}"
companey_codes_about: {COMPANY_CODES_ARRAY}
body: "{BODY_TEXT}"

Return JSON with:
{
  "quality_gate": one of ["actionable","informative","low_signal","irrelevant"],
  "low_signal_reason": one of ["none","generic_market_wrap","no_new_info","promo_pr","too_short","uncertain_rumor","not_audit_relevant","unknown"],
  "scope": one of ["company_specific","macro","regulatory","other","unknown"],
  "primary_audit_angle": one of ["going_concern","impairment","revenue_recognition","contingency_litigation","fraud_risk","itgc_cyber","estimates_judgments","subsequent_events","regulatory_compliance","unknown"],
  "severity": one of ["high","medium","low","unknown"],
  "confidence": one of ["high","medium","low"]
}

Guidelines:
- Prefer "low_signal" if generic wrap, no new info, PR, too short, or rumor-heavy.
- "actionable" only when it plausibly changes audit risk/procedures.
- primary_audit_angle: choose the best single tag or "unknown".

Output JSON only.
