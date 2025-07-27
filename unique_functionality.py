import datetime
import hashlib


def generate_unique_timestamp():
    """Generate a unique timestamp with microseconds."""
    now = datetime.datetime.now()
    return now.strftime("%Y%m%d_%H%M%S_%f")


def create_hash_fingerprint(text, algorithm="sha256"):
    """Create a cryptographic hash fingerprint of text."""
    if algorithm == "sha256":
        return hashlib.sha256(text.encode()).hexdigest()
    elif algorithm == "md5":
        return hashlib.md5(text.encode()).hexdigest()
    else:
        raise ValueError(f"Unsupported algorithm: {algorithm}")


class SessionManager:
    """Manage user sessions with unique identifiers."""

    def __init__(self):
        self.sessions = {}

    def create_session(self, user_id):
        """Create a new session for a user."""
        session_id = generate_unique_timestamp()
        self.sessions[session_id] = {
            "user_id": user_id,
            "created_at": datetime.datetime.now(),
            "last_accessed": datetime.datetime.now(),
        }
        return session_id
