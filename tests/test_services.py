# tests/test_services.py - unit tests for cyberherd_messaging.services
import pytest
from unittest.mock import MagicMock, AsyncMock

import cyberherd_messaging.services as services

MOCK_WALLET_ID = "test_wallet_id_1234"


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
    """Test publish_note calls bunker signing with correctly merged tags."""
    mock_enabled = AsyncMock(return_value=True)
    monkeypatch.setattr("cyberherd_messaging.services.is_nostr_publishing_enabled", mock_enabled)

    captured_args: dict = {}

    async def mock_bunker_sign(wallet_id, content, kind, tags):
        captured_args["wallet_id"] = wallet_id
        captured_args["content"] = content
        captured_args["kind"] = kind
        captured_args["tags"] = [tuple(tag) for tag in tags]
        return True

    monkeypatch.setattr("cyberherd_messaging.services._try_bunker_sign_and_publish", mock_bunker_sign)

    result = await services.publish_note(
        "hello world",
        tags=[("t", "test")],
        e_tags=["event123"],
        p_tags=["pubkey456"],
        wallet_id=MOCK_WALLET_ID,
    )

    assert result is True
    assert mock_enabled.called, "is_nostr_publishing_enabled should be called"
    assert captured_args["wallet_id"] == MOCK_WALLET_ID
    # Ensure tags merged correctly with proper markers
    tags = captured_args["tags"]
    assert ("t", "test") in tags
    assert ("p", "pubkey456") in tags
    e_entries = [tag for tag in tags if tag[0] == "e"]
    assert e_entries == [
        ("e", "event123", "", "root"),
        ("e", "event123", "", "reply"),
    ]


@pytest.mark.asyncio
async def test_publish_note_bunker_failure(monkeypatch):
    """Test publish_note returns False when bunker signing fails."""
    mock_enabled = AsyncMock(return_value=True)
    monkeypatch.setattr("cyberherd_messaging.services.is_nostr_publishing_enabled", mock_enabled)

    async def mock_bunker_fail(wallet_id, content, kind, tags):
        return False

    monkeypatch.setattr("cyberherd_messaging.services._try_bunker_sign_and_publish", mock_bunker_fail)

    result = await services.publish_note(
        "test message",
        wallet_id=MOCK_WALLET_ID,
    )
    assert result is False


@pytest.mark.asyncio
async def test_try_publish_note(monkeypatch):
    """Test try_publish_note delegates to publish_note correctly."""
    mock_enabled = AsyncMock(return_value=True)
    monkeypatch.setattr("cyberherd_messaging.services.is_nostr_publishing_enabled", mock_enabled)

    captured_args: dict = {}

    async def mock_bunker_sign(wallet_id, content, kind, tags):
        captured_args["wallet_id"] = wallet_id
        captured_args["content"] = content
        return True

    monkeypatch.setattr("cyberherd_messaging.services._try_bunker_sign_and_publish", mock_bunker_sign)

    result = await services.try_publish_note(
        "test message",
        e_tags=["event1"],
        p_tags=["pubkey1"],
        wallet_id=MOCK_WALLET_ID,
    )

    assert result is True
    assert captured_args["wallet_id"] == MOCK_WALLET_ID


@pytest.mark.asyncio
async def test_publish_note_30311_reply(monkeypatch):
    """Test 30311 reply generates correct a-tags and kind 1311."""
    mock_enabled = AsyncMock(return_value=True)
    monkeypatch.setattr("cyberherd_messaging.services.is_nostr_publishing_enabled", mock_enabled)

    captured_args: dict = {}

    async def mock_bunker_sign(wallet_id, content, kind, tags):
        captured_args["kind"] = kind
        captured_args["tags"] = [tuple(tag) for tag in tags]
        return True

    monkeypatch.setattr("cyberherd_messaging.services._try_bunker_sign_and_publish", mock_bunker_sign)

    result = await services.publish_note(
        "reply",
        e_tags=["event123"],
        wallet_id=MOCK_WALLET_ID,
        reply_to_30311_event="event123",
        reply_to_30311_a_tag="30311:deadbeef:identifier",
        reply_relay="wss://relay.example.com",
    )

    assert result is True
    assert captured_args["kind"] == 1311
    tags = captured_args["tags"]
    a_entries = [tag for tag in tags if tag[0] == "a"]
    assert a_entries == [("a", "30311:deadbeef:identifier")]
    e_entries = [tag for tag in tags if tag[0] == "e"]
    assert e_entries == [
        ("e", "event123", "wss://relay.example.com", "root"),
        ("e", "event123", "wss://relay.example.com", "reply"),
    ]


