"""
Connection mixin for AutoCAD adapter.

Handles connection, disconnection, and validation methods.
"""

import logging
import sys
import time
from typing import TYPE_CHECKING, Any

if sys.platform == "win32":
    import win32com.client
    import pythoncom
    import pywintypes
else:
    raise ImportError("AutoCAD adapter requires Windows OS with COM support")

from core import CADConnectionError
from adapters.prog_id_resolver import ProgIdCandidate, get_prog_id_resolver

if TYPE_CHECKING:
    from core.config import CADConfig

logger = logging.getLogger(__name__)


class ConnectionMixin:
    """Mixin for connection management."""

    if TYPE_CHECKING:
        # Tell type checker this mixin is used with CADAdapterProtocol
        cad_type: str
        config: "CADConfig"
        application: Any
        document: Any

        def _wait_for(
            self, condition: Any, timeout: float = 20.0, interval: float = 0.1
        ) -> bool: ...

    def connect(
        self,
        only_if_running: bool = False,
        preferred_prog_id: str | None = None,
    ) -> bool:
        """Connect to the CAD application via COM, initializing COM for this thread.

        Tries to attach to an already-running instance first. If none is found
        and ``only_if_running`` is False, launches a new instance.

        Args:
            only_if_running: When True, return False instead of launching a new
                CAD instance if none is currently running.

        Returns:
            True if the connection was established successfully.

        Raises:
            CADConnectionError: If COM initialization fails or the ProgID is invalid.
        """
        com_initialized = False
        try:
            logger.info(f"Connecting to {self.cad_type}...")

            # Initialize COM for this thread
            # CoInitialize() may raise if already initialized, which is fine
            try:
                pythoncom.CoInitialize()
                com_initialized = True
            except Exception as e:
                logger.debug(
                    f"CoInitialize: {e} (may already be initialized for thread)"
                )

            resolver = get_prog_id_resolver()
            candidates = resolver.discover(self.cad_type, self.config.prog_id)
            if not candidates:
                raise CADConnectionError(
                    self.cad_type, "No configured or registered COM ProgID was found"
                )
            candidates = self._prioritize_candidate(candidates, preferred_prog_id)

            self.application = None
            self.document = None
            active_candidate = self._attach_to_running_instance(candidates)

            if active_candidate is None:
                if only_if_running:
                    logger.debug(
                        f"{self.cad_type} not running and only_if_running=True. Skipping launch."
                    )
                    if com_initialized:
                        pythoncom.CoUninitialize()
                    return False

                active_candidate = self._launch_registered_instance(candidates)

            # Get active document or create new
            if self.application is not None:
                # Standard AutoCAD/ZWCAD/BricsCAD/GstarCAD handling
                if self.application.Documents.Count > 0:
                    self.document = self.application.ActiveDocument
                    logger.info("Using existing active document")
                else:
                    self.document = self.application.Documents.Add()
                    logger.info("Created new document")

            # Validate connection
            if not self._validate_document():
                raise CADConnectionError(self.cad_type, "Document validation failed")

            self.active_prog_id = active_candidate.prog_id
            resolver.remember(self.cad_type, active_candidate.prog_id)

            logger.info(
                "Successfully connected to %s via %s",
                self.cad_type,
                active_candidate.prog_id,
            )

            return True

        except pywintypes.com_error as e:
            self._cleanup_failed_connection(com_initialized)
            error_msg = f"COM error: {str(e)}"
            logger.error(f"Failed to connect to {self.cad_type}: {error_msg}")
            raise CADConnectionError(self.cad_type, error_msg)
        except Exception as e:
            self._cleanup_failed_connection(com_initialized)
            logger.error(f"Failed to connect to {self.cad_type}: {e}")
            raise CADConnectionError(self.cad_type, str(e))

    def _prioritize_candidate(
        self,
        candidates: list[ProgIdCandidate],
        preferred_prog_id: str | None,
    ) -> list[ProgIdCandidate]:
        if not preferred_prog_id:
            return candidates

        normalized_preference = preferred_prog_id.casefold()
        preferred = next(
            (
                candidate
                for candidate in candidates
                if candidate.prog_id.casefold() == normalized_preference
            ),
            None,
        )
        if preferred is None:
            allowed = ", ".join(candidate.prog_id for candidate in candidates)
            raise CADConnectionError(
                self.cad_type,
                f"ProgID '{preferred_prog_id}' was not discovered. Allowed: [{allowed}]",
            )
        return [preferred, *(candidate for candidate in candidates if candidate != preferred)]

    def _cleanup_failed_connection(self, com_initialized: bool) -> None:
        self.application = None
        self.document = None
        self.active_prog_id = None
        if com_initialized:
            try:
                pythoncom.CoUninitialize()
            except Exception as exc:
                logger.debug("CoUninitialize after connection failure: %s", exc)

    def _attach_to_running_instance(
        self, candidates: list[ProgIdCandidate]
    ) -> ProgIdCandidate | None:
        """Attach to the first active object exposed by a discovered ProgID."""
        attach_passes = 3
        for attempt in range(attach_passes):
            for candidate in candidates:
                try:
                    self.application = win32com.client.GetActiveObject(
                        candidate.prog_id
                    )
                    logger.info(
                        "%s instance found via %s (%s)",
                        self.cad_type,
                        candidate.prog_id,
                        candidate.source,
                    )
                    return candidate
                except Exception as exc:
                    logger.debug(
                        "GetActiveObject failed for %s: %s",
                        candidate.prog_id,
                        exc,
                    )
            if attempt < attach_passes - 1:
                time.sleep(0.25)
        return None

    def _launch_registered_instance(
        self, candidates: list[ProgIdCandidate]
    ) -> ProgIdCandidate:
        """Launch the first candidate whose COM registration is usable."""
        failures = []
        for candidate in candidates:
            logger.info(
                "Starting %s via %s (%s)...",
                self.cad_type,
                candidate.prog_id,
                candidate.source,
            )
            try:
                self.application = win32com.client.Dispatch(candidate.prog_id)
            except Exception as exc:
                if candidate.source == "cache":
                    get_prog_id_resolver().forget(
                        self.cad_type, candidate.prog_id
                    )
                failures.append(f"{candidate.prog_id}: {exc}")
                logger.debug("Dispatch failed for %s: %s", candidate.prog_id, exc)
                continue

            if self.application is not None:
                try:
                    self.application.Visible = True
                except (pywintypes.com_error, AttributeError) as exc:
                    logger.debug("Visible property unavailable: %s", exc)
                self._wait_for(
                    lambda: self.application is not None,
                    timeout=self.config.startup_wait_time,
                )
                return candidate

        attempted = ", ".join(candidate.prog_id for candidate in candidates)
        last_failure = failures[-1] if failures else "no COM object returned"
        raise CADConnectionError(
            self.cad_type,
            f"No usable ProgID among [{attempted}]. Last error: {last_failure}",
        )

    def discover_connections(self) -> list[dict[str, Any]]:
        """Probe discovered ProgIDs without changing this adapter's state."""
        com_initialized = False
        try:
            pythoncom.CoInitialize()
            com_initialized = True
        except Exception as exc:
            logger.debug("CoInitialize during discovery: %s", exc)

        resolver = get_prog_id_resolver()
        candidates = resolver.discover(self.cad_type, self.config.prog_id)
        results = []
        try:
            for candidate in candidates:
                result = candidate.to_dict()
                try:
                    application = win32com.client.GetActiveObject(candidate.prog_id)
                    result.update(
                        {
                            "running": True,
                            "caption": str(getattr(application, "Caption", "")),
                        }
                    )
                except Exception as exc:
                    result.update({"running": False, "error": str(exc)})
                results.append(result)
        finally:
            if com_initialized:
                pythoncom.CoUninitialize()
        return results

    def disconnect(self) -> bool:
        """Disconnect from CAD application with COM cleanup."""
        try:
            if self.application:
                self.application = None
                self.document = None
                self.active_prog_id = None
            pythoncom.CoUninitialize()
            logger.info(f"Disconnected from {self.cad_type}")
            return True
        except Exception as e:
            logger.error(f"Error disconnecting: {e}")
            return False

    def __enter__(self):
        """Enter context: connect to CAD application.

        Allows using the adapter as a context manager:
            with AutoCADAdapter("autocad") as adapter:
                adapter.draw_line((0,0), (10,10))
                # Auto-disconnect on exit

        Returns:
            Self (the adapter instance)

        Raises:
            CADConnectionError: If connection fails
        """
        if not self.connect():
            raise CADConnectionError(
                self.cad_type, "Connection failed during context manager initialization"
            )
        return self

    def __exit__(self, _exc_type, _exc_val, _exc_tb) -> None:
        """Exit context: disconnect from CAD application.

        Args:
            _exc_type: Exception type if raised
            _exc_val: Exception value if raised
            _exc_tb: Exception traceback if raised
        """
        self.disconnect()

    def is_connected(self) -> bool:
        """Check if connected to CAD application."""
        try:
            return (
                self.application is not None
                and self.document is not None
                and self._validate_document()
            )
        except Exception:
            return False

    def _validate_document(self) -> bool:
        """Validate that document is accessible."""
        try:
            if self.document is None:
                return False
            _ = self.document.Name
            return True
        except Exception:
            return False

    def check_document_change(self) -> bool:
        """
        Check if the active document in the CAD application has changed.
        If it has, update self.document to the new active document.

        Returns:
            bool: True if the document changed, False otherwise.
        """
        try:
            if not self.application:
                return False

            # If no documents are open, there's nothing to check
            if self.application.Documents.Count == 0:
                if self.document is not None:
                    self.document = None
                    return True
                return False

            active_doc = self.application.ActiveDocument

            # If we didn't have a document before, but now we do
            if self.document is None:
                self.document = active_doc
                return True

            # Compare names
            if self.document.Name != active_doc.Name:
                self.document = active_doc
                logger.info(f"Active document changed to: {active_doc.Name}")
                return True

            return False
        except Exception as e:
            # Silently catch COM errors during polling
            logger.debug(f"Error checking document change: {e}")
            return False
