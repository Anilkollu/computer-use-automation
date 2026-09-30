# 1. Architecture

The system is a small end-to-end computer-use automation pipeline with two distinct phases: discovery and replay.

During discovery, the system accepts a natural-language goal and operates a live mock banking UI using an LLM-driven observe → decide → act loop. Playwright provides the browser control layer. The LLM observes the current page state, chooses an action, and the browser layer executes it.

The successful discovery run is converted into a structured capability artifact. The artifact is intentionally separated from the raw model transcript so that it represents the reusable business capability rather than the model's reasoning process.

During replay, the saved artifact becomes the execution plan. The replay engine performs the recorded actions directly through Playwright and does not ask the LLM to make decisions. This produces a deterministic production-style execution path.

The main boundary is:

```text
LLM discovery
     |
     v
Capability artifact
     |
     v
Deterministic replay
     |
     v
Surface adapter / Playwright
```

A local mock banking application is used as the concrete target. This keeps the implementation safe and reproducible while exercising a multi-step business workflow.

The implementation intentionally remains a single-process, lightweight system. The assignment emphasizes a complete vertical slice rather than scaling infrastructure.

# 2. Artifact schema

The saved capability is versioned and serializable JSON.

The artifact contains:

* schema version
* capability ID
* capability version
* typed input parameters
* ordered actions
* semantic target information
* typed outputs
* checkpoint/success condition

The payment capability accepts:

```text
fromAccount: string
toAccount: string
amount: number
username: secret string
password: secret string
```

The action representation uses semantic targets such as:

```json
{
  "action": "click",
  "target": {
    "role": "button",
    "name": "Submit Payment"
  }
}
```

and:

```json
{
  "action": "fill",
  "target": {
    "label": "From Account"
  },
  "value": "{{fromAccount}}"
}
```

This avoids recording brittle generated CSS selectors when semantic labels, roles, and names are available.

The artifact declares outputs such as:

```text
transactionId: string
status: string
```

and verifies the checkpoint:

```text
PAYMENT SUCCESSFUL
```

Credentials are represented as secret parameters rather than being persisted as plaintext credential values in the artifact.

Versioning makes the artifact reviewable and gives the replay layer a clear capability identity.

# 3. Determinism & error handling

Discovery uses the LLM because the system must determine how to accomplish the goal on the first run.

Replay intentionally does not use the LLM.

A successful replay reports:

```text
LLM calls: 0
```

The replay engine follows the saved ordered steps and uses semantic controls such as labels, roles, and accessible names. It verifies the result through an explicit checkpoint instead of assuming that the final click succeeded.

The replay result contract distinguishes three important classes of outcomes.

## Success

The workflow completes and the declared outputs are returned.

Example:

```text
PAYMENT SUCCESSFUL
Transaction ID: TXN-...
Status: COMPLETED
```

## Business outcome

The automation completed the requested interaction, but the business system returned an expected business result.

Example:

```text
INSUFFICIENT FUNDS
```

This is reported as:

```text
BUSINESS_OUTCOME
```

rather than being treated as a software crash.

## Recoverable error

A known transient condition is detected and the replay performs a bounded retry.

Example:

```text
SERVICE TEMPORARILY UNAVAILABLE
```

The replay retries the Submit Payment operation once and verifies the resulting checkpoint.

## Hard failure

A condition that cannot safely be recovered automatically stops execution.

Example:

```text
PERMISSION DENIED
```

The result identifies the failing step and reason.

This separation prevents the replay engine from blindly continuing after a runtime condition.

The implementation also produces structured replay events containing the capability, version, scenario, step, action, result, and output information.

# 4. Heterogeneity & multi-tenant

The implementation uses a browser-based mock application as the concrete surface, but the artifact is intentionally separated from the perception/action mechanism.

The replay engine can be viewed as consuming a surface adapter with operations such as:

```text
navigate
click
fill
read
wait
checkpoint
```

A modern web adapter can implement those operations with Playwright.

A legacy web adapter could implement the same conceptual operations using accessibility-tree or browser automation techniques where semantic DOM selectors are unavailable.

A desktop adapter could implement the same contract through OS-level or accessibility APIs.

The artifact therefore describes the intended control and target semantics rather than encoding a single automation library into the business capability.

For multi-tenant reuse, an artifact would be associated with application/vendor/version metadata. Institutions using the same underlying vendor application could share a base capability while allowing controlled tenant-specific locator or configuration overrides.

Replay would validate compatibility before execution and record the application/version context in evidence. If a tenant-specific version cannot safely satisfy the recorded targets, the capability should fail clearly or escalate rather than silently performing an incorrect action.

The assignment explicitly does not require implementing the multi-tenant or desktop infrastructure, so these are design seams rather than separate production systems.

# 5. Escalation & handoff

The system supports a real human-required path using the same browser session.

When the payment surface reports:

```text
HUMAN APPROVAL REQUIRED
```

the replay does not silently continue.

It emits a structured human handoff event containing:

* capability
* current step
* reason
* current browser context

The automation pauses and the browser remains active.

The human can intervene in that existing session.

After intervention, the automation resumes using the same browser session rather than starting a new session. The post-human result is then checked using the normal checkpoint mechanism.

The evidence records:

```text
human_handoff
human_resumed
replay_success
```

This models the required control-transfer seam while keeping the operator interface intentionally minimal.

A production version could expose the same session through a controlled operator console, but a full real-time co-browsing system is outside the scope of this implementation.

# 6. Safety

The system uses an explicit URL allowlist.

The mock banking application origin is allowed:

```text
http://127.0.0.1:3000
```

A non-allowlisted origin is rejected before browser automation proceeds.

The local mock application is used instead of a real banking system, so no real financial accounts or customer data are accessed.

Credentials are represented as secret parameters and are not intentionally written to the capability artifact.

The system also separates ordinary browser actions from policy decisions so that a production implementation could classify risky or irreversible actions and require confirmation or human approval before execution.

For the demonstration, payment submission is intentionally exercised only against the local mock system.

# 7. Cuts

The implementation deliberately focuses on the required vertical slice.

The following were intentionally not built:

* Spring Boot backend
* Kafka
* production database
* distributed queues
* Kubernetes or cloud infrastructure
* real banking integrations
* full multi-tenant infrastructure
* native desktop automation
* production operator console
* large-scale capability catalog

These were not necessary to demonstrate the core requirement.

The core implementation instead demonstrates the complete thread:

```text
goal
  ->
LLM discovery
  ->
successful UI interaction
  ->
structured capability
  ->
deterministic replay
  ->
LLM calls: 0
  ->
business/recoverable/hard outcomes
  ->
human handoff
  ->
evidence
```

With additional production time, the next areas would be stronger surface adapters, artifact approval/version compatibility, richer screenshots/traces, tenant-specific overrides, and a controlled operator interface.

The main design goal of this submission is to keep the core system small enough to understand while making the boundaries explicit enough to extend to the more heterogeneous banking environment described in the assignment.