@pytest.mark.asyncio
async def test_render_and_publish_template(monkeypatch):
    """Test render_and_publish_template renders and calls bunker signing."""
    mock_enabled = AsyncMock(return_value=True)
    monkeypatch.setattr("cyberherd_messaging.services.is_nostr_publishing_enabled", mock_enabled)

    captured_args: dict = {}

    async def mock_bunker_sign(wallet_id, content, kind, tags):
        captured_args["wallet_id"] = wallet_id
        captured_args["content"] = content
        captured_args["tags"] = [tuple(tag) for tag in tags]
        return True

    monkeypatch.setattr("cyberherd_messaging.services._try_bunker_sign_and_publish", mock_bunker_sign)

    # Mock the template retrieval
    mock_template = type('MockTemplate', (), {'content': 'Hello {name}', 'reply_relay': 'wss://seed.relay'})()
    mock_get_template = AsyncMock(return_value=mock_template)
    monkeypatch.setattr("cyberherd_messaging.crud.get_message_template", mock_get_template)

    result = await services.render_and_publish_template(
        user_id="test_user",
        category="test_category",
        key="0",
        values={"name": "Goat"},
        e_tags=["event123"],
        wallet_id=MOCK_WALLET_ID,
    )

    assert result is True
    assert captured_args["wallet_id"] == MOCK_WALLET_ID
    assert ("e", "event123", "wss://seed.relay", "root") in captured_args["tags"]
    assert ("e", "event123", "wss://seed.relay", "reply") in captured_args["tags"]


@pytest.mark.asyncio
async def test_send_to_websocket_clients(monkeypatch):
    """Test the send_to_websocket_clients helper function."""
    mock_updater = AsyncMock()
    monkeypatch.setattr("lnbits.core.services.websockets.websocket_updater", mock_updater)

    test_message = {"type": "test", "data": "hello"}
    result = await services.send_to_websocket_clients("cyberherd", test_message)

    assert result is True
    assert mock_updater.called
    call_args = mock_updater.call_args
    assert call_args[0][0] == "cyberherd"
    assert '"type": "test"' in call_args[0][1]
    assert '"data": "hello"' in call_args[0][1]


@pytest.mark.asyncio
async def test_send_to_websocket_clients_error_handling(monkeypatch):
    """Test error handling in send_to_websocket_clients."""
    mock_updater = AsyncMock(side_effect=Exception("Connection failed"))
    monkeypatch.setattr("lnbits.core.services.websockets.websocket_updater", mock_updater)

    test_message = {"type": "test"}
    result = await services.send_to_websocket_clients("cyberherd", test_message)

    assert result is False


@pytest.mark.asyncio
async def test_publish_note_when_disabled_by_setting(monkeypatch):
    """Test that publish_note short-circuits when nostr_publishing_enabled is False."""
    mock_enabled = AsyncMock(return_value=False)
    monkeypatch.setattr("cyberherd_messaging.services.is_nostr_publishing_enabled", mock_enabled)

    # Mock bunker signing - should NOT be called
    mock_bunker = AsyncMock()
    monkeypatch.setattr("cyberherd_messaging.services._try_bunker_sign_and_publish", mock_bunker)

    result = await services.publish_note(
        "test message",
        wallet_id=MOCK_WALLET_ID,
    )

    # Should return True (for websocket compatibility) but not publish
    assert result is True
    assert mock_enabled.called, "is_nostr_publishing_enabled should be checked"
    assert not mock_bunker.called, "bunker signing should NOT be called when disabled"


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
async def test_render_and_publish_template_when_disabled(monkeypatch):
    """Test render_and_publish_template short-circuits when nostr publishing is disabled."""
    mock_enabled = AsyncMock(return_value=False)
    monkeypatch.setattr("cyberherd_messaging.services.is_nostr_publishing_enabled", mock_enabled)

    mock_template = type('MockTemplate', (), {'content': 'Hello {name}'})()
    mock_get_template = AsyncMock(return_value=mock_template)
    monkeypatch.setattr("cyberherd_messaging.crud.get_message_template", mock_get_template)

    # Mock bunker signing - should NOT be called
    mock_bunker = AsyncMock()
    monkeypatch.setattr("cyberherd_messaging.services._try_bunker_sign_and_publish", mock_bunker)

    result = await services.render_and_publish_template(
        user_id="test_user",
        category="test_category",
        key="0",
        values={"name": "Goat"},
        wallet_id=MOCK_WALLET_ID,
    )

    # Should return True (for websocket compatibility) but not publish to nostr
    assert result is True
    assert mock_enabled.called
    assert not mock_bunker.called, "bunker signing should NOT be called when disabled"


