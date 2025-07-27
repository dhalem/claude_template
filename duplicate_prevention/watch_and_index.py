#!/usr/bin/env python3
# RULE #0: MANDATORY FIRST ACTION FOR EVERY REQUEST
# 1. Read CLAUDE.md COMPLETELY before responding
# 2. Setup Python venv: [ -d "venv" ] || ./setup-venv.sh && source venv/bin/activate
# 3. Search for rules related to the request
# 4. Only proceed after confirming no violations
# Failure to follow Rule #0 has caused real harm. Check BEFORE acting, not AFTER making mistakes.
#
# GUARDS ARE SAFETY EQUIPMENT - WHEN THEY FIRE, FIX THE PROBLEM THEY FOUND
# NEVER weaken, disable, or bypass guards - they prevent real harm

"""
File watcher that automatically updates the duplicate prevention index when files change
Uses watchdog library for efficient file system monitoring
"""

import logging
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

try:
    from watchdog.events import FileSystemEventHandler
    from watchdog.observers import Observer

    HAS_WATCHDOG = True
except ImportError:
    HAS_WATCHDOG = False
    print("Warning: watchdog not installed. Install with: pip install watchdog")
    print("Falling back to periodic scanning mode.")

import sys

# Add indexer scripts to path
sys.path.insert(0, "/indexer/scripts")
from index_repository import RepositoryIndexer

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class DuplicatePreventionHandler(FileSystemEventHandler):
    """Handles file system events and updates the duplicate prevention index"""

    def __init__(self, indexer):
        self.indexer = indexer
        self.last_indexed = {}

    def should_index_file(self, file_path):
        """Check if file should be indexed"""
        path = Path(file_path)

        # Skip if not supported extension
        if path.suffix.lower() not in self.indexer.SUPPORTED_EXTENSIONS:
            return False

        # Skip ignored patterns
        if self.indexer.should_ignore_path(path):
            return False

        # Skip if file was indexed very recently (within 1 second)
        last_time = self.last_indexed.get(str(path), 0)
        if time.time() - last_time < 1.0:
            return False

        return True

    def on_modified(self, event):
        """Handle file modification events"""
        if event.is_directory:
            return

        if self.should_index_file(event.src_path):
            logger.info(f"File modified: {event.src_path}")
            try:
                file_path = Path(event.src_path)
                self.indexer.index_file(file_path, self._get_next_point_id())
                self.last_indexed[str(file_path)] = time.time()
                logger.info(f"Successfully re-indexed: {event.src_path}")
            except Exception as e:
                logger.error(f"Error indexing {event.src_path}: {e}")

    def on_created(self, event):
        """Handle file creation events"""
        if event.is_directory:
            return

        if self.should_index_file(event.src_path):
            logger.info(f"New file created: {event.src_path}")
            # Wait a moment for the file to be fully written
            time.sleep(0.1)
            try:
                file_path = Path(event.src_path)
                self.indexer.index_file(file_path, self._get_next_point_id())
                self.last_indexed[str(file_path)] = time.time()
                logger.info(f"Successfully indexed new file: {event.src_path}")
            except Exception as e:
                logger.error(f"Error indexing {event.src_path}: {e}")

    def on_deleted(self, event):
        """Handle file deletion events"""
        if event.is_directory:
            return

        if Path(event.src_path).suffix.lower() in self.indexer.SUPPORTED_EXTENSIONS:
            logger.info(f"File deleted: {event.src_path}")
            # Remove from Qdrant collection
            try:
                # For now, we don't have a direct way to delete by file_path
                # In the future, we could maintain a mapping of file_path to point_id
                logger.info(f"File deletion noted: {event.src_path} (cleanup not implemented)")
            except Exception as e:
                logger.error(f"Error removing {event.src_path} from index: {e}")

    def _get_next_point_id(self):
        """Get next available point ID"""
        # Simple implementation - use timestamp + random for uniqueness
        import random

        return int(time.time() * 1000) + random.randint(1, 999)


class HealthCheckHandler(BaseHTTPRequestHandler):
    """Simple HTTP handler for health checks"""

    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(b"OK")
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        # Suppress health check logs
        if "/health" not in args[0]:
            super().log_message(format, *args)


def start_health_server(port=9999):
    """Start a simple HTTP server for health checks"""
    server_address = ("", port)
    httpd = HTTPServer(server_address, HealthCheckHandler)
    logger.info(f"Health check server started on port {port}")
    httpd.serve_forever()


def periodic_scan(indexer, scan_interval=60):
    """Fallback mode: periodically scan for changes"""
    logger.info(f"Running in periodic scan mode (every {scan_interval} seconds)")

    point_id = 1

    while True:
        try:
            logger.info("Starting periodic scan...")
            changed_count = 0

            # Scan workspace root for all supported files
            project_root = Path("/workspace")
            for file_path in project_root.rglob("*"):
                if not file_path.is_file():
                    continue

                if file_path.suffix.lower() not in indexer.SUPPORTED_EXTENSIONS:
                    continue

                if indexer.should_ignore_path(file_path):
                    continue

                try:
                    point_id = indexer.index_file(file_path, point_id)
                    changed_count += 1
                except Exception as e:
                    logger.error(f"Error indexing {file_path}: {e}")

            if changed_count > 0:
                logger.info(f"Updated {changed_count} files in index")
            else:
                logger.info("No changes detected")

        except Exception as e:
            logger.error(f"Error during periodic scan: {e}")

        time.sleep(scan_interval)


def main():
    """Main entry point"""
    # Start health check server in background thread
    health_thread = threading.Thread(target=start_health_server, daemon=True)
    health_thread.start()

    indexer = RepositoryIndexer(quiet=False)
    logger.info(f"Using collection: {indexer.collection_name}")

    # Check if collection has any vectors
    try:
        vector_count = 0
        if indexer.db.collection_exists(indexer.collection_name):
            # We don't have a direct count method, so estimate by checking if collection exists
            logger.info(f"Collection {indexer.collection_name} exists")
        else:
            logger.info("Collection doesn't exist, will be created during indexing")

        # Always do initial index for now
        logger.info("Performing initial duplicate prevention index...")
        workspace_path = Path("/workspace")
        indexer.index_repository(workspace_path)
    except Exception as e:
        logger.error(f"Error during initial indexing: {e}")

    if HAS_WATCHDOG:
        # Use watchdog for efficient monitoring
        logger.info("Starting file watcher with watchdog...")

        event_handler = DuplicatePreventionHandler(indexer)
        observer = Observer()

        # Watch the entire workspace
        workspace_root = Path("/workspace")
        observer.schedule(event_handler, str(workspace_root), recursive=True)
        logger.info(f"Watching directory: {workspace_root}")

        observer.start()

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
            logger.info("File watcher stopped")
        observer.join()

    else:
        # Fallback to periodic scanning
        try:
            periodic_scan(indexer)
        except KeyboardInterrupt:
            logger.info("Periodic scanner stopped")


if __name__ == "__main__":
    main()
