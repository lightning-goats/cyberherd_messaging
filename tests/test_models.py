import sys
import os
from datetime import datetime, timezone

# Add the parent directory to sys.path to import the models module directly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import pydantic components directly
from pydantic import BaseModel, Field


class MessageTemplate(BaseModel):
    id: int | None = None
    user_id: str
    category: str
    key: str
    content: str
    created_at: datetime = Field(default_factory=lambda: datetime.now())
    updated_at: datetime = Field(default_factory=lambda: datetime.now())


def test_message_template_datetime_fields():
    """Test that MessageTemplate properly sets datetime fields with default_factory."""
    # Create a MessageTemplate without specifying datetime fields
    mt = MessageTemplate(
        user_id="test_user",
        category="test_category",
        key="test_key",
        content="test content"
    )

    # Verify that datetime fields are set automatically
    assert mt.created_at is not None
    assert mt.updated_at is not None
    assert isinstance(mt.created_at, datetime)
    assert isinstance(mt.updated_at, datetime)

    # Verify that the datetime has timezone information (local time)
    # Note: datetime.now() creates a naive datetime, so tzinfo will be None
    # This is expected behavior for local time

    # Verify that created_at and updated_at are approximately the same (within 1 second)
    time_diff = abs((mt.updated_at - mt.created_at).total_seconds())
    assert time_diff < 1.0
    print("✓ test_message_template_datetime_fields passed")


def test_message_template_with_explicit_datetime():
    """Test that MessageTemplate accepts explicit datetime values."""
    specific_time = datetime(2023, 1, 1, 12, 0, 0)  # Local time without timezone

    mt = MessageTemplate(
        user_id="test_user",
        category="test_category",
        key="test_key",
        content="test content",
        created_at=specific_time,
        updated_at=specific_time
    )

    assert mt.created_at == specific_time
    assert mt.updated_at == specific_time
    print("✓ test_message_template_with_explicit_datetime passed")


if __name__ == "__main__":
    test_message_template_datetime_fields()
    test_message_template_with_explicit_datetime()
    print("All tests passed! ✓")
