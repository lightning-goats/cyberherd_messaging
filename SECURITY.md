# Security Policy

`cyberherd_messaging` is a security-sensitive messaging integration project.

The software accepts, processes, queues, routes, or displays messages associated with the Lightning Goats / CyberHerd ecosystem and may interact with systems such as:

* LNbits;
* Lightning payments;
* Nostr;
* web applications;
* browser or OBS overlays;
* external messaging services;
* public APIs;
* automation consuming message events.

Because messages may originate from public or semi-public networks, nearly all externally supplied message content should be treated as untrusted.

A vulnerability may result in:

* unauthorized message publication;
* spoofed sender identity;
* duplicate or replayed messages;
* cross-site scripting;
* credential disclosure;
* message-queue denial of service;
* corruption of message ordering;
* false association between messages and Lightning payments;
* unauthorized use of external messaging accounts;
* unintended downstream automation.

Security vulnerabilities should be reported privately.

**Do not open a public GitHub issue containing details of an unpatched vulnerability.**

## Supported Versions

Security fixes are primarily provided for the latest maintained release and current development branch.

| Version                   | Supported   |
| ------------------------- | ----------- |
| `main` / latest release   | ✅           |
| Older maintained releases | Best effort |
| Unmaintained versions     | ❌           |
| Third-party forks         | ❌           |

Operators should run the latest stable release whenever practical.

# Reporting a Vulnerability

Use GitHub **Private Vulnerability Reporting** for this repository when available.

If Private Vulnerability Reporting is unavailable, contact the maintainers privately before publicly disclosing technical details.

A useful report should include:

* A clear description of the vulnerability.
* The affected version or commit.
* The affected module, endpoint, message source, queue, renderer, or external integration.
* Preconditions required for exploitation.
* Reproduction instructions.
* A minimal proof of concept where appropriate.
* Expected behavior.
* Observed behavior.
* Potential impact.
* Whether credentials, payments, message authenticity, privacy, or downstream automation may be affected.
* Relevant logs with secrets removed.
* Any proposed mitigation or patch.

Never include real:

* LNbits credentials;
* Nostr private keys;
* OAuth tokens;
* API keys;
* session tokens;
* external messaging credentials;
* database passwords;
* wallet secrets

in vulnerability reports.

# Security Model

`cyberherd_messaging` should be treated as a boundary between untrusted communication networks and trusted application behavior.

The preferred conceptual flow is:

```text
external message source
        ↓
authentication / verification
        ↓
validation
        ↓
normalization
        ↓
deduplication / replay protection
        ↓
message queue
        ↓
safe presentation or authorized outbound delivery
```

Messages must not bypass these stages merely because they arrive through a known integration.

A valid message is not automatically a trusted message.

A trusted identity is not automatically authorized to perform privileged actions.

# Trust Boundaries

Potentially untrusted inputs may originate from:

* Nostr relays;
* Lightning payment metadata;
* LNURL comments;
* HTTP requests;
* webhooks;
* browser clients;
* websocket clients;
* external social networks;
* external APIs;
* database records;
* configuration;
* imported historical messages.

Every transition across these boundaries should validate both:

1. **structure**, and
2. **semantic authorization**.

# Message Authenticity

Where an external protocol supports cryptographic authentication or signed events, signatures should be verified before sender identity is trusted.

For Nostr this includes verifying:

* event ID;
* Schnorr signature;
* public key;
* canonical serialization;
* expected event kind;
* relevant tags.

A valid cryptographic signature proves that the message was authorized by the corresponding private key.

It does **not** prove that the key is permitted to perform every CyberHerd action.

Authentication and authorization are separate.

# Nostr Security

Nostr events must be treated as untrusted until verified.

Validate:

* event signature;
* event ID;
* event kind;
* tags;
* content length;
* timestamps;
* expiration where applicable.

Do not trust caller-supplied:

* event IDs;
* public keys;
* relay metadata

without appropriate verification.

Unsupported event kinds should be rejected or ignored.

# Nostr Private Keys

If the application publishes Nostr events, private keys must remain server-side.

Never:

* send an `nsec` to browser JavaScript;
* log an `nsec`;
* return it from an API;
* expose it through debug output;
* include it in exceptions;
* commit it to Git.

Where possible, use a dedicated signing service or restricted signing boundary rather than directly exposing long-lived private keys to Internet-facing message-processing code.

# External Messaging Accounts

