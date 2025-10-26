# tests/test_services.py - unit tests for cyberherd_messaging.services
import pytest
import secp256k1
from unittest.mock import MagicMock, AsyncMock

import cyberherd_messaging.services as services

class DummyNostrClient:
    def __init__(self):
        self.published = []
        self.relay_manager = MagicMock()
        self.relay_manager.relays = []
        self.relay_manager.publish_message = MagicMock()

    async def publish(self, event):
        self.published.append(event)
        return True

@pytest.mark.asyncio
async def test_publish_note_with_tags(monkeypatch):
    # Mock is_nostr_publishing_enabled to return True
    mock_enabled = AsyncMock(return_value=True)
    monkeypatch.setattr("cyberherd_messaging.services.is_nostr_publishing_enabled", mock_enabled)
    
    dummy_client = DummyNostrClient()
    monkeypatch.setattr("lnbits.extensions.nostrclient.router.nostr_client", dummy_client)
    
    # Mock create_and_sign_event to return a mock event
    mock_event = MagicMock()
    mock_event.content = "hello world"
    mock_event.tags = []
    mock_event.id = "mockid"
    mock_event.kind = 1
    mock_event.to_message = MagicMock(return_value="mock_message")
    captured_tags: list[tuple[str, ...]] = []
    
    def mock_create_sign(content, private_key_hex, tags):
        nonlocal captured_tags
        captured_tags = [tuple(tag) for tag in tags]
        mock_event.tags = [[str(part) for part in tag] for tag in tags]
        return mock_event
    
    monkeypatch.setattr("cyberherd_messaging.services.create_and_sign_event", mock_create_sign)

    sk = secp256k1.PrivateKey()
    pk_hex = sk.serialize()

    result = await services.publish_note(
        "hello world",
        tags=[("t", "test")],
        e_tags=["event123"],
        p_tags=["pubkey456"],
        private_key_hex=pk_hex,
    )

    assert result is True
    assert mock_enabled.called, "is_nostr_publishing_enabled should be called"
    # Ensure tags merged correctly with proper markers
    assert ("t", "test") in captured_tags
    assert ("p", "pubkey456") in captured_tags
    e_entries = [tag for tag in captured_tags if tag[0] == "e"]
    assert e_entries == [
        ("e", "event123", "", "root"),
        ("e", "event123", "", "reply"),
    ]

@pytest.mark.asyncio
async def test_publish_note_without_private_key(monkeypatch):
    # Mock is_nostr_publishing_enabled to return True
    mock_enabled = AsyncMock(return_value=True)
    monkeypatch.setattr("cyberherd_messaging.services.is_nostr_publishing_enabled", mock_enabled)
    
    result = await services.publish_note("test message")
    assert result is False

@pytest.mark.asyncio
async def test_try_publish_note(monkeypatch):
    # Mock is_nostr_publishing_enabled to return True
    mock_enabled = AsyncMock(return_value=True)
    monkeypatch.setattr("cyberherd_messaging.services.is_nostr_publishing_enabled", mock_enabled)
    
    dummy_client = DummyNostrClient()
    monkeypatch.setattr("lnbits.extensions.nostrclient.router.nostr_client", dummy_client)
    
    # Mock create_and_sign_event
    mock_event = MagicMock()
    mock_event.content = "test message"
    mock_event.id = "mockid"
    mock_event.kind = 1
    mock_event.to_message = MagicMock(return_value="mock_message")
    
    monkeypatch.setattr("cyberherd_messaging.services.create_and_sign_event", lambda c, p, t: mock_event)

    sk = secp256k1.PrivateKey()
    pk_hex = sk.serialize()

    result = await services.try_publish_note(
        "test message",
        e_tags=["event1"],
        p_tags=["pubkey1"],
        private_key=pk_hex
    )

    assert result is True
    assert mock_event.to_message.called


