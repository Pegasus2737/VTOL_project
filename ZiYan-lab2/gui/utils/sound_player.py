#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sound Player

Plays alarm sounds using multiple fallback methods:
1. Try pygame mixer (if available)
2. Fall back to winsound (Windows built-in)
3. Fall back to silent mode

Non-blocking playback with volume control.
"""

from pathlib import Path
from typing import Optional
from PyQt6.QtCore import QObject

# Try to import pygame, but don't fail if unavailable
try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    print("Warning: pygame not available, using winsound fallback")


class SoundPlayer(QObject):
    """Sound player for alarm notifications"""
    
    def __init__(self):
        """Initialize sound player"""
        super().__init__()
        self._initialized = False
        self._enabled = True
        self._volume = 0.7  # 0.0 to 1.0
        self._use_pygame = False
        
        if PYGAME_AVAILABLE:
            try:
                pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
                self._initialized = True
                self._use_pygame = True
                print("✓ Sound player initialized (pygame)")
            except Exception as e:
                print(f"Warning: pygame mixer failed: {e}")
                self._initialized = True  # Still usable with winsound
                self._use_pygame = False
                print("✓ Sound player initialized (winsound fallback)")
        else:
            self._initialized = True  # Use winsound
            self._use_pygame = False
            print("✓ Sound player initialized (winsound fallback)")
    
    def set_enabled(self, enabled: bool) -> None:
        """
        Enable or disable sound playback
        
        Args:
            enabled: True to enable sound
        """
        self._enabled = enabled
    
    def set_volume(self, volume: float) -> None:
        """
        Set playback volume
        
        Args:
            volume: Volume level 0.0 to 1.0
        """
        self._volume = max(0.0, min(1.0, volume))
    
    def play_alarm(self, sound_file: Optional[str] = None) -> bool:
        """
        Play alarm sound
        
        Args:
            sound_file: Path to sound file (None for default beep)
            
        Returns:
            bool: True if sound played successfully
        """
        if not self._enabled or not self._initialized:
            return False
        
        try:
            if self._use_pygame and sound_file and Path(sound_file).exists():
                # Play custom sound file with pygame
                sound = pygame.mixer.Sound(sound_file)
                sound.set_volume(self._volume)
                sound.play()
            else:
                # Play beep (pygame or winsound)
                self._play_beep()
            
            return True
            
        except Exception as e:
            print(f"Error playing sound: {e}")
            # Try winsound fallback
            try:
                import winsound
                winsound.Beep(440, 200)
                return True
            except:
                return False
    
    def _play_beep(self) -> None:
        """Play a generated beep sound"""
        if self._use_pygame and PYGAME_AVAILABLE:
            # Try pygame with numpy
            try:
                import numpy as np
                
                # Generate 440Hz beep (A4 note) for 0.2 seconds
                sample_rate = 22050
                duration = 0.2
                frequency = 440
                
                # Generate sine wave
                samples = int(sample_rate * duration)
                wave = np.sin(2 * np.pi * frequency * np.linspace(0, duration, samples))
                
                # Apply envelope (fade in/out to avoid clicks)
                envelope = np.ones(samples)
                fade_samples = int(sample_rate * 0.02)  # 20ms fade
                envelope[:fade_samples] = np.linspace(0, 1, fade_samples)
                envelope[-fade_samples:] = np.linspace(1, 0, fade_samples)
                wave = wave * envelope
                
                # Convert to 16-bit PCM
                wave = (wave * 32767 * self._volume).astype(np.int16)
                
                # Create stereo sound (duplicate mono to both channels)
                stereo_wave = np.column_stack((wave, wave))
                
                # Play sound
                sound = pygame.sndarray.make_sound(stereo_wave)
                sound.play()
                return
                
            except Exception as e:
                print(f"pygame beep failed: {e}")
        
        # Fallback: Windows system beep
        try:
            import winsound
            # Adjust duration based on volume (louder = longer feel)
            duration_ms = int(200 * self._volume)
            duration_ms = max(100, min(500, duration_ms))  # Clamp 100-500ms
            winsound.Beep(440, duration_ms)
        except Exception as e:
            print(f"winsound beep failed: {e}")
    
    def stop_all(self) -> None:
        """Stop all playing sounds"""
        if self._initialized and self._use_pygame and PYGAME_AVAILABLE:
            try:
                pygame.mixer.stop()
            except:
                pass
    
    def cleanup(self) -> None:
        """Cleanup resources"""
        if self._initialized and self._use_pygame and PYGAME_AVAILABLE:
            try:
                pygame.mixer.quit()
            except:
                pass
            self._initialized = False


# Global sound player instance
_sound_player_instance: Optional[SoundPlayer] = None


def get_sound_player() -> SoundPlayer:
    """
    Get global sound player instance (singleton pattern)
    
    Returns:
        SoundPlayer: Global sound player
    """
    global _sound_player_instance
    if _sound_player_instance is None:
        _sound_player_instance = SoundPlayer()
    return _sound_player_instance


if __name__ == "__main__":
    """Test sound player"""
    from PyQt6.QtWidgets import QApplication
    import sys
    import time
    
    print("=== Sound Player Test ===\n")
    
    app = QApplication(sys.argv)
    
    player = SoundPlayer()
    
    # Test 1: Check initialization
    print(f"1. Initialized: {player._initialized}")
    print(f"   Enabled: {player._enabled}")
    print(f"   Volume: {player._volume}\n")
    
    # Test 2: Play beep at default volume
    print("2. Playing beep at default volume (0.7)...")
    player.play_alarm()
    time.sleep(0.5)
    
    # Test 3: Play beep at low volume
    print("3. Playing beep at low volume (0.3)...")
    player.set_volume(0.3)
    player.play_alarm()
    time.sleep(0.5)
    
    # Test 4: Play beep at high volume
    print("4. Playing beep at high volume (1.0)...")
    player.set_volume(1.0)
    player.play_alarm()
    time.sleep(0.5)
    
    # Test 5: Multiple beeps
    print("5. Playing 3 rapid beeps...")
    player.set_volume(0.7)
    for i in range(3):
        player.play_alarm()
        time.sleep(0.3)
    
    time.sleep(0.5)
    
    # Test 6: Disable and try to play
    print("\n6. Disabling sound...")
    player.set_enabled(False)
    result = player.play_alarm()
    print(f"   Play result (should be False): {result}")
    
    # Test 7: Re-enable
    print("\n7. Re-enabling sound...")
    player.set_enabled(True)
    player.play_alarm()
    time.sleep(0.5)
    
    # Test 8: Global instance
    print("\n8. Testing global instance...")
    global_player = get_sound_player()
    print(f"   Same instance: {global_player is player}")
    
    # Cleanup
    print("\n9. Cleanup...")
    player.cleanup()
    print("   Resources released")
    
    print("\n✓ Test completed!")
    print("Note: If you heard beeps, audio is working correctly.")