Credentials for external messaging platforms must be treated as high-value secrets.

Examples include:

* OAuth access tokens;
* refresh tokens;
* API keys;
* API secrets;
* bearer tokens;
* webhook signing secrets.

A compromise of a messaging token may allow an attacker to impersonate the project publicly even when no Lightning funds are at risk.

Use least-privileged credentials wherever the external service supports permission scopes.

# Outbound Message Authorization

Inbound messages must never automatically gain authorization to publish messages externally.

The system should distinguish:

```text
message received
```

from:

```text
message approved for outbound publication
```

Where external publication has material consequences, apply an explicit policy layer.

# Payment-Associated Messages

If messages are associated with Lightning payments, the message must be linked to an authoritative settled payment record.

Security issues include:

* attributing a message to an unpaid invoice;
* spoofing payment state;
* attaching a message to someone else's payment;
* processing one payment's message multiple times;
* accepting caller-provided payment status as authoritative.

The browser must not be the authority for settlement state.

LNbits or the Lightning backend should be used to verify payment settlement.

# Payment Idempotency

One settled payment should not cause duplicate message effects unless explicitly intended.

Possible duplicate effects include:

* repeated public display;
* repeated Nostr publication;
* repeated social-network posts;
* repeated notifications;
* repeated automation events.

Handlers must assume that:

* webhooks may retry;
* service processes may restart;
* network calls may time out after succeeding;
* the same event may arrive from multiple sources.

Use stable identifiers where practical, including:

* payment hash;
* LNbits checking ID;
* Nostr event ID;
* internal message ID;
* external platform event ID.

# Replay Protection

Cryptographically valid messages may still be unsafe when replayed.

Replay-sensitive workflows should consider:

* event IDs;
* timestamps;
* expiration;
* nonces;
* persisted processed-event records.

A restarted process should not forget important replay protection if duplicate publication or automation would be harmful.

# Message Identity

Every normalized message should ideally have a stable identity.

Conceptually:

```text
source
source_event_id
normalized_message_id
received_at
author
content
status
```

Stable identities improve:

* idempotency;
* queue integrity;
* debugging;
* auditability.

# Message Normalization

Messages from different protocols should be normalized before downstream processing.

Normalization should not silently remove security-relevant provenance.

For example, preserve:

* source network;
* original event ID;
* verified sender identity;
* payment association;
* timestamp;
* authentication result.

Downstream code should be able to distinguish:

```text
verified Nostr message
```

from:

```text
anonymous web submission
```

rather than treating both as generic strings.

# Safe Rendering

All message content should be treated as untrusted when displayed in:

* web pages;
* OBS Browser Sources;
* dashboards;
* administrative interfaces.

Never assume a message is safe HTML.

Avoid patterns equivalent to:

```javascript
element.innerHTML = message
```

Prefer:

```javascript
element.textContent = message
```

or framework-native escaped output.

If rich text is deliberately supported, use an allowlist-based sanitizer.

# Cross-Site Scripting

Potential XSS sources include:

* payment comments;
* Nostr content;
* usernames;
* profile names;
* external social messages;
* URLs;
* announcement text.

Test explicitly for payloads involving:

```html
<script>
<img onerror=...>
<svg onload=...>
```

and encoded equivalents.

A signed Nostr event is still untrusted HTML.

# CSS Injection

If messages are ever inserted into style attributes or dynamic CSS, validate them separately.

HTML escaping alone does not necessarily make content safe for CSS contexts.

Avoid placing user-controlled strings inside dynamic CSS.

# URL Safety

URLs embedded in messages should not automatically become trusted links.

If links are rendered, consider:

* allowed protocols;
* `javascript:` URLs;
* `data:` URLs;
* phishing;
* opener behavior.

Restrict URL schemes where practical to expected protocols such as:

```text
https:
http:
```

depending on application requirements.

# Unicode and Control Characters

Attackers may use:

* bidirectional Unicode controls;
* zero-width characters;
* terminal control sequences;
* unusual newlines

to disguise messages or log output.

Where security-sensitive identity information is displayed, consider sanitizing or visibly representing dangerous control characters.

# Message Length Limits

Apply explicit length limits to publicly supplied messages.

This protects against:

* memory exhaustion;
* layout breakage;
* queue abuse;
* oversized outbound API requests;
* excessive logging.

Different sources may need different limits.

# Queue Security