@pytest.mark.asyncio
async def test_publish_note_30311_reply(monkeypatch):
    mock_enabled = AsyncMock(return_value=True)
    monkeypatch.setattr("cyberherd_messaging.services.is_nostr_publishing_enabled", mock_enabled)

    dummy_client = DummyNostrClient()
    monkeypatch.setattr("lnbits.extensions.nostrclient.router.nostr_client", dummy_client)

    mock_event = MagicMock()
    mock_event.content = "reply"
    mock_event.id = "mockid"
    mock_event.kind = 1311
    mock_event.to_message = MagicMock(return_value="mock_message")

    captured_tags: list[tuple[str, ...]] = []

    def mock_create_and_sign(content, private_key_hex, tags):
        nonlocal captured_tags
        captured_tags = [tuple(tag) for tag in tags]
        return mock_event

    monkeypatch.setattr(
        "cyberherd_messaging.services.create_and_sign_event", mock_create_and_sign
    )

    sk = secp256k1.PrivateKey()
    pk_hex = sk.serialize()

    result = await services.publish_note(
        "reply",
        e_tags=["event123"],
        private_key_hex=pk_hex,
        reply_to_30311_event="event123",
        reply_to_30311_a_tag="30311:deadbeef:identifier",
        reply_relay="wss://relay.example.com",
    )

    assert result is True
    assert dummy_client.relay_manager.publish_message.called
    a_entries = [tag for tag in captured_tags if tag[0] == "a"]
    assert a_entries == [("a", "30311:deadbeef:identifier")]
    e_entries = [tag for tag in captured_tags if tag[0] == "e"]
    assert e_entries == [
        ("e", "event123", "wss://relay.example.com", "root"),
        ("e", "event123", "wss://relay.example.com", "reply"),
    ]


@pytest.mark.asyncio
async def test_render_and_publish_template(monkeypatch):
    # Mock is_nostr_publishing_enabled to return True
    mock_enabled = AsyncMock(return_value=True)
    monkeypatch.setattr("cyberherd_messaging.services.is_nostr_publishing_enabled", mock_enabled)
    
    dummy_client = DummyNostrClient()
    monkeypatch.setattr("lnbits.extensions.nostrclient.router.nostr_client", dummy_client)
    
    # Mock create_and_sign_event
    mock_event = MagicMock()
    mock_event.content = "Hello Goat"
    mock_event.id = "mockid"
    mock_event.kind = 1
    mock_event.to_message = MagicMock(return_value="mock_message")
    captured_tags: list[tuple[str, ...]] = []

    def fake_create_and_sign(content, private_key_hex, tags):
        nonlocal captured_tags
        captured_tags = [tuple(tag) for tag in tags]
        return mock_event

    monkeypatch.setattr("cyberherd_messaging.services.create_and_sign_event", fake_create_and_sign)

    # Mock the template retrieval
    mock_template = type('MockTemplate', (), {'content': 'Hello {name}', 'reply_relay': 'wss://seed.relay'})()
    mock_get_template = AsyncMock(return_value=mock_template)
    monkeypatch.setattr("cyberherd_messaging.crud.get_message_template", mock_get_template)

    sk = secp256k1.PrivateKey()
    pk_hex = sk.serialize()

    result = await services.render_and_publish_template(
        user_id="test_user",
        category="test_category", 
        key="0",
        values={"name": "Goat"},
        private_key=pk_hex,
        e_tags=["event123"],
    )

    assert result is True
    assert mock_event.to_message.called
    assert ("e", "event123", "wss://seed.relay", "root") in captured_tags
    assert ("e", "event123", "wss://seed.relay", "reply") in captured_tags


@pytest.mark.asyncio
async def test_send_to_websocket_clients(monkeypatch):
    """Test the send_to_websocket_clients helper function."""
    from unittest.mock import AsyncMock
    
    # Mock the websocket_updater from core
    mock_updater = AsyncMock()
    monkeypatch.setattr("lnbits.core.services.websockets.websocket_updater", mock_updater)
    
    # Test sending a message
    test_message = {"type": "test", "data": "hello"}
    result = await services.send_to_websocket_clients("cyberherd", test_message)
    
    assert result is True
    assert mock_updater.called
    # Verify the topic and that message was JSON-serialized
    call_args = mock_updater.call_args
    assert call_args[0][0] == "cyberherd"
    assert '"type": "test"' in call_args[0][1]
    assert '"data": "hello"' in call_args[0][1]


