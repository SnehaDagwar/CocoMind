# National Framework for Business

## Registry Modernization: A Unified Digital
Infrastructure for Bharat
The digital evolution of India's business landscape is currently navigating a pivotal "Amrit Kaal"
transition, moving from a legacy of fragmented state-level silos toward a population-scale Digital
Public Infrastructure (DPI). As India strives for the "Viksit Bharat 2047" vision, the primary
barrier remains the structural friction between 40+ state departments and centralized regulatory
anchors. This report provides a comprehensive, expert-level architectural and policy roadmap
for resolving business entity data, ensuring bi-directional interoperability, and leveraging AI for
active intelligence across the entire Indian subcontinent.

## I. Foundations of the Unique Business Identifier

## (UBID)
The core of a unified registry is the implementation of a Unique Business Identifier (UBID) that
acts as the "DNA" of an entity across all interactions. Per the Union Budget 2023, the
Permanent Account Number (PAN) is established as the primary common identifier for all digital
systems of specified government agencies.
A. The PAN 2.0 Ecosystem
The government has recently approved the PAN 2.0 Project, a ₹1,435 crore initiative designed
to re-engineer taxpayer registration services.
- Unified Management: Consolidates multiple platforms (e-Filing, UTIITSL, Protean) into a
single portal.
- Common Business Identifier: PAN links directly with the Tax Deduction and Collection
Account Number (TAN) and Taxpayer Identification Number (TIN) to streamline
multi-sector compliance.
- Security: Implements a "PAN Data Vault" and dynamic QR codes for enhanced data
protection and instant validation by financial institutions.

## B. National Registry Anchors
Beyond PAN, a robust UBID strategy must resolve data against three other critical national
pillars:
- CIN (Corporate Identification Number): A 21-digit alphanumeric code for registered
companies, encoding listing status, industry code, and state of registration.
- GSTIN (Goods and Services Tax Identification Number): A 15-digit identifier where the
middle 10 digits represent the entity's PAN, enabling a direct bridge between tax and
business identity.
- Udyam Registration Number (URN): A permanent identifier for MSMEs that
automatically fetches PAN and GST-linked details from government databases during a

paperless registration process.

## II. State-of-the-Art Entity Resolution (ER) Architecture
Entity Resolution is the decision-making process of linking fragmented records across disparate
data sources. In the Indian context, this requires overcoming "usual chaos" such as landmarks
in addresses and phonetic variations in names.

## A. The Resolution Workflow
A national-scale ER engine should follow a structured lifecycle:
- Preprocessing: Cleaning and parsing complex fields into components (e.g., splitting
"Suresh Agro & Sons Pvt Ltd" into legal name and entity type).
- Blocking (Indexing): Grouping records by shared attributes like pincode or ward to
reduce computational complexity from O(N^2) to a manageable scale.
- Similarity Analysis: Utilizing both deterministic (exact tax IDs) and probabilistic (fuzzy
matching) algorithms.
- Classification & Clustering: High-confidence matches are committed automatically,
while "fuzzy" records are routed to human data stewards.

## B. Specialized Indian Localization Tools
- Address Normalization: Libraries like bharataddress outperform global models by
winning on 6 of 9 Indian-specific fields. It supports India Post's new 10-character DIGIPIN
geo-code for sub-meter location accuracy.
- Geospatial Queries: The indiapins toolkit allows the system to compute geodesic
distances between pincodes and find neighboring blocks, critical for ward-level
administrative reporting.

## III. Active Business Intelligence: Inferring Status from

## Event Streams
Administrative efficiency depends on distinguishing between Active, Dormant, and Closed
entities. Section 455 of the Companies Act 2013 defines a dormant company as one with no
"significant accounting transactions"—meaning no revenue, operating expenses, or trade
contracts.
A. Multi-Source Transactional Signals
A central intelligence layer can infer status by monitoring one-way streams of Relational Event

## Data :
- GSTN Signals: Real-time monitoring of GSTR-1 and GSTR-3B filing consistency. The
GSTN processes 3 billion API calls monthly and can flag "risk profiles" based on sector
benchmarks.
- e-Way Bill Analytics: More than 6.19 crore e-way bills are created monthly, providing
undeniable evidence of commercial activity through the physical movement of goods.

