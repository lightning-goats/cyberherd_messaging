# CyberHerd Messaging Extension

A comprehensive messaging infrastructure extension for LNbits that provides dual-channel communication: Nostr protocol publishing and WebSocket broadcasting. Built with full NIP compliance for seamless integration with the Nostr ecosystem.

## Features

### 🌐 Dual-Channel Messaging
- **Nostr Publishing**: Publish notes to Nostr relays with full NIP-01, NIP-10, and NIP-19 compliance
- **WebSocket Broadcasting**: Real-time message delivery to connected clients via LNbits core

### 🔐 Security & Privacy
- Admin key authentication required for all publishing endpoints
- Per-user Nostr private key storage
- Global toggle for enabling/disabling Nostr publishing
- Secure key validation and sanitization

### 📝 Template System
- Database-backed message templates with category organization
- Dynamic template rendering with variable substitution
- User-specific template overrides
- Support for both simple and structured content

### ✅ Full Nostr NIP Compliance
- **NIP-01**: Basic protocol flow with proper event structure and signing
- **NIP-10**: Reply threading with correct e-tag markers (root, reply, mention)
- **NIP-19**: Bech32 encoding (npub, note, nprofile)
- **Kind 1**: Regular text notes
- **Kind 1311**: Replies to kind 30311 events (live chat/communities)

### 🎯 Advanced Features
- Automatic reply context detection and proper threading
- P-tag management for participant notifications
- A-tag support for parameterized replaceable events
- Relay hints for improved event routing
- Content sanitization and validation
- Goat profile integration with automatic p-tagging

## Installation

This extension is designed to work with LNbits and requires the `nostrclient` extension for Nostr publishing functionality.

### Dependencies
- LNbits core
- nostrclient extension (for Nostr publishing)
- bech32 library
- secp256k1

## Configuration

### Global Settings
- `nostr_publishing_enabled`: Toggle Nostr publishing on/off (default: enabled)

### Per-User Settings
- `nostr_private_key`: User-specific private key for signing Nostr events

## Usage

### Python API

#### Publish a Nostr Note

```python
from lnbits.extensions.cyberherd_messaging import services

# Simple note
await services.publish_note(
    "Hello from CyberHerd!",
    private_key_hex="your_64_char_hex_key"
)

# Reply with proper threading (NIP-10 compliant)
await services.publish_note(
    "This is a reply",
    e_tags=["event_id_to_reply_to"],
    p_tags=["pubkey_to_mention"],
    private_key_hex="your_64_char_hex_key",
    reply_relay="wss://relay.example.com"
)

# Reply to 30311 event (live chat)
await services.publish_note(
    "Chat reply",
    e_tags=["30311_event_id"],
    reply_to_30311_event="30311_event_id",
    reply_to_30311_a_tag="30311:pubkey:identifier",
    private_key_hex="your_64_char_hex_key"
)
```

#### Broadcast to WebSocket Clients

```python
# Send real-time message to connected clients
await services.send_to_websocket_clients(
    topic="cyberherd",
    message={
        "type": "update",
        "data": {"amount": 1000, "member": "Alice"}
    }
)
```

#### Render and Publish Template

```python
# Use stored template with dynamic values
await services.render_and_publish_template(
    user_id="user123",
    category="cyber_herd_join",
    key="welcome_1",
    values={"name": "Alice", "amount": 100},
    e_tags=["parent_event_id"],
    private_key="your_nsec_or_hex_key"
)

# Return rendered message for WebSocket without publishing
content, goat_data = await services.render_and_publish_template(
    user_id="user123",
    category="feeder_trigger",
    key="0",
    values={"new_amount": 5000},
    return_websocket_message=True
)
```

#### Build Message Bundles

```python
# Generate formatted messages for both Nostr and WebSocket
bundle = await services.build_message_bundle(
    event_type="cyber_herd",
    new_amount=100,
    cyber_herd_item={
        "display_name": "Alice",
        "pubkey": "hex_pubkey",
        "amount": 100
    },
    spots_remaining=5,
    user_id="user123"
)

print(bundle.nostr_content)      # Formatted for Nostr (with npub/note refs)
print(bundle.websocket_content)  # Formatted for WebSocket (with display names)
print(bundle.spots_info)         # Available spots text
print(bundle.headbutt_text)      # Headbutt challenge info
```

### REST API

All API endpoints require admin key authentication.

#### POST `/api/v1/publish`
Publish a note to Nostr relays.

```json
{
  "content": "Hello Nostr!",
  "e_tags": ["event_id_1", "event_id_2"],
  "p_tags": ["pubkey_1", "pubkey_2"],
  "reply_relay": "wss://relay.example.com"
}
```

#### POST `/api/v1/ws_broadcast`
Broadcast message to WebSocket clients.

```json
{
  "category": "update",
  "message": {
    "type": "payment_received",
    "amount": 1000
  }
}
```

#### POST `/api/v1/templates`
Create or update a message template.

```json
{
  "category": "cyber_herd_join",
  "key": "welcome_1",
  "content": "Welcome {name}! You joined with {amount} sats.",
  "reply_relay": "wss://relay.example.com"
}
```

#### POST `/api/v1/templates/publish`
Publish using a stored template.

```json
{
  "category": "cyber_herd_join",
  "key": "welcome_1",
  "e_tags": ["parent_event_id"],
  "p_tags": ["pubkey_to_mention"]
}
```