@pytest.mark.asyncio
async def test_send_to_websocket_clients_error_handling(monkeypatch):
    """Test error handling in send_to_websocket_clients."""
    from unittest.mock import AsyncMock
    
    # Mock websocket_updater to raise an exception
    mock_updater = AsyncMock(side_effect=Exception("Connection failed"))
    monkeypatch.setattr("lnbits.core.services.websockets.websocket_updater", mock_updater)
    
    test_message = {"type": "test"}
    result = await services.send_to_websocket_clients("cyberherd", test_message)
    
    # Should return False on error but not raise
    assert result is False


@pytest.mark.asyncio
async def test_publish_note_when_disabled_by_setting(monkeypatch):
    """Test that publish_note short-circuits when nostr_publishing_enabled is False."""
    # Mock is_nostr_publishing_enabled to return False (toggle off)
    mock_enabled = AsyncMock(return_value=False)
    monkeypatch.setattr("cyberherd_messaging.services.is_nostr_publishing_enabled", mock_enabled)
    
    # Mock create_and_sign_event - should NOT be called
    mock_create = MagicMock()
    monkeypatch.setattr("cyberherd_messaging.services.create_and_sign_event", mock_create)
    
    # Mock nostrclient - should NOT be accessed
    dummy_client = DummyNostrClient()
    monkeypatch.setattr("lnbits.extensions.nostrclient.router.nostr_client", dummy_client)
    
    sk = secp256k1.PrivateKey()
    pk_hex = sk.serialize()
    
    result = await services.publish_note(
        "test message",
        private_key_hex=pk_hex,
    )
    
    # Should return True (for websocket compatibility) but not publish
    assert result is True
    assert mock_enabled.called, "is_nostr_publishing_enabled should be checked"
    assert not mock_create.called, "create_and_sign_event should NOT be called when disabled"


@pytest.mark.asyncio
async def test_build_message_bundle_headbutt_success():
    bundle = await services.build_message_bundle(
        "headbutt_success",
        cyber_herd_item={
            "attacker_name": "Alice",
            "attacker_amount": 5500,
            "victim_name": "Bob",
            "victim_amount": 3200,
            "attacker_pubkey": "a" * 64,
            "victim_pubkey": "b" * 64,
        },
    )
    assert "⚡headbutt⚡" in bundle.nostr_content
    assert not bundle.nostr_content.strip().startswith("{")
    assert "Alice" in bundle.websocket_content


@pytest.mark.asyncio
async def test_build_message_bundle_sats_received_goats():
    bundle = await services.build_message_bundle(
        "sats_received",
        new_amount=2500,
        difference=1500,
    )
    assert "sats" in bundle.nostr_content
    if bundle.goat_data:
        assert all("name" in goat and "imageUrl" in goat for goat in bundle.goat_data)


@pytest.mark.asyncio
async def test_build_message_bundle_new_member_spots_info():
    bundle = await services.build_message_bundle(
        "new_member",
        new_amount=5000,
        difference=0,
        cyber_herd_item={"display_name": "Tester", "amount": 5000},
        spots_remaining=3,
    )
    assert "⚡ 3 more spots available. ⚡" in bundle.nostr_content
    assert bundle.spots_info == "⚡ 3 more spots available. ⚡"


@pytest.mark.asyncio
async def test_build_message_bundle_headbutt_success():
    bundle = await services.build_message_bundle(
        "headbutt_success",
        cyber_herd_item={
            "attacker_name": "Alice",
            "attacker_amount": 5500,
            "victim_name": "Bob",
            "victim_amount": 3200,
            "attacker_pubkey": "a" * 64,
            "victim_pubkey": "b" * 64,
        },
    )
    assert "⚡headbutt⚡" in bundle.nostr_content
    assert not bundle.nostr_content.strip().startswith("{")
    assert "Alice" in bundle.websocket_content


