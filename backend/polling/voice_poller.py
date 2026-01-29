"""Background polling thread for voice channel events"""

import threading
import time
from queue import Queue
from typing import Optional


class VoicePoller:
    """
    Background polling system for voice channel member changes and game sync.

    Runs in separate thread to avoid blocking the main plugin thread.
    Uses adaptive polling intervals to save battery when idle.
    """

    def __init__(self, logger=None):
        """
        Initialize voice poller with default settings.

        Args:
            logger: Logger instance for logging operations
        """
        self.logger = logger
        self.active = False
        self.thread: Optional[threading.Thread] = None
        self.event_queue = Queue()

        # Callbacks
        self.check_members_callback = None
        self.sync_game_callback = None
        self.is_active_callback = None  # Returns True if user is in voice or game running

    def start(self, check_members_callback, sync_game_callback, is_active_callback) -> None:
        """
        Start background polling thread.

        Args:
            check_members_callback: Function to check voice member changes
            sync_game_callback: Function to sync game status
            is_active_callback: Function returning True if user is active (in voice or game)
        """
        if self.active:
            if self.logger:
                self.logger.warning("Discord Lite: Polling already active")
            return

        self.check_members_callback = check_members_callback
        self.sync_game_callback = sync_game_callback
        self.is_active_callback = is_active_callback

        self.active = True
        self.thread = threading.Thread(target=self._polling_loop, daemon=True)
        self.thread.start()

        if self.logger:
            self.logger.info("Discord Lite: Voice polling started")

    def stop(self) -> None:
        """Stop background polling thread."""
        self.active = False

        if self.thread:
            self.thread = None

        if self.logger:
            self.logger.info("Discord Lite: Voice polling stopped")

    def _polling_loop(self) -> None:
        """
        Main polling loop with adaptive intervals.

        Uses 15-second intervals when active (in voice or game running),
        60-second intervals when idle to save battery.
        """
        while self.active:
            try:
                loop_start_time = time.time()

                # Execute callbacks
                if self.check_members_callback:
                    try:
                        self.check_members_callback()
                    except Exception as e:
                        if self.logger:
                            self.logger.error(f"Discord Lite: Error in check_members callback: {e}")

                if self.sync_game_callback:
                    try:
                        self.sync_game_callback()
                    except Exception as e:
                        if self.logger:
                            self.logger.error(f"Discord Lite: Error in sync_game callback: {e}")

                # Determine polling interval based on activity
                is_active = False
                if self.is_active_callback:
                    try:
                        is_active = self.is_active_callback()
                    except Exception as e:
                        if self.logger:
                            self.logger.error(f"Discord Lite: Error in is_active callback: {e}")

                # Adaptive interval: 15s when active, 60s when idle
                target_interval = 15.0 if is_active else 60.0

                # Calculate sleep time accounting for work done
                elapsed = time.time() - loop_start_time
                sleep_time = max(1.0, target_interval - elapsed)

                time.sleep(sleep_time)

            except Exception as e:
                if self.logger:
                    self.logger.error(f"Discord Lite: Error in polling loop: {e}")
                time.sleep(20.0)  # Error recovery delay

    def enqueue_event(self, event_type: str, **event_data) -> None:
        """
        Add event to queue for frontend consumption.

        Args:
            event_type: Event type string (e.g., "VOICE_JOIN")
            **event_data: Additional event data as keyword arguments
        """
        event = {"type": event_type, **event_data}
        self.event_queue.put(event)

    def get_pending_events(self) -> list[dict]:
        """
        Get all pending events from queue (non-blocking).

        Returns:
            List of event dictionaries
        """
        events = []

        while not self.event_queue.empty():
            try:
                event = self.event_queue.get_nowait()
                events.append(event)
            except:
                break

        return events

    def is_running(self) -> bool:
        """
        Check if polling thread is running.

        Returns:
            True if active, False otherwise
        """
        return self.active
