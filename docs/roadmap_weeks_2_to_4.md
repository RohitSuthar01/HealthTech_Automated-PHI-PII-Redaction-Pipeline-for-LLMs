# HealthTech Vault Engine: Engineering Roadmap (Weeks 2-4)

This document outlines the detailed day-by-day engineering roadmap for the Vault / Pseudonymization Engine, covering Week 2 through Week 4. It focuses exclusively on the vault engine, omitting the NLP, regex, FastAPI, and frontend modules as requested.

## Proposed Roadmap

### WEEK 2: Core Pseudonymization & Text Processing

#### Day 8: NLP Integration Adapter & Entity-to-Token Pipeline
1. **Goal**: Build an adapter that consumes NLP outputs (lists of entity dicts) and interacts with the Vault to generate or retrieve tokens.
2. **Concepts to learn**: Adapter pattern, JSON payload structuring, batch operations in Redis.
3. **Files to modify**: `vault/nlp_adapter.py` [NEW], `vault/__init__.py`.
4. **Code to write**: `NLPAdapter.process_entities(nlp_results: list[dict]) -> list[dict]`. It will iterate through NLP entities and use `TokenStore.get_or_create_token` to assign tokens.
5. **Tests to create**: `tests/test_nlp_adapter.py` validating successful mapping of varying entity types.
6. **Documentation to update**: `docs/architecture.md` (Add NLP Adapter component diagram).
7. **Expected Git commit**: `feat(vault): add NLP adapter for entity-to-token pipeline`