#### POST `/api/v1/templates/render`
Render template with values and publish or return for WebSocket.

```json
{
  "category": "cyber_herd_join",
  "key": "welcome_1",
  "values": {
    "name": "Alice",
    "amount": 100
  },
  "e_tags": ["parent_event_id"],
  "reply_to_30311_event": "30311_event_id",
  "reply_to_30311_a_tag": "30311:pubkey:identifier",
  "return_websocket_message": false
}
```

## NIP-10 Reply Threading

The extension implements proper NIP-10 reply threading:

### Direct Reply to Root
```python
# Single event ID = root marker only
await services.publish_note(
    "Reply to root",
    e_tags=["root_event_id"],
    private_key_hex="key"
)
# Results in: ["e", "root_event_id", "relay", "root"]
```

### Reply Chain
```python
# Multiple event IDs = root, reply, and mention markers
await services.publish_note(
    "Reply in thread",
    e_tags=["root_id", "parent_id", "mention_id"],
    private_key_hex="key"
)
# Results in:
# ["e", "root_id", "relay", "root"]
# ["e", "parent_id", "relay", "reply"]
# ["e", "mention_id", "", "mention"]
```

## Validation

### Enhanced Security Features

#### Pubkey Validation
All pubkeys are validated before use:
- Must be exactly 64 hex characters
- Regex pattern: `^[0-9a-f]{64}$`
- Invalid pubkeys are logged and skipped

#### Nprofile Validation
Nprofiles are validated via bech32 decoding:
- Must start with `nprofile1`
- Proper bech32 encoding verified
- HRP (human-readable part) must be "nprofile"
- Invalid nprofiles are rejected with debug logging

#### Private Key Sanitization
Private keys are sanitized and validated:
- Supports hex, nsec, or 0x-prefixed formats
- Whitespace and newlines stripped
- Must be exactly 64 hex characters after normalization

## Event Types

The extension supports building messages for various event types:

- `cyber_herd` / `new_member` - New member joins
- `member_increase` - Member increases contribution
- `feeder_triggered` / `feeder_trigger_bolt12` - Feeder activation
- `sats_received` / `sats_received_zap` - Payment received
- `cyber_herd_treats` - Treats distributed
- `headbutt_info` - Headbutt challenge info
- `headbutt_success` - Successful headbutt
- `headbutt_failure` - Failed headbutt attempt
- `daily_reset` / `herd_reset_message` - Daily/herd reset
- `interface_info` - Status/help information
- `kind_6_repost` / `kind_7_reaction` - Repost/reaction joins
- `kind_6_headbutt_failure` / `kind_7_headbutt_failure` - Headbutt failures
- `zapper_displaces_kind_6` / `zapper_displaces_kind_7` - Zapper displacement
- `feeding_regular` / `feeding_bonus` / `feeding_remainder` / `feeding_fallback` - Feeding events

## Database Schema

### Message Templates
```sql
CREATE TABLE cyberherd_messaging.message_templates (
    id INTEGER PRIMARY KEY,
    user_id TEXT NOT NULL,
    category TEXT NOT NULL,
    key TEXT NOT NULL,
    content TEXT NOT NULL,
    reply_relay TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    UNIQUE(user_id, category, key)
);
```

### Settings
```sql
CREATE TABLE cyberherd_messaging.settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE cyberherd_messaging.user_settings (
    user_id TEXT NOT NULL,
    key TEXT NOT NULL,
    value TEXT NOT NULL,
    PRIMARY KEY(user_id, key)
);
```

## Architecture

### Message Flow

1. **Template Rendering** → Dynamic content generation with variable substitution
2. **Validation** → Pubkey, nprofile, and content validation
3. **Message Building** → Dual-format message creation (Nostr + WebSocket)
4. **Publishing** → 
   - Nostr: Event signing and relay publishing
   - WebSocket: JSON serialization and broadcast

### Content Formatting

Messages are formatted differently for each channel:
- **Nostr**: Uses npub/note/nprofile references for discoverability
- **WebSocket**: Uses display names for readability

Example:
```python
# Nostr: "Welcome nostr:npub1abc...xyz!"
# WebSocket: "Welcome Alice!"
```

## Testing

Run the test suite:
```bash
pytest tests/
```

Key test files:
- `test_services.py` - Service function tests
- `test_models.py` - Model validation tests
- `test_view_payloads.py` - API endpoint tests

## Contributing

This extension follows strict NIP compliance. When contributing:

1. Maintain NIP-10 reply threading conventions
2. Validate all Nostr identifiers (pubkeys, nprofiles, event IDs)
3. Ensure dual-channel compatibility (Nostr + WebSocket)
4. Add tests for new functionality
5. Update documentation

## License

[Specify License]

## Support

For issues, questions, or contributions, please visit the [GitHub repository](https://github.com/lightning-goats/cyberherd_messaging).

## Related Projects

- [LNbits](https://github.com/lnbits/lnbits) - Lightning Network wallet/accounts system
- [nostrclient](https://github.com/lnbits/nostrclient-extension) - LNbits Nostr client extension
- [Nostr Protocol](https://github.com/nostr-protocol/nips) - Nostr Implementation Possibilities

---

**Note**: For detailed NIP compliance information, see [NIP_COMPLIANCE_REPORT.md](NIP_COMPLIANCE_REPORT.md).