@pytest.mark.asyncio
async def test_build_message_bundle_sats_received_goats():
    bundle = await services.build_message_bundle(
        "sats_received",
        new_amount=2500,
        difference=1500,
    )
    assert "sats" in bundle.nostr_content
    if bundle.goat_data:
        assert all("name" in goat and "imageUrl" in goat for goat in bundle.goat_data)


@pytest.mark.asyncio
async def test_is_nostr_publishing_enabled_with_setting_disabled(monkeypatch):
    """Test is_nostr_publishing_enabled returns False when setting is '0'."""
    # Mock crud.get_setting to return "0" (disabled)
    mock_get_setting = AsyncMock(return_value="0")
    monkeypatch.setattr("cyberherd_messaging.crud.get_setting", mock_get_setting)
    
    # Mock _is_nostrclient_available - should NOT be called when setting is off
    mock_nostrclient = AsyncMock(return_value=True)
    monkeypatch.setattr("cyberherd_messaging.services._is_nostrclient_available", mock_nostrclient)
    
    result = await services.is_nostr_publishing_enabled()
    
    assert result is False
    assert mock_get_setting.called
    assert not mock_nostrclient.called, "_is_nostrclient_available should NOT be called when setting is disabled"


@pytest.mark.asyncio
async def test_is_nostr_publishing_enabled_with_various_disabled_values(monkeypatch):
    """Test is_nostr_publishing_enabled handles various disabled values."""
    # Mock _is_nostrclient_available - should NOT be called
    mock_nostrclient = AsyncMock(return_value=True)
    monkeypatch.setattr("cyberherd_messaging.services._is_nostrclient_available", mock_nostrclient)
    
    # Test various disabled values
    disabled_values = ["0", "false", "False", "FALSE", "no", "NO", "off", "OFF", "  false  ", ""]
    
    for value in disabled_values:
        mock_nostrclient.reset_mock()
        mock_get_setting = AsyncMock(return_value=value)
        monkeypatch.setattr("cyberherd_messaging.crud.get_setting", mock_get_setting)
        
        result = await services.is_nostr_publishing_enabled()
        
        assert result is False, f"Expected False for value '{value}'"
        assert not mock_nostrclient.called, f"_is_nostrclient_available should NOT be called for '{value}'"


@pytest.mark.asyncio
async def test_is_nostr_publishing_enabled_with_setting_enabled(monkeypatch):
    """Test is_nostr_publishing_enabled checks nostrclient when setting is '1'."""
    # Mock crud.get_setting to return "1" (enabled)
    mock_get_setting = AsyncMock(return_value="1")
    monkeypatch.setattr("cyberherd_messaging.crud.get_setting", mock_get_setting)
    
    # Mock _is_nostrclient_available to return True
    mock_nostrclient = AsyncMock(return_value=True)
    monkeypatch.setattr("cyberherd_messaging.services._is_nostrclient_available", mock_nostrclient)
    
    result = await services.is_nostr_publishing_enabled()
    
    assert result is True
    assert mock_get_setting.called
    assert mock_nostrclient.called, "_is_nostrclient_available should be called when setting is enabled"


@pytest.mark.asyncio
async def test_is_nostr_publishing_enabled_with_missing_setting(monkeypatch):
    """Test is_nostr_publishing_enabled defaults to enabled when setting is missing."""
    # Mock crud.get_setting to return None (missing)
    mock_get_setting = AsyncMock(return_value=None)
    monkeypatch.setattr("cyberherd_messaging.crud.get_setting", mock_get_setting)
    
    # Mock _is_nostrclient_available to return True
    mock_nostrclient = AsyncMock(return_value=True)
    monkeypatch.setattr("cyberherd_messaging.services._is_nostrclient_available", mock_nostrclient)
    
    result = await services.is_nostr_publishing_enabled()
    
    assert result is True
    assert mock_get_setting.called
    assert mock_nostrclient.called, "_is_nostrclient_available should be called when setting is missing (default enabled)"


