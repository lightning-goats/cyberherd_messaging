# CyberHerd Messaging Extension

This extension provides shared messaging utilities for LNbits extensions, including:

- Publishing notes to Nostr using the nostrclient extension
- Broadcasting JSON messages to websocket clients via LNbits core
- API endpoints for publishing and broadcasting

## Settings

- A global toggle is provided to enable/disable Nostr publishing. When disabled, messages are only sent to connected websocket clients.

## Usage

### Internal (Python)

```python
from lnbits.extensions.cyberherd_messaging import services as chm

# Publish a note to Nostr
await chm.try_publish_note(
    "Hello from CyberHerd!",
    e_tags=["<note_id>"],
    p_tags=["<pubkey>"],
    private_key="nsec1..."  # or hex
)

# Broadcast to websockets
await chm.send_to_websocket_clients("topic", {"type": "update", "data": "..."})
```

### API

- `POST /cyberherd_messaging/api/v1/publish` - Publish a note (admin key required)
- `POST /cyberherd_messaging/api/v1/ws_broadcast` - Broadcast to websockets (admin key required)

## Dependencies

- Requires the `nostrclient` extension for Nostr publishing
- Uses LNbits core websocket updater for broadcasting
