# Portfolio resume and interview guide

## Resume bullets

**Financial Risk Intelligence**

- Connected synthetic transaction scoring, case evidence and local Ollama generation into a
  reproducible analyst-brief workflow; evaluated citations, abstention and latency while
  retaining failed model outputs for review. See the financial repository's local RAG report.

- Built a synthetic financial-investigation copilot with TF-IDF and pinned CPU MiniLM retrieval,
  cited case evidence, explicit evidence-availability checks and automated dashboard tests.
- Evaluated retrieval on authored challenge sets; reduced TF-IDF unsupported acceptance from
  7/18 to 2/18 on a 36-question scope-check fixture without additional answerable rejections,
  and rejected a threshold change that failed separate-question validation.

**Enterprise Healthcare Data Platform**

- Added Spark data-quality gates, stage-level failure reporting and lineage manifests; executed
  a 5,000-event local pipeline producing 3,911 unique patient records and tested recovery isolation.
- Executed a historical 50M-row synthetic Spark generation/aggregation workload on one EC2
  instance with S3 output in 156.294 seconds (319,909 rows/sec), as documented in benchmark evidence.

- Developed a synthetic healthcare data platform with Spark Bronze/Silver/Gold processing,
  schema and quality contracts, chronological readmission evaluation and cohort diagnostics.
- Implemented discharge-time outcome-maturity checks; on 20,000 synthetic encounters,
  excluded 421 unavailable training labels and 562 immature holdout labels, preserving a
  reproducible before/after evaluation and updating dashboard evidence.

The repository also documents a historical 50M-row single-node AWS Spark benchmark. Describe
that as generation, aggregation and S3 output on one EC2 instance, not a 50M-row end-to-end
ML pipeline or distributed-cluster test. Include it only if you can explain the run and evidence.

## Two-minute explanations

**Financial:** Start with limited investigator capacity and the need for source-grounded review.
Explain lexical versus semantic retrieval, then show that high ranking recall did not guarantee
answerability. Walk through the rejected 0.36 threshold experiment and the evidence-scope rules.
Close with the remaining paraphrase failures and the difference between citation IDs and supported
claims. The live runtime was rebooted after a stale-import failure and the exercised flows passed.

**Healthcare:** Start with point-in-time data correctness. An earlier encounter can still have
an unavailable 30-day outcome. Explain prediction at discharge, strictly earlier encounter
history, label maturity, fit-cutoff exclusions and follow-up coverage. Present the lower PR-AUC
honestly: correctness changed the evaluation population; the goal was credible evidence.

## Questions to rehearse

- Why does a chronological split alone not eliminate outcome leakage?
- Why does an unavailable outcome differ from a negative outcome?
- What does Recall@3 measure, and what does it fail to establish?
- How were development and validation separated, and why are authored fixtures still limited?
- Why keep TF-IDF in the public app while offering MiniLM locally?
- How would you validate calibration and choose an operating threshold for a real workflow?
- What remains untested in a production deployment, and what evidence would you collect next?

## Evidence links

- [Financial case study](https://github.com/mahaveerreddysamala/financial-risk-intelligence/blob/main/docs/portfolio-case-study.md)
- [Healthcare label maturity](label-maturity.md)
- [Machine-readable comparison](label-maturity-results.json)

Use these as portfolio claims, not employment achievements or deployed business impact.
Describe what you can demonstrate and explain; avoid claims of clinical accuracy, cost savings,
or reduced real-world fraud that these synthetic experiments do not measure.
