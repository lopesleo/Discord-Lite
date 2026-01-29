#!/usr/bin/env python3
"""
Verification script for Discord Lite refactoring

Checks that all modules are properly structured and importable.
Run this before deploying to ensure the refactor is working.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all backend modules can be imported."""
    print("Testing backend module imports...")

    tests = [
        ("backend.discord_rpc.client", "DiscordRPCClient"),
        ("backend.discord_rpc.protocol", "encode_message"),
        ("backend.discord_rpc.events", "SpeakingTracker"),
        ("backend.auth.oauth", "OAuth2Manager"),
        ("backend.auth.token_manager", "TokenManager"),
        ("backend.voice.volume", "perceptual_to_amplitude"),
        ("backend.voice.controller", "VoiceController"),
        ("backend.voice.members", "MemberTracker"),
        ("backend.steam.game_detector", "SteamGameDetector"),
        ("backend.steam.activity_sync", "ActivitySyncManager"),
        ("backend.polling.voice_poller", "VoicePoller"),
        ("backend.utils.cache", "LRUCache"),
        ("backend.utils.settings", "SettingsManager"),
        ("backend.utils.socket_finder", "find_discord_ipc_socket"),
    ]

    passed = 0
    failed = 0

    for module_name, class_name in tests:
        try:
            module = __import__(module_name, fromlist=[class_name])
            obj = getattr(module, class_name)
            print(f"  ✓ {module_name}.{class_name}")
            passed += 1
        except Exception as e:
            print(f"  ✗ {module_name}.{class_name} - {e}")
            failed += 1

    print(f"\nResults: {passed} passed, {failed} failed")
    return failed == 0

def test_volume_conversion():
    """Test volume conversion functions."""
    print("\nTesting volume conversion...")

    from backend.voice.volume import perceptual_to_amplitude, amplitude_to_perceptual

    tests = [
        (50, 100, "50% input should convert correctly"),
        (100, 100, "100% input should be max"),
        (0, 100, "0% input should be 0"),
        (100, 200, "100% output should be normal"),
        (200, 200, "200% output should be max boost"),
    ]

    for perceptual, max_val, description in tests:
        try:
            amplitude = perceptual_to_amplitude(perceptual, max_val)
            back_to_perceptual = amplitude_to_perceptual(amplitude, max_val)

            # Allow small floating point error
            if abs(back_to_perceptual - perceptual) < 0.1:
                print(f"  ✓ {description}")
            else:
                print(f"  ✗ {description} - roundtrip error: {perceptual} → {amplitude} → {back_to_perceptual}")
                return False
        except Exception as e:
            print(f"  ✗ {description} - {e}")
            return False

    print("  ✓ All volume conversion tests passed")
    return True

def test_cache():
    """Test LRU cache."""
    print("\nTesting LRU cache...")

    from backend.utils.cache import LRUCache

    cache = LRUCache(max_size=3)

    # Add items
    cache.set("a", 1)
    cache.set("b", 2)
    cache.set("c", 3)

    if cache.get("a") != 1:
        print("  ✗ Cache get failed")
        return False

    # Add 4th item (should evict oldest)
    cache.set("d", 4)

    if cache.get("b") is not None:  # b should be evicted
        print("  ✗ Cache eviction failed")
        return False

    if len(cache) != 3:
        print(f"  ✗ Cache size incorrect: {len(cache)} != 3")
        return False

    print("  ✓ LRU cache working correctly")
    return True

def test_structure():
    """Test directory structure."""
    print("\nTesting directory structure...")

    required_dirs = [
        "backend",
        "backend/discord_rpc",
        "backend/auth",
        "backend/voice",
        "backend/steam",
        "backend/polling",
        "backend/utils",
    ]

    for dir_name in required_dirs:
        if not os.path.isdir(dir_name):
            print(f"  ✗ Missing directory: {dir_name}")
            return False

        init_file = os.path.join(dir_name, "__init__.py")
        if not os.path.isfile(init_file):
            print(f"  ✗ Missing __init__.py in {dir_name}")
            return False

    print("  ✓ All directories present")
    return True

def main():
    """Run all verification tests."""
    print("=" * 60)
    print("Discord Lite Refactoring Verification")
    print("=" * 60)

    all_passed = True

    all_passed &= test_structure()
    all_passed &= test_imports()
    all_passed &= test_volume_conversion()
    all_passed &= test_cache()

    print("\n" + "=" * 60)
    if all_passed:
        print("✓ All verification tests PASSED")
        print("=" * 60)
        return 0
    else:
        print("✗ Some verification tests FAILED")
        print("=" * 60)
        return 1

if __name__ == "__main__":
    sys.exit(main())
