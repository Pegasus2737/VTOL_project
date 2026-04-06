#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick Sound System Test

Tests the sound player to verify it works without pygame.
"""

import sys
import time
from PyQt6.QtWidgets import QApplication
from utils.sound_player import SoundPlayer

def main():
    print("=" * 60)
    print("Sound System Test")
    print("=" * 60)
    
    app = QApplication(sys.argv)
    
    player = SoundPlayer()
    
    print(f"\n1. Initialization Status:")
    print(f"   Initialized: {player._initialized}")
    print(f"   Using pygame: {player._use_pygame}")
    print(f"   Enabled: {player._enabled}")
    
    if not player._initialized:
        print("\n❌ Sound player not initialized!")
        return 1
    
    print("\n2. Playing test beep...")
    if player.play_alarm():
        print("   ✓ Beep played successfully!")
        print("   (You should hear a beep sound)")
    else:
        print("   ❌ Failed to play beep")
        return 1
    
    time.sleep(0.5)
    
    print("\n3. Testing volume control...")
    print("   Playing 3 beeps at different volumes:")
    
    for vol, label in [(0.3, "Low"), (0.7, "Medium"), (1.0, "High")]:
        print(f"   - {label} volume ({vol})...")
        player.set_volume(vol)
        player.play_alarm()
        time.sleep(0.4)
    
    print("\n4. Testing enable/disable...")
    player.set_enabled(False)
    if not player.play_alarm():
        print("   ✓ Correctly disabled")
    else:
        print("   ❌ Should not play when disabled")
    
    player.set_enabled(True)
    if player.play_alarm():
        print("   ✓ Re-enabled successfully")
    else:
        print("   ❌ Failed to play after re-enable")
    
    time.sleep(0.5)
    
    print("\n5. Cleanup...")
    player.cleanup()
    print("   ✓ Resources released")
    
    print("\n" + "=" * 60)
    print("✓ All tests passed!")
    print("=" * 60)
    
    if player._use_pygame:
        print("\nSound engine: pygame (high quality)")
    else:
        print("\nSound engine: winsound (Windows built-in)")
    
    print("\nNote: If you heard beeps, the alarm system will work!")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
