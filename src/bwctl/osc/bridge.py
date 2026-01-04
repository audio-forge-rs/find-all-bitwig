"""OSC bridge for communicating with Bitwig via DrivenByMoss."""

from typing import Any, Callable
import threading

from pythonosc import udp_client
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
        # DrivenByMoss uses 0-128 range
        self.send(f"/track/{index}/volume", int(value * 128))

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
        self.send(f"/device/param/{index}/value", int(value * 128))

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


# Global bridge instance
_bridge: BitwigOSCBridge | None = None


def get_bridge() -> BitwigOSCBridge:
    """Get or create the global OSC bridge instance."""
    global _bridge
    if _bridge is None:
        _bridge = BitwigOSCBridge()
    return _bridge