@pytest.mark.asyncio
async def test_is_nostr_publishing_enabled_with_db_error(monkeypatch):
    """Test is_nostr_publishing_enabled falls back to enabled on database error."""
    # Mock crud.get_setting to raise an exception
    mock_get_setting = AsyncMock(side_effect=Exception("Database error"))
    monkeypatch.setattr("cyberherd_messaging.crud.get_setting", mock_get_setting)
    
    # Mock _is_nostrclient_available to return True
    mock_nostrclient = AsyncMock(return_value=True)
    monkeypatch.setattr("cyberherd_messaging.services._is_nostrclient_available", mock_nostrclient)
    
    result = await services.is_nostr_publishing_enabled()
    
    # Should fall back to enabled and check nostrclient
    assert result is True
    assert mock_get_setting.called
    assert mock_nostrclient.called, "_is_nostrclient_available should be called on database error (fallback to enabled)"


@pytest.mark.asyncio
async def test_is_nostr_publishing_enabled_when_nostrclient_unavailable(monkeypatch):
    """Test is_nostr_publishing_enabled returns False when nostrclient is unavailable."""
    # Mock crud.get_setting to return "1" (enabled)
    mock_get_setting = AsyncMock(return_value="1")
    monkeypatch.setattr("cyberherd_messaging.crud.get_setting", mock_get_setting)
    
    # Mock _is_nostrclient_available to return False
    mock_nostrclient = AsyncMock(return_value=False)
    monkeypatch.setattr("cyberherd_messaging.services._is_nostrclient_available", mock_nostrclient)
    
    result = await services.is_nostr_publishing_enabled()
    
    # Setting is enabled but nostrclient unavailable = False
    assert result is False
    assert mock_get_setting.called
    assert mock_nostrclient.called


@pytest.mark.asyncio
async def test_render_and_publish_template_when_disabled(monkeypatch):
    """Test render_and_publish_template short-circuits when nostr publishing is disabled."""
    # Mock is_nostr_publishing_enabled to return False
    mock_enabled = AsyncMock(return_value=False)
    monkeypatch.setattr("cyberherd_messaging.services.is_nostr_publishing_enabled", mock_enabled)
    
    # Mock the template retrieval
    mock_template = type('MockTemplate', (), {'content': 'Hello {name}'})()
    mock_get_template = AsyncMock(return_value=mock_template)
    monkeypatch.setattr("cyberherd_messaging.crud.get_message_template", mock_get_template)
    
    # Mock create_and_sign_event - should NOT be called
    mock_create = MagicMock()
    monkeypatch.setattr("cyberherd_messaging.services.create_and_sign_event", mock_create)
    
    sk = secp256k1.PrivateKey()
    pk_hex = sk.serialize()
    
    result = await services.render_and_publish_template(
        user_id="test_user",
        category="test_category",
        key="0",
        values={"name": "Goat"},
        private_key=pk_hex
    )
    
    # Should return True (for websocket compatibility) but not publish to nostr
    assert result is True
    assert mock_enabled.called
    assert not mock_create.called, "create_and_sign_event should NOT be called when disabled"


@pytest.mark.asyncio
async def test_build_message_bundle_headbutt_success():
    bundle = await services.build_message_bundle(
        "headbutt_success",
        cyber_herd_item={
            "attacker_name": "Alice",
            "attacker_amount": 5500,
            "victim_name": "Bob",
            "victim_amount": 3200,
            "attacker_pubkey": "a" * 64,
            "victim_pubkey": "b" * 64,
        },
    )
    assert "⚡headbutt⚡" in bundle.nostr_content
    assert not bundle.nostr_content.strip().startswith("{")
    assert "Alice" in bundle.websocket_content


@pytest.mark.asyncio
async def test_build_message_bundle_sats_received_goats():
    bundle = await services.build_message_bundle(
        "sats_received",
        new_amount=2500,
        difference=1500,
    )
    assert "sats" in bundle.nostr_content
    if bundle.goat_data:
        assert all("name" in goat and "imageUrl" in goat for goat in bundle.goat_data)
