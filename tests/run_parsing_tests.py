#!/usr/bin/env python3
"""
Lightweight test runner for cyberherd_messaging parsing and normalization.
This avoids pytest collection importing the host package and its heavy deps.
"""
import asyncio
import importlib.util
import sys
from types import SimpleNamespace
from pathlib import Path
import traceback

pkg_dir = Path(__file__).resolve().parents[1]
svc_path = str(pkg_dir / "services.py")

spec = importlib.util.spec_from_file_location("lnbits.extensions.cyberherd_messaging.services", svc_path)
chm = importlib.util.module_from_spec(spec)
# Prepare package context so services.py can perform relative imports
pkg_parent = str(pkg_dir.parent.parent)
if pkg_parent not in sys.path:
    sys.path.insert(0, pkg_parent)

# Ensure the package modules exist so relative imports work
import types
pkg_name = "lnbits.extensions.cyberherd_messaging"
pkg_mod = types.ModuleType(pkg_name)
pkg_mod.__path__ = [str(pkg_dir)]
sys.modules["lnbits.extensions.cyberherd_messaging"] = pkg_mod

# Ensure parent package modules exist so relative imports resolve
lnbits_mod = types.ModuleType("lnbits")
lnbits_mod.__path__ = [str(repo_root := Path(__file__).resolve().parents[3] / "lnbits")]
extensions_mod = types.ModuleType("lnbits.extensions")
extensions_mod.__path__ = [str(repo_root / "extensions")]
sys.modules["lnbits"] = lnbits_mod
sys.modules["lnbits.extensions"] = extensions_mod

# Provide a small stub for the relative import .utils used by services.py
utils_name = "lnbits.extensions.cyberherd_messaging.utils"
utils_mod = types.ModuleType(utils_name)
def get_random_goat_names():
    return ["goat1", "goat2"]
utils_mod.get_random_goat_names = get_random_goat_names
sys.modules[utils_name] = utils_mod

spec.loader.exec_module(chm)

PASS = 0
FAIL = 0


def ok(msg):
    print(f"[PASS] {msg}")


def fail(msg, exc=None):
    global FAIL
    FAIL += 1
    print(f"[FAIL] {msg}")
    if exc:
        print(traceback.format_exc())


# Test normalize_relay_hint
try:
    assert chm.normalize_relay_hint("wss://relay.example") == "wss://relay.example"
    assert chm.normalize_relay_hint("ws://relay.example") == "ws://relay.example"
    assert chm.normalize_relay_hint("https://relay.example/nostr") == "wss://relay.example/nostr"
    assert chm.normalize_relay_hint("http://relay.example/nostr") == "ws://relay.example/nostr"
    assert chm.normalize_relay_hint("ftp://bad") is None
    assert chm.normalize_relay_hint("") is None
    assert chm.normalize_relay_hint(None) is None
    ok("normalize_relay_hint cases")
except AssertionError as e:
    fail("normalize_relay_hint cases", e)


async def run_async_tests():
    global PASS

    # Helper to stub crud.get_message_template
    async def fake_get_message_template_json(user_id, category, key):
        return SimpleNamespace(content='{"content":"Hello {name}", "reply_relay":"https://r.example"}', reply_relay=None)

    async def fake_get_message_template_py(user_id, category, key):
        return SimpleNamespace(content="{'content': 'Hi {name}', 'reply_relay': 'http://r.example'}", reply_relay=None)

    async def fake_get_message_template_messy(user_id, category, key):
        return SimpleNamespace(content="{content:'Yo {name}', reply_relay:'https://r.example'}", reply_relay=None)

    async def fake_get_message_template_discard(user_id, category, key):
        return SimpleNamespace(content="{'foo':'bar','baz':1}", reply_relay=None)

    # JSON template
    try:
        # Register a stub module for the in-package relative import `.crud`
        crud_mod = types.ModuleType("lnbits.extensions.cyberherd_messaging.crud")
        crud_mod.get_message_template = fake_get_message_template_json
        sys.modules["lnbits.extensions.cyberherd_messaging.crud"] = crud_mod
        rendered, goats = await chm.render_and_publish_template(
            user_id="u",
            category="c",
            key="k",
            values={"name": "Alice"},
            return_websocket_message=True,
        )
        assert rendered == "Hello Alice"
        ok("render JSON template")
    except Exception as e:
        fail("render JSON template", e)

    # Python literal template
    try:
        crud_mod = types.ModuleType("lnbits.extensions.cyberherd_messaging.crud")
        crud_mod.get_message_template = fake_get_message_template_py
        sys.modules["lnbits.extensions.cyberherd_messaging.crud"] = crud_mod
        rendered, goats = await chm.render_and_publish_template(
            user_id="u",
            category="c",
            key="k",
            values={"name": "Bob"},
            return_websocket_message=True,
        )
        assert rendered == "Hi Bob"
        ok("render python-literal template")
    except Exception as e:
        fail("render python-literal template", e)

    # Messy serialized template
    try:
        crud_mod = types.ModuleType("lnbits.extensions.cyberherd_messaging.crud")
        crud_mod.get_message_template = fake_get_message_template_messy
        sys.modules["lnbits.extensions.cyberherd_messaging.crud"] = crud_mod
        rendered, goats = await chm.render_and_publish_template(
            user_id="u",
            category="c",
            key="k",
            values={"name": "Carol"},
            return_websocket_message=True,
        )
        assert rendered == "Yo Carol"
        ok("render messy serialized template")
    except Exception as e:
        fail("render messy serialized template", e)

    # Discard dict-like template without content
    try:
        crud_mod = types.ModuleType("lnbits.extensions.cyberherd_messaging.crud")
        crud_mod.get_message_template = fake_get_message_template_discard
        sys.modules["lnbits.extensions.cyberherd_messaging.crud"] = crud_mod
        rendered, goats = await chm.render_and_publish_template(
            user_id="u",
            category="c",
            key="k",
            values={},
            return_websocket_message=True,
        )
        assert rendered == ""
        ok("discard dict-like template without content")
    except Exception as e:
        fail("discard dict-like template without content", e)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run_async_tests())

    total = PASS + FAIL
    print("\nRESULTS: {} passed, {} failed ({} total)".format(PASS, FAIL, total))
    sys.exit(0 if FAIL == 0 else 2)
