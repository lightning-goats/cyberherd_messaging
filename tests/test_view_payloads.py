"""Tests for API payload models ensuring private keys are ignored."""

from lnbits.extensions.cyberherd_messaging.views_api import (
    PublishPayload,
    PublishTemplatePayload,
    PublishTemplateWithValuesPayload,
)


def test_publish_payload_ignores_private_key_field():
    payload = PublishPayload(content="hello", private_key="nsec...", reply_relay="wss://relay")  # type: ignore[arg-type]
    assert not hasattr(payload, "private_key")
    assert "private_key" not in payload.dict()
    assert payload.reply_relay == "wss://relay"


def test_publish_template_payload_ignores_private_key_field():
    payload = PublishTemplatePayload(
        category="demo",
        key="a",
        e_tags=[],
        p_tags=[],
        private_key="nsec...",  # type: ignore[arg-type]
        reply_relay="wss://relay",
    )
    assert not hasattr(payload, "private_key")
    assert "private_key" not in payload.dict()
    assert payload.reply_relay == "wss://relay"


def test_publish_template_with_values_payload_ignores_private_key_field():
    payload = PublishTemplateWithValuesPayload(
        category="demo",
        key="b",
        values={"foo": "bar"},
        private_key="nsec...",  # type: ignore[arg-type]
        reply_relay="wss://relay",
    )
    assert not hasattr(payload, "private_key")
    assert "private_key" not in payload.dict()
    assert payload.reply_relay == "wss://relay"