- Labor & Social Security: Tracking contributory remittances from 6.54 lakh
establishments via EPFO and ESIC act as a proxy for operational viability.
B. Continuous-Time Status Modeling
By modeling interaction "contagion" (where one interaction increases the propensity for future
ones), the system can trigger automated alerts.
- Active: High frequency of regulatory, utility, and financial progress events.
- Dormant: Cessation of transactions for 18+ months while maintaining statutory
preservation (e.g., payment of government fees).
- Closed: Terminal events like ROC strike-off notifications or bank account closure.

## IV. Bi-Directional Interoperability: Single Window vs.

## Legacy Silos
India’s modernization strategy avoids "rip-and-replace" in favor of the Strangler Fig Pattern,
where new layers wrap around existing logic.
A. Change Data Capture (CDC) Strategies
To synchronize the National Single Window System (NSWS) with 40+ legacy department
systems, the interoperability layer must implement CDC :
- Log-based CDC: The gold standard for national systems. It "tails" database transaction
logs (like PostgreSQL WAL) to identify changes instantly with near-zero overhead on
production systems.
- API Setu Integration: Uses the national "Open API Platform" to facilitate standardized,
secure data exchange between publishers (departments) and consumers (SWS).

## B. Conflict Resolution & Auditability
Bi-directional sync introduces "split-brain" risks that must be managed through explicit policies :
- Last Write Wins (LWW): Modification with the latest timestamp is retained.
- Source of Truth Rules: MCA is authoritative for corporate structure, while the SWS is
authoritative for operational contact details.
- Manual Review Workflows: Conflicts exceeding a risk threshold are flagged for
administrative resolution.

## Sync Aspect Requirement Mechanism
Integrity Transactional consistency for
related records.
Unified CDC with Kafka
buffering.
Traceability Full audit trail of every
propagation.
Immutable logs with
"canonical_id" mapping.
Scalability Handling population-scale
throughput.
Event-driven architecture with
backpressure.

## V. AI-Enhanced Procurement and Tender Evaluation
Public procurement represents ~13% of GDP, yet manual evaluation remains slow and

error-prone. AI-native procurement shifts committees from manual reading to "augmentation of
evaluation intelligence".

## A. Intelligent Eligibility Analysis
Using Natural Language Processing (NLP) and Retrieval-Augmented Generation (RAG), the
system automates bidder screening:
- Criterion Extraction: AI parses 300–3,000 page tender documents to identify technical
specs, financial thresholds, and mandatory certifications.
- Explainable Verdicts: Instead of a simple "Yes/No," the system provides "clause-level
transparency," referencing specific RFP sections (e.g., Section 3.2 for turnover rules).
- Human-AI Balance: Uncertain cases or unreadable scans are flagged for human review
with a clear "reason for ambiguity".

## B. Multimodal Intelligence
- PaddleOCR-VL-1.5: Released in 2026, this model reaches 94.5% accuracy in
recognizing complex tables, charts, and handwritten signatures in bidder documents.
- Modular RAG: Combines dense retrieval (semantic coverage) with sparse retrieval
(lexical precision for section numbers) to ensure "traceable" provenance for every
evaluation claim.

## VI. Data Governance and Privacy-Preserving AI
The consolidation of national business data is governed by the National Data Governance
Framework Policy (NDGFP), which aims to standardize security standards across the whole of
government.
A. Privacy-Preserving LLM Deployment
For government systems dealing with PII (Aadhaar, PAN), the SoE framework (Continual
Pretraining on Encrypted Synthetic Data) offers a solution :
- NER-based Extraction: Identifies PII entities within the corpus.
- Deterministic Encryption: PII entities are encrypted using AES, allowing the model to
learn domain knowledge from ciphertext without seeing plaintext.
- Synthetic Data (RPSG): Generates realistic "replicas" of private text that preserve
semantic richness while integrating formal differential privacy (DP).
B. AIKosh (National Dataset Platform)
Under the IndiaAI Mission, AIKosh hosts 9,500+ datasets and 273 sectoral models, providing a
secure "AI Sandbox" for model training that integrates data from both government and
non-government sources.

## VII. Implementation Roadmap for National

## Transformation

