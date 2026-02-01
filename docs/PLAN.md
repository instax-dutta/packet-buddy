# Optimization Plan: Neon DB Sync Efficiency & Resilience

## 1. Executive Summary
The goal is to reduce Neon DB compute usage and ensure system resilience against power/internet outages. The current implementation of `NeonSync` in `src/core/sync.py` performs high-frequency, row-by-row updates, leading to excessive database queries (O(N)) and keeping the Neon instance active unnecessarily. We will refactor this to use in-memory batch aggregation and prolonged sync intervals.

## 2. Problem Analysis
-   **High Query Count**: For a batch of 1000 logs, the current system executes ~2001 queries (1 bulk insert + 2000 individual aggregate updates).
-   **Active Compute**: A 30-second sync interval prevents serverless databases (like Neon) from scaling to zero (sleeping), incurring higher costs.
-   **Inefficient Bandwidth**: Sending granular updates consumes more bandwidth and connection overhead.

## 3. Proposed Solution

### 3.1. Batch Aggregation Strategy
Instead of updating aggregates for every log row:
1.  Fetch 1000 logs from SQLite.
2.  In Python, calculate the **sum** of `bytes_sent` and `bytes_received` grouped by `date`.
3.  Perform a single `INSERT ... ON CONFLICT DO UPDATE` query for each unique date (usually just 1 or 2 rows per batch).
4.  This reduces aggregate queries from 1000 to ~1-2.

### 3.2. Optimized Sync Interval
-   Increase default sync interval from 30s to **300s (5 minutes)** or even **15 minutes**.
-   This allows Neon to autoscale to zero during idle times.
-   **Trade-off**: Data on the dashboard might be up to 15 minutes delayed for *other* devices, but local data remains real-time. This is an acceptable trade-off for "lightweight" and "cost-effective" goals.

### 3.3. Resilience & Outage Handling
-   **Connection Check**: Implement a lightweight "pre-flight" check (e.g., DNS resolution or ping) before attempting to connect to DB, to avoid timeouts hanging the thread.
-   **Transaction Safety**: Ensure the `mark_logs_synced` happens only after the *entire* batch transaction (logs + aggregates) is committed.
-   **Backoff Strategy**: Keep the exponential backoff for retries.

### 3.4. Lightweight Constraints
-   The in-memory aggregation uses a simple dictionary. For 1000 logs, additional memory usage is negligible (< 1MB).
-   Processing logic remains simple.

## 4. Implementation Steps

### Phase 1: Foundation (Backend)
-   [ ] Modify `src/core/sync.py`:
    -   Implement `_aggregate_batch(logs)` helper.
    -   Refactor `_sync_data` to use aggregation.
    -   Update SQL queries to batch updates.

### Phase 2: Configuration & Resilience (DevOps/Backend)
-   [ ] Update `src/utils/config.py` (or default values) to change default sync interval to 300s.
-   [ ] Add connection availability check wrapper.

## 5. Verification
-   **Unit Test**: Mock the storage and verify that 100 logs result in ~3 DB calls instead of ~200.
-   **Integration**: Run offline/online toggle test.