@pytest.mark.asyncio
async def test_is_nostr_publishing_enabled_with_setting_disabled(monkeypatch):
    """Test is_nostr_publishing_enabled returns False when setting is '0'."""
    mock_get_setting = AsyncMock(return_value="0")
    monkeypatch.setattr("cyberherd_messaging.crud.get_setting", mock_get_setting)

    mock_nostrclient = AsyncMock(return_value=True)
    monkeypatch.setattr("cyberherd_messaging.services._is_nostrclient_available", mock_nostrclient)

    result = await services.is_nostr_publishing_enabled()

    assert result is False
    assert mock_get_setting.called
    assert not mock_nostrclient.called, "_is_nostrclient_available should NOT be called when setting is disabled"


@pytest.mark.asyncio
async def test_is_nostr_publishing_enabled_with_various_disabled_values(monkeypatch):
    """Test is_nostr_publishing_enabled handles various disabled values."""
    mock_nostrclient = AsyncMock(return_value=True)
    monkeypatch.setattr("cyberherd_messaging.services._is_nostrclient_available", mock_nostrclient)

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
    mock_get_setting = AsyncMock(return_value="1")
    monkeypatch.setattr("cyberherd_messaging.crud.get_setting", mock_get_setting)

    mock_nostrclient = AsyncMock(return_value=True)
    monkeypatch.setattr("cyberherd_messaging.services._is_nostrclient_available", mock_nostrclient)

    result = await services.is_nostr_publishing_enabled()

    assert result is True
    assert mock_get_setting.called
    assert mock_nostrclient.called, "_is_nostrclient_available should be called when setting is enabled"


@pytest.mark.asyncio
async def test_is_nostr_publishing_enabled_with_missing_setting(monkeypatch):
    """Test is_nostr_publishing_enabled defaults to enabled when setting is missing."""
    mock_get_setting = AsyncMock(return_value=None)
    monkeypatch.setattr("cyberherd_messaging.crud.get_setting", mock_get_setting)

    mock_nostrclient = AsyncMock(return_value=True)
    monkeypatch.setattr("cyberherd_messaging.services._is_nostrclient_available", mock_nostrclient)

    result = await services.is_nostr_publishing_enabled()

    assert result is True
    assert mock_get_setting.called
    assert mock_nostrclient.called, "_is_nostrclient_available should be called when setting is missing (default enabled)"


@pytest.mark.asyncio
async def test_is_nostr_publishing_enabled_with_db_error(monkeypatch):
    """Test is_nostr_publishing_enabled falls back to enabled on database error."""
    mock_get_setting = AsyncMock(side_effect=Exception("Database error"))
    monkeypatch.setattr("cyberherd_messaging.crud.get_setting", mock_get_setting)

    mock_nostrclient = AsyncMock(return_value=True)
    monkeypatch.setattr("cyberherd_messaging.services._is_nostrclient_available", mock_nostrclient)

    result = await services.is_nostr_publishing_enabled()

    assert result is True
    assert mock_get_setting.called
    assert mock_nostrclient.called, "_is_nostrclient_available should be called on database error (fallback to enabled)"


@pytest.mark.asyncio
async def test_is_nostr_publishing_enabled_when_nostrclient_unavailable(monkeypatch):
    """Test is_nostr_publishing_enabled returns False when nostrclient is unavailable."""
    mock_get_setting = AsyncMock(return_value="1")
    monkeypatch.setattr("cyberherd_messaging.crud.get_setting", mock_get_setting)

    mock_nostrclient = AsyncMock(return_value=False)
    monkeypatch.setattr("cyberherd_messaging.services._is_nostrclient_available", mock_nostrclient)

    result = await services.is_nostr_publishing_enabled()

    assert result is False
    assert mock_get_setting.called
    assert mock_nostrclient.called
