"""OSC bridge for communicating with Bitwig via DrivenByMoss."""

import logging
from typing import Any, Callable
import threading

from pythonosc import udp_client

logger = logging.getLogger(__name__)
from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import ThreadingOSCUDPServer

from bwctl.config import settings


class BitwigOSCBridge:
    """Bridge for sending OSC commands to Bitwig via DrivenByMoss.

    DrivenByMoss OSC protocol documentation:
    https://github.com/git-moss/DrivenByMoss-Documentation/blob/master/Generic-Tools-Protocols/Open-Sound-Control-(OSC).md
    """

    def __init__(
        self,
        send_host: str | None = None,
        send_port: int | None = None,
        receive_port: int | None = None,
    ):
        """Initialize the OSC bridge.

        Args:
            send_host: Host to send OSC messages to
            send_port: Port to send OSC messages to
            receive_port: Port to receive OSC messages on
        """
        self.send_host = send_host or settings.osc.send_host
        self.send_port = send_port or settings.osc.send_port
        self.receive_port = receive_port or settings.osc.receive_port

        self.client = udp_client.SimpleUDPClient(self.send_host, self.send_port)
        self.dispatcher = Dispatcher()
        self.server: ThreadingOSCUDPServer | None = None
        self._server_thread: threading.Thread | None = None

        # State tracking
        self._state: dict[str, Any] = {}
        self._callbacks: dict[str, list[Callable]] = {}

    def start_server(self) -> None:
        """Start the OSC server to receive messages from Bitwig."""
        if self.server is not None:
            return

        self.server = ThreadingOSCUDPServer(
            ("0.0.0.0", self.receive_port),
            self.dispatcher,
        )
        self._server_thread = threading.Thread(target=self.server.serve_forever)
        self._server_thread.daemon = True
        self._server_thread.start()

    def stop_server(self) -> None:
        """Stop the OSC server."""
        if self.server:
            self.server.shutdown()
            self.server = None
            self._server_thread = None

    def send(self, address: str, *args: Any) -> None:
        """Send an OSC message.

        Args:
            address: OSC address path (e.g., "/track/1/select")
            *args: Message arguments
        """
        logger.debug(f"OSC SEND: {address} {list(args)}")
        self.client.send_message(address, list(args))

    # Transport Controls
    def play(self) -> None:
        """Start playback."""
        self.send("/play", 1)

    def stop(self) -> None:
        """Stop playback."""
        self.send("/stop", 1)

    def record(self) -> None:
        """Toggle recording."""
        self.send("/record", 1)

    def toggle_loop(self) -> None:
        """Toggle loop mode."""
        self.send("/repeat", -1)

    def set_tempo(self, bpm: float) -> None:
        """Set the tempo in BPM.

        Args:
            bpm: Tempo in beats per minute (20-666)
        """
        self.send("/tempo/raw", bpm)

    def invoke_action(self, action_id: str) -> None:
        """Invoke a Bitwig action by its ID.

        Args:
            action_id: The Bitwig action ID (e.g., "group_selected_tracks")
        """
        self.send("/action/invoke", action_id)

    # Track Operations
    def add_track(self, track_type: str) -> None:
        """Add a new track.

        Args:
            track_type: One of "audio", "instrument", "effect"
        """
        self.send(f"/track/add/{track_type}")

    def select_track(self, index: int) -> None:
        """Select a track by index (1-8).

        Args:
            index: Track index (1-indexed)
        """
        self.send(f"/track/{index}/select")

    def enter_group(self, index: int) -> None:
        """Enter a group track (hierarchical mode).

        Args:
            index: Track index of the group (1-indexed)
        """
        self.send(f"/track/{index}/enter", 1)

    def exit_group(self) -> None:
        """Exit current group to parent (hierarchical mode)."""
        self.send("/track/parent")

    def set_track_mute(self, index: int, mute: bool | None = None) -> None:
        """Set or toggle track mute.

        Args:
            index: Track index (1-indexed)
            mute: True to mute, False to unmute, None to toggle
        """
        value = 1 if mute else (0 if mute is False else -1)
        self.send(f"/track/{index}/mute", value)

    def set_track_solo(self, index: int, solo: bool | None = None) -> None:
        """Set or toggle track solo.

        Args:
            index: Track index (1-indexed)
            solo: True to solo, False to unsolo, None to toggle
        """
        value = 1 if solo else (0 if solo is False else -1)
        self.send(f"/track/{index}/solo", value)

    def set_track_arm(self, index: int, arm: bool | None = None) -> None:
        """Set or toggle track record arm.

        Args:
            index: Track index (1-indexed)
            arm: True to arm, False to disarm, None to toggle
        """
        value = 1 if arm else (0 if arm is False else -1)
        self.send(f"/track/{index}/recarm", value)

    def set_track_volume(self, index: int, value: float) -> None:
        """Set track volume.

        Args:
            index: Track index (1-indexed)
            value: Volume value (0.0 to 1.0)
        """
        # Touch the fader first (required for reliable value changes)
        self.send(f"/track/{index}/volume/touched", 1)
        # DrivenByMoss uses 0-128 range
        self.send(f"/track/{index}/volume", int(value * 128))
        # Release the touch
        self.send(f"/track/{index}/volume/touched", 0)

    def set_track_pan(self, index: int, value: float) -> None:
        """Set track pan.

        Args:
            index: Track index (1-indexed)
            value: Pan value (-1.0 = full left, 0.0 = center, 1.0 = full right)
        """
        # Touch the fader first (required for reliable value changes)
        self.send(f"/track/{index}/pan/touched", 1)
        # DrivenByMoss uses 0-128 range where 64 is center
        pan_value = int((value + 1.0) * 64)  # Convert -1..1 to 0..128
        self.send(f"/track/{index}/pan", pan_value)
        # Release the touch
        self.send(f"/track/{index}/pan/touched", 0)

    # Device Operations
    def open_device_browser(self) -> None:
        """Open the device browser."""
        self.send("/browser/device")

    def open_preset_browser(self) -> None:
        """Open the preset browser for current device."""
        self.send("/browser/preset")

    def browser_navigate(self, direction: int) -> None:
        """Navigate browser results.

        Args:
            direction: Positive for next, negative for previous
        """
        if direction > 0:
            self.send("/browser/result/+")
        else:
            self.send("/browser/result/-")

    def browser_commit(self) -> None:
        """Commit the current browser selection."""
        self.send("/browser/commit")

    def browser_cancel(self) -> None:
        """Cancel the browser."""
        self.send("/browser/cancel")

    def add_device(self, device_name: str) -> None:
        """Add a device by name to the current track (headless).

        Uses the OscByMoss /device/add command to insert a device
        directly without opening the browser.

        Args:
            device_name: Name of the device to add (e.g., "Polymer", "EQ-5")
        """
        self.send("/device/add", device_name)

    def add_master_device(self, device_name: str) -> None:
        """Add a device by name to the master track.

        Args:
            device_name: Name of the device to add (e.g., "Peak Limiter", "EQ-5")
        """
        self.send("/device/master/add", device_name)

    def insert_master_preset(self, preset_path: str) -> None:
        """Insert a preset file to the master track.

        Args:
            preset_path: Absolute path to the .bwpreset file
        """
        self.send("/device/master/file", preset_path)

    def insert_preset(self, preset_path: str) -> None:
        """Insert a preset file (.bwpreset) to the current track (headless).

        Uses the DrivenByMoss /device/file command to insert a preset
        directly without opening the browser.

        Args:
            preset_path: Absolute path to the .bwpreset file
        """
        self.send("/device/file", preset_path)

    def select_next_device(self) -> None:
        """Select the next device in the chain."""
        self.send("/device/+", 1)

    def select_previous_device(self) -> None:
        """Select the previous device in the chain."""
        self.send("/device/-", 1)

    def swap_device_with_previous(self) -> None:
        """Move the current device left (swap with previous device)."""
        self.send("/device/swap/previous")

    def swap_device_with_next(self) -> None:
        """Move the current device right (swap with next device)."""
        self.send("/device/swap/next")

    def set_device_bypass(self, bypass: bool | None = None) -> None:
        """Set or toggle device bypass.

        Args:
            bypass: True to bypass, False to enable, None to toggle
        """
        value = 1 if bypass else (0 if bypass is False else -1)
        self.send("/device/bypass", value)

    def set_device_param(self, index: int, value: float) -> None:
        """Set a device parameter value.

        Args:
            index: Parameter index (1-8)
            value: Parameter value (0.0 to 1.0)
        """
        # Touch the parameter first (required for reliable value changes)
        self.send(f"/device/param/{index}/touched", 1)
        self.send(f"/device/param/{index}/value", int(value * 128))
        self.send(f"/device/param/{index}/touched", 0)

    # Clip Operations
    def create_clip(self, track: int, slot: int, length_beats: int = 4) -> None:
        """Create a new clip.

        Args:
            track: Track index (1-indexed)
            slot: Slot index (1-indexed)
            length_beats: Clip length in beats
        """
        self.send(f"/track/{track}/clip/{slot}/create", length_beats)

    def launch_clip(self, track: int, slot: int) -> None:
        """Launch a clip.

        Args:
            track: Track index (1-indexed)
            slot: Slot index (1-indexed)
        """
        self.send(f"/track/{track}/clip/{slot}/launch", 1)

    def stop_clip(self, track: int, slot: int) -> None:
        """Stop a clip.

        Args:
            track: Track index (1-indexed)
            slot: Slot index (1-indexed)
        """
        self.send(f"/track/{track}/clip/{slot}/launch", 0)

    def stop_all_clips(self) -> None:
        """Stop all playing clips."""
        self.send("/clip/stopall")

    def insert_clip_file(self, track: int, slot: int, file_path: str) -> None:
        """Insert a file (MIDI, audio) into a clip launcher slot.

        Args:
            track: Track index (1-indexed)
            slot: Slot index (1-indexed)
            file_path: Absolute path to the file to insert
        """
        self.send(f"/track/{track}/clip/{slot}/insertFile", file_path)


# Global bridge instance
_bridge: BitwigOSCBridge | None = None


def get_bridge() -> BitwigOSCBridge:
    """Get or create the global OSC bridge instance."""
    global _bridge
    if _bridge is None:
        _bridge = BitwigOSCBridge()
    return _bridge
