# Next Steps – Phase 1 & 2 Follow-Up

1. **Execute Automated Tests**
   - On a machine with network access run:
     ```bash
     python -m pip install .[test]
     python -m pytest
     ```
   - Capture results and address any regressions.

2. **Runtime Verification**
   - With `docker compose up --build` running, perform:
     - CLI scan: `lcc scan . --format json --output report.json --policy permissive --context saas`.
     - Policy regression: `lcc policy test permissive report.json --context saas`.
     - Dashboard smoke test at `http://localhost:3000`.
   - Confirm decision logs in `~/.lcc/decisions.jsonl`.

3. **OPA Bundle Refresh (Optional)**
   - If policies change, rebuild and reload:
     ```bash
     scripts/build_policy_bundle.py --output dist/policy.bundle.tar.gz
     docker compose restart opa
     ```

4. **Performance/Monitoring Enhancements (Deferred)**
   - Evaluate remaining Phase 2 “Should” items:
     - API response caching metrics.
     - Database query optimisation hooks.
     - Cache hit-rate dashboards using `Cache.get_metrics()`.

5. **Plan for Phase 3 Kick-off**
   - Review `docs/PRD-v1.1.md` Phase 3 epics and prepare backlog grooming once verification is complete.
