## Problem Statement
Government procurement in India — especially for security forces like CRPF — carries
consequences far exceeding commercial procurement. A single mis-evaluated bid can expose
the organisation to RTI challenges, CVC scrutiny, vendor litigation, and CAG audit findings. The
current manual evaluation process suffers from three compounding failure modes:
- Zero-bias requirement: Evaluators are human. Even with integrity, unconscious bias
toward known vendors, fatigue on large bid sets (50+ bidders), or inconsistent
interpretation of identical criteria across evaluators creates unequal treatment.
- Heterogeneous messy data: Bids arrive as scanned PDFs (often photographed on
phones), handwritten certificates from State Government offices, multi-language
documents (Hindi/Marathi/English mixed), and legacy Word/Excel attachments. No two
bids are structurally identical.
- RTI & auditability: Under Section 6 of the RTI Act 2005, any unsuccessful bidder can
demand disclosure of the reasons for rejection. Without machine-readable, source-
traceable reasoning, the procuring authority cannot defend its decisions — inviting legal
challenge and re-tendering delays.
Why This Wins at a Hackathon
- Not just another chatbot: Most teams will build a Q&A bot over PDFs. This is a
decision-support engine with formal verification.

- Addresses the hard problem: OCR for handwritten government certificates + conflict
resolution is a solved-for engineering problem here, not left as "future work".
- Demo-able explainability: The Verdict Traceability Matrix is a tangible artifact the jury
can examine — they can pick any bid, ask "why was this rejected?", and get a source-
pinned answer in under 3 seconds.
- India-specific compliance: Built around RTI Act 2005, GFR 2017 procure
ment rules, and CVC guidelines — not generic procurement theory.