## Phase Milestone Operational Impact
Foundation Full rollout of PAN 2.0 and
UBID layer; adoption of
DIGIPIN for address
standardization.
Creates a single source of truth
for 1.4 billion people and 63
million MSMEs.
Integration Implementation of API-driven
CDC across all state SWS;
alignment with API Setu
policies.
Achieves real-time
synchronization between state
registries and central regulatory
anchors.
Intelligence Deployment of AI-native
procurement cells and business
activity monitoring layers.
Enhances ease of doing
business through automated
eligibility and fraud detection.
By synergizing Digital Public Infrastructure (DPI) with AI-driven intelligence, India can dismantle
the "criminal compliance architecture" and move toward a trust-based regulatory environment
that fosters institutional capacity and strategic autonomy.

## Works cited
- What is Entity Resolution? - RudderStack,
https://www.rudderstack.com/blog/what-is-entity-resolution/
2. Entity Resolution — An
Introduction | by Adrian Evensen | Medium,
https://medium.com/@adev94/entity-resolution-an-introduction-fb2394d9a04e
3. What is Entity
Resolution? - Reltio, https://www.reltio.com/glossary/data-quality/what-is-entity-resolution/ 4.
Bharataddress v0.2 — The Complete Open Source Indian Address Toolkit - DEV Community,
https://dev.to/neelagiri65/why-indian-address-parsing-is-broken-and-what-i-built-to-fix-it-2pne 5.
Determining the best data architecture and stack for entity resolution : r/dataengineering,
https://www.reddit.com/r/dataengineering/comments/1s5xlj5/determining_the_best_data_archite
cture_and_stack/
6. What is Agentic Entity Resolution? Why It's The Future of AI,
https://senzing.com/what-is-agentic-entity-resolution/
7. indiapins - PyPI,
https://pypi.org/project/indiapins/
8. Inferring social structure from continuous-time interaction
data - PMC - NIH, https://pmc.ncbi.nlm.nih.gov/articles/PMC6020699/
9. Business transaction
monitoring - IBM,
https://www.ibm.com/docs/bg/integration-bus/10.0.0?topic=monitoring-business-transaction 10.
What is a Dormant Company and How Does it Work? - Rapid Formations,
https://www.rapidformations.co.uk/blog/a-guide-to-dormant-companies/
11. Dormant Company
vs Active Company: What's the Difference? - filingpro,
https://filingpro.io/dormant-company-vs-active-company/
12. What Is Change Data Capture
(CDC)? Methods & Use Cases - Striim,
https://www.striim.com/blog/change-data-capture-cdc-what-it-is-and-how-it-works/
13. What is
Change Data Capture (CDC)? A Beginner's Guide - DataCamp,
https://www.datacamp.com/blog/change-data-capture
14. What Is Change Data Capture? - IBM,
https://www.ibm.com/think/topics/change-data-capture
15. The Engineering Challenges of
Bi-Directional Sync: Why Two One-Way Pipelines Fail,
https://www.stacksync.com/blog/the-engineering-challenges-of-bi-directional-sync-why-two-one-
way-pipelines-fail
16. Why Two-way Sync is Essential for Modern Teams in 2026 - Exalate,

https://exalate.com/blog/two-way-synchronization/
17. Conflict resolution strategies in Data
Synchronization | by Mobterest Studio - Medium,
https://mobterest.medium.com/conflict-resolution-strategies-in-data-synchronization-2a10be5b8
2bc
18. AI in public procurement: Governing with Artificial Intelligence - OECD,
https://www.oecd.org/en/publications/governing-with-artificial-intelligence_795de142-en/full-repo
rt/ai-in-public-procurement_2e095543.html
19. AI Tender Eligibility Checks | Analyze Tenders

## Instantly - Minaions,
https://minaions.com/blog/understanding-ai-powered-tender-analysis-how-minaions-determines-
your-eligibility-instantly
20. Legal-DC: Benchmarking Retrieval-Augmented Generation for Legal
Documents - arXiv, https://arxiv.org/html/2603.11772v1
21. A Comparative Evaluation of RAG
Architectures for Cross-Domain LLM Applications: Design, Implementation, and Assessment -
IEEE Xplore, https://ieeexplore.ieee.org/iel8/6287639/10820123/11245479.pdf
22. Continual
Pretraining on Encrypted Synthetic Data ... - ACL Anthology,
https://aclanthology.org/2026.findings-eacl.21.pdf
23. Safeguarding Data Privacy While Using
LLMs | Tonic.ai, https://www.tonic.ai/guides/llm-data-privacy
24. Private Seeds, Public LLMs:
Realistic and Privacy-Preserving Synthetic Data Generation, https://arxiv.org/html/2604.07486v2