Message queues should have clearly defined behavior.

Security-relevant queue properties include:

* bounded size;
* deterministic ordering;
* duplicate suppression;
* message isolation;
* failure recovery;
* priority behavior.

An attacker should not be able to create an unlimited queue through public messages.

# Queue Ordering

When messages are intended to display serially, only one message should occupy the relevant display slot at a time unless concurrent presentation is explicitly intended.

Avoid race conditions where:

```text
message A begins
message B arrives
message B overwrites A
message C starts simultaneously
```

State transitions should be explicit.

# Queue Persistence

If losing queued messages during restart is unacceptable, queue state should be persisted.

If persisting the queue, validate records when reading them back.

Persistent data must still be treated as potentially malformed.

# Queue Failure Handling

A malformed or undeliverable message must not block the entire queue indefinitely.

Use:

* bounded retries;
* retry delays;
* failure states;
* dead-letter handling where appropriate.

Avoid infinite retries.

# Duplicate Delivery

Outbound message APIs may return ambiguous outcomes.

For example:

```text
send request
    ↓
remote service publishes message
    ↓
connection fails
    ↓
client sees timeout
```

Blind retry can create duplicate public posts.

Where supported, use:

* provider idempotency keys;
* stable message IDs;
* reconciliation before retry.

# Rate Limiting

Public message-ingestion endpoints should be rate limited where appropriate.

Consider separate limits for:

* anonymous users;
* authenticated users;
* IP addresses;
* public keys;
* payment-associated messages.

Rate limiting should not replace authentication or authorization.

# Spam and Abuse

Spam is primarily an operational concern, but becomes a security issue when it causes:

* denial of service;
* queue exhaustion;
* excessive API charges;
* automated external publication;
* bypass of intended payment requirements.

Use appropriate:

* rate limits;
* payment requirements;
* allowlists;
* moderation;
* queue limits.

# Webhook Authentication

External webhooks should be authenticated where the provider supports it.

Validate:

* cryptographic signatures;
* shared secrets;
* timestamp freshness;
* expected source;
* replay identifiers.

Knowledge of the webhook URL alone should not imply authorization.

# Webhook Idempotency

Even authenticated webhooks may be delivered repeatedly.

Webhook handlers must be idempotent.

Use stable provider event IDs whenever available.

# HTTP Input Validation

Treat all:

* query parameters;
* form inputs;
* JSON payloads;
* route parameters;
* headers

as untrusted.

Use schema validation where possible.

Reject malformed fields rather than guessing.

# API Authorization

Administrative or privileged API endpoints must verify authorization server-side.

Examples include operations to:

* delete messages;
* force publication;
* modify queues;
* alter integration configuration;
* retry failed messages;
* manage credentials.

A hidden UI button is not an authorization mechanism.

# Authentication Tokens

Tokens should:

* contain sufficient entropy;
* be generated using a cryptographically secure RNG;
* be stored securely;
* be rotatable;
* never appear in URLs;
* never be logged.

Compare secret tokens using security-appropriate mechanisms.

# CORS

Do not enable unrestricted CORS for authenticated management endpoints.

Public presentation endpoints and privileged API endpoints should have separate policies.

# CSRF

Cookie-authenticated state-changing endpoints should be protected against Cross-Site Request Forgery.

Examples include:

* deleting messages;
* changing integration settings;
* manually publishing content;
* changing queue state.

GET requests should not perform privileged state changes.

# Browser / OBS Clients

OBS Browser Sources and public browser clients should be considered presentation clients only.

They should not receive:

* LNbits keys;
* Nostr private keys;
* OAuth tokens;
* administrative bearer tokens;
* database credentials.

A compromised OBS Browser Source should not gain control over backend messaging integrations.

# WebSockets

If real-time updates use WebSockets:

* validate subscription scope;
* authenticate privileged channels;
* bound message sizes;
* limit connections;
* validate incoming client messages.

Do not assume WebSocket establishment itself grants authorization.

# Cross-Client Data Leakage

If multiple audiences or message streams exist, ensure that a subscriber receives only the streams it is authorized to access.

Do not rely solely on frontend filtering.

# Secret Management

Secrets must never be committed to Git.

Examples include:

```text
LNbits API keys
Nostr private keys
OAuth tokens
API secrets
webhook secrets
session secrets
database passwords
```

Example configuration should use obvious placeholders.

# Logging