#### Day 9: Text Replacement Engine (Forward Redaction)
1. **Goal**: Implement the logic to replace identified sensitive text in the original note with their mapped tokens without altering surrounding context.
2. **Concepts to learn**: Safe string substitution, word boundary detection (`\b` in regex) to prevent partial replacements.
3. **Files to modify**: `vault/text_engine.py` [NEW].
4. **Code to write**: `TextEngine.redact(text: str, entities: list[dict]) -> str`.
5. **Tests to create**: `tests/test_text_engine.py` (test standard replacements and ensure substrings in other words aren't replaced).
6. **Documentation to update**: `docs/architecture.md` (Add Redaction Flow).
7. **Expected Git commit**: `feat(vault): implement forward text redaction engine`

#### Day 10: Reverse Restoration Engine (De-redaction)
1. **Goal**: Reconstruct the original text from a redacted note containing pseudonyms.
2. **Concepts to learn**: Inverse text substitution algorithms, error handling for missing/expired tokens.
3. **Files to modify**: `vault/text_engine.py`.
4. **Code to write**: `TextEngine.restore(redacted_text: str, token_store: TokenStore) -> str`.
5. **Tests to create**: `tests/test_text_engine.py` (validate exact restoration of original notes).
6. **Documentation to update**: `docs/architecture.md` (Add Restoration Flow).
7. **Expected Git commit**: `feat(vault): implement reverse text restoration engine`

#### Day 11: Duplicate Entity Handling
1. **Goal**: Ensure multiple occurrences of the same entity (e.g., "John Smith" appearing twice) receive the exact same token and are redacted correctly.
2. **Concepts to learn**: Token idempotency, overlapping entity resolution.
3. **Files to modify**: `vault/text_engine.py`, `vault/token_store.py`.
4. **Code to write**: Optimize `TextEngine` to sort entities by length (descending) before replacement to handle overlaps, and ensure `TokenStore` returns consistent tokens.
5. **Tests to create**: `tests/test_duplicate_entities.py`.
6. **Documentation to update**: `docs/token_mapping.md` (Add Duplicate Handling rules).
7. **Expected Git commit**: `fix(vault): handle duplicate entity appearances consistently`

#### Day 12: Collision Prevention Mechanisms
1. **Goal**: Prevent distinct entities from accidentally sharing tokens (e.g., "John Smith" the patient vs. "John Smith" the doctor) and ensure generated tokens are strictly unique.
2. **Concepts to learn**: Namespace isolation in Redis, composite key design.
3. **Files to modify**: `vault/token_generator.py`, `vault/token_store.py`.
4. **Code to write**: Update Redis key schemas to strictly incorporate entity type (`TYPE:NAME` mapping) to separate domains.
5. **Tests to create**: `tests/test_collision_prevention.py` (test cross-type identical names).
6. **Documentation to update**: `docs/architecture.md` (Add Collision Prevention section).
7. **Expected Git commit**: `feat(vault): implement strict collision prevention in token mapping`

#### Day 13: Confidence-Aware Mapping & Edge Case Handling
1. **Goal**: Safely process NLP outputs that have low confidence scores or overlapping boundaries.
2. **Concepts to learn**: Confidence thresholding, defensive programming against malformed data.
3. **Files to modify**: `vault/nlp_adapter.py`.
4. **Code to write**: Add a configurable `confidence_threshold` argument to `NLPAdapter`. Filter out or flag entities below this threshold. Add boundary overlap resolution.
5. **Tests to create**: `tests/test_edge_cases.py`.
6. **Documentation to update**: `docs/nlp_research.md` (Document confidence thresholds).
7. **Expected Git commit**: `feat(vault): add confidence-aware thresholding and overlap handling`

#### Day 14: Vault Engine Facade (Week 2 Integration)
1. **Goal**: Integrate all Week 2 components into a high-level, easy-to-use interface for the pipeline.
2. **Concepts to learn**: Facade design pattern.
3. **Files to modify**: `vault/vault.py`.
4. **Code to write**: `Vault.redact_note()` and `Vault.restore_note()` combining `NLPAdapter`, `TokenStore`, and `TextEngine`.
5. **Tests to create**: `tests/test_vault.py` (End-to-end redaction and restoration tests).
6. **Documentation to update**: `README.md` (Usage examples for redaction/restoration).
7. **Expected Git commit**: `feat(vault): integrate components into VaultEngine facade`

---

### WEEK 3: Security, Isolation & Performance

#### Day 15: Session-Scoped Vaults & Multi-user Isolation
1. **Goal**: Ensure that tokens and data from one user session do not leak into another.
2. **Concepts to learn**: Multi-tenant data architectures, session management.
3. **Files to modify**: `vault/token_store.py`, `vault/vault.py`.
4. **Code to write**: Enforce `session_id` in all Redis keys (e.g., `SESSION_ID:TYPE:NAME`). Update `TokenStore` to require `session_id`.
5. **Tests to create**: `tests/test_session_isolation.py`.
6. **Documentation to update**: `docs/architecture.md` (Data Isolation Strategy).
7. **Expected Git commit**: `feat(vault): implement session-scoped vaults and user isolation`

#### Day 16: TTL Expiration & Cleanup Mechanisms
1. **Goal**: Implement automatic expiration of sensitive mappings to comply with minimal data retention policies.
2. **Concepts to learn**: Redis TTL (`EX` / `EXPIRE`), cache invalidation.
3. **Files to modify**: `vault/token_store.py`.
4. **Code to write**: Attach TTLs to every key written in `TokenStore`. Add `Vault.clear_session(session_id)` method.
5. **Tests to create**: `tests/test_storage.py` (update to test TTL application).
6. **Documentation to update**: `docs/redis_notes.md` (Document TTL policy).
7. **Expected Git commit**: `feat(vault): enforce TTL expiration and implement session cleanup`

#### Day 17: Redis Performance Optimization & Cache Strategy
1. **Goal**: Minimize latency introduced by the Vault engine by optimizing Redis interactions.
2. **Concepts to learn**: Redis Connection Pools, pipelining, minimizing network round-trips.
3. **Files to modify**: `vault/redis_client.py`, `vault/token_store.py`.
4. **Code to write**: Implement persistent connection pooling in `redis_client.py`. Group read/write operations using Redis pipelines in `TokenStore`.
5. **Tests to create**: `tests/test_performance.py` (benchmark pipelined vs non-pipelined operations).
6. **Documentation to update**: `docs/redis_notes.md` (Optimization strategies).
7. **Expected Git commit**: `perf(vault): implement connection pooling and Redis pipelining`

#### Day 18: Latency Measurement & Benchmarking
1. **Goal**: Quantify the proxy's performance to ensure it meets production millisecond requirements.
2. **Concepts to learn**: Code profiling, latency metrics.
3. **Files to modify**: `vault/vault.py`.
4. **Code to write**: Add lightweight telemetry/timing decorators around `redact_note` and `restore_note`.
5. **Tests to create**: `tests/test_latency.py` (assert that redaction of standard notes takes < 50ms).
6. **Documentation to update**: `docs/architecture.md` (Add Performance SLAs).
7. **Expected Git commit**: `test(vault): implement latency measurement and benchmarking suite`

#### Day 19: Secure Integration Hooks
1. **Goal**: Expose a secure, clean API for the `main_pipeline.py` (which we aren't writing, but must support).
2. **Concepts to learn**: API contract design, defensive API boundaries.
3. **Files to modify**: `vault/vault.py`, `vault/__init__.py`.
4. **Code to write**: Finalize typing, add custom Exception classes (`VaultError`, `TokenNotFoundError`) for clean error handling by the pipeline.
5. **Tests to create**: `tests/test_vault.py` (test error handling and exception bubbling).
6. **Documentation to update**: `docs/architecture.md` (Pipeline Integration Contract).
7. **Expected Git commit**: `feat(vault): finalize secure integration API and error handling`

#### Day 20: Re-identification Risk Analysis
1. **Goal**: Build automated checks to verify the statistical safety of the pseudonymized output.
2. **Concepts to learn**: k-anonymity, l-diversity basics, HIPAA Safe Harbor metrics.
3. **Files to modify**: `vault/risk_analyzer.py` [NEW].
4. **Code to write**: `RiskAnalyzer.calculate_risk(original, redacted)` to verify that specific patterns (like SSNs or emails) are entirely absent from the redacted text.
5. **Tests to create**: `tests/test_risk_analyzer.py`.
6. **Documentation to update**: `docs/risk_analysis.md` [NEW].
7. **Expected Git commit**: `feat(vault): implement automated re-identification risk metrics`

#### Day 21: Week 3 Integration & Bug Bash
1. **Goal**: Resolve any integration bugs and ensure Session management works perfectly with the text engine.
2. **Concepts to learn**: System debugging, edge case discovery.
3. **Files to modify**: Various in `vault/`.
4. **Code to write**: Bug fixes.
5. **Tests to create**: Complex end-to-end tests involving multiple sessions concurrently.
6. **Documentation to update**: `README.md` (Troubleshooting).
7. **Expected Git commit**: `fix(vault): week 3 integration fixes and multi-session stabilization`

---

### WEEK 4: Hardening, Compliance & Delivery

#### Day 22: Unit Test Coverage Expansion
1. **Goal**: Achieve >95% test coverage for the Vault engine.
2. **Concepts to learn**: Code coverage tools (`pytest-cov`).
3. **Files to modify**: `tests/*.py`.
4. **Code to write**: Add missing tests for edge cases, error conditions, and Redis failure states.
5. **Tests to create**: Extensive unit tests.
6. **Documentation to update**: None.
7. **Expected Git commit**: `test(vault): expand unit test coverage to meet >95% threshold`

#### Day 23: PHI Leakage Testing
1. **Goal**: Implement tests specifically designed to force the vault to fail open and leak PHI, proving it handles these safely.
2. **Concepts to learn**: Negative testing, fail-safe vs fail-open.
3. **Files to modify**: `tests/test_security.py` [NEW].
4. **Code to write**: Tests that mock Redis crashes, invalid tokens, and malformed text, asserting that raw PHI is *never* output on failure.
5. **Tests to create**: `tests/test_security.py`.
6. **Documentation to update**: `docs/architecture.md` (Fail-safe architecture).
7. **Expected Git commit**: `test(vault): implement rigorous PHI leakage and fail-safe testing`

#### Day 24: Vault Penetration Testing & Security Audit
1. **Goal**: Ensure the Redis store and Vault code are secure against common vulnerabilities.
2. **Concepts to learn**: Data-at-rest encryption concepts, code injection.
3. **Files to modify**: `vault/redis_client.py`.
4. **Code to write**: Enforce secure Redis configurations (e.g., rejecting unauthenticated connections if required). Add input sanitization to token parameters.
5. **Tests to create**: `tests/test_security.py` (injection attempts).
6. **Documentation to update**: `docs/architecture.md` (Security Audit Log).
7. **Expected Git commit**: `sec(vault): harden Redis connections and sanitize inputs`

#### Day 25: Final Optimization & Profiling
1. **Goal**: Final pass on code quality, memory leaks, and performance.
2. **Concepts to learn**: Python memory profiling.
3. **Files to modify**: `vault/*.py`.
4. **Code to write**: Refactor any inefficient loops or string concatenations.
5. **Tests to create**: None.
6. **Documentation to update**: None.
7. **Expected Git commit**: `refactor(vault): final code optimization and profiling adjustments`

#### Day 26: HIPAA Alignment Report
1. **Goal**: Document exactly how the Vault meets HIPAA requirements.
2. **Concepts to learn**: HIPAA Privacy Rule, technical safeguards.
3. **Files to modify**: None.
4. **Code to write**: None.
5. **Tests to create**: None.
6. **Documentation to update**: `docs/hipaa_alignment.md` [NEW]. Write out the 18 HIPAA identifiers and how the system addresses them.
7. **Expected Git commit**: `docs(vault): add HIPAA alignment report`

#### Day 27: Safe Harbor Mapping Document
1. **Goal**: Detail the mapping strategy for Safe Harbor compliance.
2. **Concepts to learn**: Safe Harbor de-identification standards.
3. **Files to modify**: None.
4. **Code to write**: None.
5. **Tests to create**: None.
6. **Documentation to update**: `docs/safe_harbor_mapping.md` [NEW]. Document how dates, zip codes, and ages over 89 are technically handled by the vault mappings.
7. **Expected Git commit**: `docs(vault): add Safe Harbor mapping documentation`

#### Day 28: Final README Updates
1. **Goal**: Polish the repository documentation for a flawless handoff.
2. **Concepts to learn**: Technical writing, developer onboarding.
3. **Files to modify**: `README.md`.
4. **Code to write**: None.
5. **Tests to create**: None.
6. **Documentation to update**: `README.md` (Add Vault architecture summary, installation instructions, and testing commands).
7. **Expected Git commit**: `docs: finalize README with Vault architecture and usage instructions`

#### Day 29: Final PR Preparation
1. **Goal**: Prepare the final Pull Request with all Week 2-4 changes.
2. **Concepts to learn**: Git squashing, PR descriptions.
3. **Files to modify**: None.
4. **Code to write**: Clean up any `TODO` comments or print statements.
5. **Tests to create**: Verify all tests pass locally.
6. **Documentation to update**: None.
7. **Expected Git commit**: `chore: final cleanup and preparation for version 1.0 release`

#### Day 30: Project Wrap-up & Delivery
1. **Goal**: Final review of the entire vault engine against the original problem statement.
2. **Concepts to learn**: Project retrospective.
3. **Files to modify**: None.
4. **Code to write**: None.
5. **Tests to create**: None.
6. **Documentation to update**: None.
7. **Expected Git commit**: `chore: project completion and final tag`
