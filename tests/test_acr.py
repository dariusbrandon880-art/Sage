"""Tests for SAGE ACR bridge."""

import pytest
from sage.acr import ACRBridge


class TestACRBridge:
    """Test cases for ACRBridge."""

    def test_acr_initialization(self):
        """Test ACR bridge initializes correctly."""
        bridge = ACRBridge(use_persistence=False)
        assert bridge is not None
        assert len(bridge.continuity_state) == 0
        assert len(bridge.session_lineage) == 0

    def test_save_and_load_state(self):
        """Test saving and loading continuity state."""
        bridge = ACRBridge(use_persistence=False)
        state = {"key_1": "value_1", "key_2": 42}
        
        bridge.save_state(state)
        loaded_state = bridge.load_state()
        
        assert loaded_state == state

    def test_session_lineage(self):
        """Test session lineage tracking."""
        bridge = ACRBridge(use_persistence=False)
        bridge.add_session_link("session_1")
        bridge.add_session_link("session_2")
        bridge.add_session_link("session_3")
        
        lineage = bridge.get_lineage()
        assert lineage == ["session_1", "session_2", "session_3"]

    def test_lineage_independence(self):
        """Test that lineage copy is independent."""
        bridge = ACRBridge(use_persistence=False)
        bridge.add_session_link("session_1")
        
        lineage = bridge.get_lineage()
        lineage.append("session_2")  # Modify the returned list
        
        # Original lineage should be unchanged
        assert bridge.get_lineage() == ["session_1"]