Logs should be sufficient to reconstruct message processing without exposing secrets.

Useful fields may include:

* normalized message ID;
* source;
* source event ID;
* processing status;
* queue status;
* delivery result;
* authentication result.

Do not log:

* API secrets;
* private keys;
* full authorization headers;
* refresh tokens;
* session credentials.

Avoid unnecessary logging of private message content.

# Error Messages

Public errors should not expose:

* stack traces;
* internal URLs;
* API credentials;
* tokens;
* database queries;
* filesystem paths;
* complete upstream responses.

Detailed diagnostics belong in protected server logs.

# External API Responses

Treat external API responses as untrusted.

Validate:

* HTTP status;
* response size;
* expected schema;
* content types;
* identifiers.

Do not assume external APIs always return valid JSON or expected fields.

# Timeouts

All external network requests should have explicit timeouts.

Never permit an external API to block a queue indefinitely.

# Retry Policy

Retries should be:

* bounded;
* delayed appropriately;
* aware of idempotency.

Avoid retry storms when an external service becomes unavailable.

Exponential backoff with an upper bound may be appropriate.

# Circuit Breaking

For repeatedly failing providers, temporarily suppressing outbound delivery may be safer than indefinitely retrying.

Failure of one provider should not necessarily halt unrelated message channels.

# SSRF

If users or administrators can configure external URLs, protect against Server-Side Request Forgery.

Do not permit untrusted URLs to access:

* localhost;
* private network ranges;
* cloud metadata endpoints;
* LNbits internal APIs;
* Lightning node RPC services;
* other container services.

# Command Injection

Never pass untrusted message text into shell commands.

Avoid constructs equivalent to:

```python
os.system("some_command " + message)
```

If external processes are required, pass arguments using structured process APIs and fixed executable paths.

# Template Injection

Do not compile or evaluate user-controlled messages as:

* templates;
* Python code;
* JavaScript;
* expressions.

Messages are data.

They should remain data throughout the processing pipeline.

# Database Security

Database queries should use parameter binding.

Never construct SQL by concatenating user-supplied message values.

Persisted message records should preserve enough provenance to support auditing.

# Database Isolation

If messages belong to different users, wallets, or contexts, authorization boundaries must be enforced at the backend.

Changing a message ID in a URL must not permit access to another user's private record.

# Concurrency

Concurrent workers can create duplicate publication or queue corruption even when the underlying programming language prevents memory races.

Protect check-and-act sequences.

For example:

```text
worker A checks "not sent"
worker B checks "not sent"
worker A sends
worker B sends
```

Use:

* atomic state transitions;
* transactions;
* locks;
* uniqueness constraints;
* leases

where appropriate.

# Message State Machine

Message status should preferably follow explicit states such as:

```text
received
validated
queued
processing
sent
failed
```

Transitions should be controlled.

Avoid ambiguous combinations such as:

```text
sent = false
processing = false
retry = true
published_id = non-null
```

where software cannot determine the actual state.

# Auditability

For outbound messages, the system should ideally be able to determine:

* what content was intended;
* which source produced it;
* who authorized publication;
* which destination received it;
* when sending was attempted;
* the provider's resulting event ID;
* whether retry occurred.

This is especially useful when public social accounts are involved.

# Privacy

Messages may contain personally identifying or sensitive information.

Collect and retain only what the application requires.

Do not automatically assume that content attached to a payment is appropriate for:

* indefinite storage;
* public display;
* reposting to social networks.

Different publication contexts may require different consent or moderation policies.

# Data Retention

If historical messages are retained, document or implement appropriate retention behavior.

Deleting a message from a display queue may not remove it from:

* logs;
* databases;
* external social networks;
* relay networks.

Operators should understand those distinctions.

# Downstream Automation

If other systems consume message events, message authenticity does not automatically grant permission for downstream physical or financial actions.

A safe boundary is:

```text
message
   ↓
authenticated source
   ↓
validated message
   ↓
separate automation policy
   ↓
authorized action
```

Do not make arbitrary message text executable commands.

# Dependencies and Supply Chain

Python, JavaScript, Nostr, API, and other dependencies are part of the trusted computing base.

Review new dependencies for:

* maintenance status;
* ownership;
* release history;
* transitive dependency count;
* install-time behavior;
* known vulnerabilities.

Use lockfiles where supported.

# GitHub Actions

CI workflows should use least privilege.

Prefer:

```yaml
permissions:
  contents: read
```

and grant additional permissions only where necessary.

Never expose production messaging credentials to untrusted pull-request workflows.

Pin security-sensitive third-party Actions to trusted releases or commit SHAs where practical.

# Testing Expectations

Security-sensitive testing should include:

* invalid Nostr signatures;
* spoofed sender identities;
* replayed Nostr events;
* duplicate Lightning payment events;
* duplicate webhooks;
* simultaneous queue workers;
* XSS payloads;
* HTML injection;
* oversized messages;
* malformed API responses;
* webhook signature failures;
* unauthorized administration requests;
* external API timeouts;
* ambiguous send outcomes;
* restart during queue processing.

# Security Invariants

Important properties should be directly testable.

Examples include:

```text
Invalid Nostr signature → no trusted sender identity.
```

```text
Duplicate source event → no duplicate outbound publication.
```

```text
One payment → no more than one corresponding message effect unless explicitly configured.
```

```text
User-controlled message → never executable HTML or JavaScript.
```

```text
Public presentation client → never receives integration secrets.
```

```text
Unauthorized caller → cannot publish through project messaging accounts.
```

```text
Malformed message → cannot block the entire queue.
```

```text
One provider failure → does not corrupt unrelated message streams.
```

# Fail-Safe Behavior

When authenticity or authorization is ambiguous:

**do not perform privileged publication.**

When payment association cannot be verified:

**do not treat the message as payment-authorized.**

When an external provider returns an ambiguous result:

**reconcile before blindly retrying where possible.**

When a message is malformed:

**reject or quarantine it without blocking unrelated processing.**

# Production Deployment

Recommended practice:

1. Run the service under a dedicated, minimally privileged account.
2. Protect integration secrets.
3. Use HTTPS for Internet-facing endpoints.
4. Keep administrative APIs private where practical.
5. Apply explicit queue and message-size limits.
6. Enable authentication on privileged endpoints.
7. Monitor failed and duplicate deliveries.
8. Test messaging integrations with non-production accounts when possible.
9. Maintain a way to disable each outbound integration independently.
10. Rotate API credentials immediately after suspected compromise.

# Incident Response

If an external messaging credential may have been exposed:

1. Disable the affected integration.
2. Revoke the credential at the provider.
3. Generate new credentials.
4. Review outbound message history.
5. Inspect logs for unauthorized use.
6. Patch the underlying vulnerability.
7. Restore the integration only after validation.

If a Nostr private key may have been exposed, consider that key permanently compromised and rotate the identity where operationally possible.

# Out of Scope

The following normally do not constitute security vulnerabilities:

* ordinary spam that does not bypass intended controls;
* objectionable but technically valid public messages;
* external platform outages;
* unsupported historical versions;
* generic dependency CVEs without demonstrated impact;
* theoretical vulnerabilities with no plausible exploitation path;
* automated scanner results without validation.

Spam becomes security-relevant when it enables:

* denial of service;
* unauthorized publication;
* resource exhaustion;
* billing abuse;
* policy bypass.

# Responsible Disclosure

We appreciate researchers who:

* report vulnerabilities privately;
* use test identities and accounts where practical;
* avoid publishing unauthorized content through production accounts;
* avoid exposing real credentials;
* minimize interaction with production users;
* allow reasonable remediation time;
* coordinate disclosure where downstream installations may be affected.

Security testing must not intentionally:

* impersonate the project's public identities;
* publish harmful messages through production accounts;
* steal Lightning funds;
* expose private user information;
* overload production relays or services;
* trigger downstream physical actions without authorization.

# Security Is a Process

`cyberherd_messaging` connects several systems with different trust models.

A secure implementation must preserve the distinctions between:

```text
message content
message authenticity
sender identity
payment verification
publication authorization
downstream side effects
```

Those concepts must not be collapsed into one another.

The most important security goals are:

* verify sender identity where possible;
* preserve source provenance;
* prevent replay and duplicate delivery;
* keep external account credentials secret;
* render messages safely;
* isolate public clients from privileged controls;
* bound queues and retries;
* require explicit authorization for outbound publication;
* prevent arbitrary messages from becoming executable commands.

If you identify behavior that permits sender spoofing, unauthorized publication, duplicate paid-message processing, credential exposure, cross-site scripting, queue exhaustion, replay of privileged events, or another expansion of an untrusted message into unauthorized system behavior, please report it privately.
