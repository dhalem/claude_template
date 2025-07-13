#!/usr/bin/env python3
"""
File watcher that automatically updates the code index when Python files change
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

from code_indexer import CodeIndexer

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class CodeIndexHandler(FileSystemEventHandler):
    """Handles file system events and updates the code index"""

    def __init__(self, indexer):
        self.indexer = indexer
        self.last_indexed = {}

    def should_index_file(self, file_path):
        """Check if file should be indexed"""
        path = Path(file_path)

        # Skip non-Python files
        if path.suffix not in self.indexer.extensions:
            return False

        # Skip __pycache__ and venv directories
        if "__pycache__" in str(path) or "venv" in str(path):
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
                self.indexer.index_file(file_path)
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
                self.indexer.index_file(file_path)
                self.last_indexed[str(file_path)] = time.time()
                logger.info(f"Successfully indexed new file: {event.src_path}")
            except Exception as e:
                logger.error(f"Error indexing {event.src_path}: {e}")

    def on_deleted(self, event):
        """Handle file deletion events"""
        if event.is_directory:
            return

        if Path(event.src_path).suffix in self.indexer.extensions:
            logger.info(f"File deleted: {event.src_path}")
            # Remove from index
            try:
                import sqlite3

                conn = sqlite3.connect(self.indexer.db_path)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM symbols WHERE file_path = ?", (event.src_path,))
                cursor.execute("DELETE FROM file_hashes WHERE file_path = ?", (event.src_path,))
                conn.commit()
                conn.close()
                logger.info(f"Removed from index: {event.src_path}")
            except Exception as e:
                logger.error(f"Error removing {event.src_path} from index: {e}")


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

    while True:
        try:
            logger.info("Starting periodic scan...")
            changed_count = 0

            for directory in indexer.index_dirs:
                dir_path = indexer.project_root / directory
                if not dir_path.exists():
                    continue

                for file_path in dir_path.rglob("*.py"):
                    if "__pycache__" in str(file_path) or "venv" in str(file_path):
                        continue

                    if indexer.should_reindex_file(file_path):
                        indexer.index_file(file_path)
                        changed_count += 1

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

    indexer = CodeIndexer()

    # Initial full index if database is empty
    import sqlite3

    conn = sqlite3.connect(indexer.db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM symbols")
    symbol_count = cursor.fetchone()[0]
    conn.close()

    if symbol_count == 0:
        logger.info("Database is empty, performing initial index...")
        indexer.index_all()

    if HAS_WATCHDOG:
        # Use watchdog for efficient monitoring
        logger.info("Starting file watcher with watchdog...")

        event_handler = CodeIndexHandler(indexer)
        observer = Observer()

        # Watch each configured directory
        for directory in indexer.index_dirs:
            dir_path = indexer.project_root / directory
            if dir_path.exists():
                observer.schedule(event_handler, str(dir_path), recursive=True)
                logger.info(f"Watching directory: {dir_path}")

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
