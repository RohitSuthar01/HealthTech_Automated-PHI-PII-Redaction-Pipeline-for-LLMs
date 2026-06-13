# Redis Token Vault — Implementation Guide

**Project:** HealthTech Automated PHI/PII Redaction Pipeline for LLMs  
**Module:** `vault/`  
**Owner:** Jash  
**Document Version:** 1.0

---

## 1. Why Redis?

When the pipeline detects PHI like `"John Smith"`, it must store a reversible mapping (`John Smith` → `PATIENT_001`) somewhere accessible for the duration of the AI session. We evaluated three options:

| Option | Speed | TTL / Auto-Expiry | Persistence Control | Production Readiness | Verdict |
|--------|-------|-------------------|---------------------|---------------------|---------|
| **Python `dict`** | Fast (in-memory) | Manual cleanup only | Lost on process restart | Not suitable for multi-worker APIs | ❌ Dev only |
| **SQL database (PostgreSQL)** | Slower (disk I/O) | Manual cleanup | Persistent by default — PHI linger risk | Overkill for ephemeral session data | ❌ Wrong tool |
| **Redis** | Very fast (in-memory) | Built-in TTL (`EX`/`EXPIRE`) | Configurable persistence; can disable for vault use | Battle-tested, used in healthcare-adjacent systems | ✅ **Selected** |

### Why Redis Wins for This Use Case

1. **Speed** — In-memory lookups in sub-millisecond range; no disk I/O on every token store/retrieve during a live AI request.
2. **TTL expiry** — Keys automatically delete themselves after a session timeout. No cron jobs, no manual cleanup, no forgotten PHI.
3. **Simplicity** — Key-value model maps directly to our `{session_id}:{entity_type}:{token}` → `original_value` design.
4. **Production-ready** — Connection pooling, password auth, TLS, clustering, and monitoring are first-class features.
5. **Session isolation** — Each session's keys are namespaced by UUID; one session cannot read another's mappings.

---

## 2. How Redis Is Used in This Project

### The Token Vault Concept

Instead of sending real patient data to an external AI, the pipeline:

1. Detects PHI in the clinical note.
2. Assigns a pseudonym token (e.g., `PATIENT_001`).
3. **Stores the mapping in Redis** so it can be reversed later.
4. Sends only the pseudonymized text to the AI.
5. When the AI responds, **looks up each token in Redis** and swaps it back to the real value.

### Before / After Example

**Original note (never leaves the organization as-is):**

```
Patient John Smith, DOB: 12/03/1990, Phone: 9876543210
```

**What Redis stores (internal only):**

```
session_abc:PERSON:PATIENT_001  →  "John Smith"
session_abc:DATE:DATE_001       →  "12/03/1990"
session_abc:PHONE:PHONE_001     →  "9876543210"
```

**What the external AI receives:**

```
Patient PATIENT_001, DOB: DATE_001, Phone: PHONE_001
```

**What the doctor receives after reverse mapping:**

```
Patient John Smith, DOB: 12/03/1990, Phone: 9876543210
```

---

## 3. Data Structure Design

### Key Format

```
{session_id}:{entity_type}:{token}
```

| Component | Description | Example |
|-----------|-------------|---------|
| `session_id` | UUID v4 generated per API request | `f47ac10b-58cc-4372-a567-0e02b2c3d479` |
| `entity_type` | Category of PHI | `PERSON`, `PHONE`, `DATE`, `EMAIL`, `MRN` |
| `token` | Pseudonym assigned to this entity | `PATIENT_001`, `PHONE_001` |

### Value

The **original PHI value** as a plain string:

```
"f47ac10b-58cc-4372-a567-0e02b2c3d479:PERSON:PATIENT_001"  →  "John Smith"
```

### Reverse Lookup Index (Optional)

For faster reverse mapping, a secondary key can store token → original:

```
{session_id}:reverse:{token}  →  "John Smith"
```

### TTL (Time To Live)

Every key is created with an expiry:

| Setting | Default | Purpose |
|---------|---------|---------|
| Session TTL | 1800 seconds (30 min) | Matches typical clinical AI interaction duration |
| Configurable via | `VAULT_TTL_SECONDS` env var | Adjust per deployment policy |

**Why TTL is mandatory:** PHI mappings must not persist beyond the session. If a doctor closes their browser or a request fails mid-flight, Redis automatically purges the data — no orphaned PHI in memory.

### Example Redis Commands

```bash
# Store a patient name mapping (expires in 30 minutes)
SET "f47ac10b-58cc-4372-a567-0e02b2c3d479:PERSON:PATIENT_001" "John Smith" EX 1800

# Store a phone number mapping
SET "f47ac10b-58cc-4372-a567-0e02b2c3d479:PHONE:PHONE_001" "9876543210" EX 1800

# Retrieve original value from token (forward lookup)
GET "f47ac10b-58cc-4372-a567-0e02b2c3d479:PERSON:PATIENT_001"
# Returns: "John Smith"

# Check remaining TTL
TTL "f47ac10b-58cc-4372-a567-0e02b2c3d479:PERSON:PATIENT_001"
# Returns: 1742 (seconds remaining)

# List all keys for a session (admin/debug only — never in production logs)
KEYS "f47ac10b-58cc-4372-a567-0e02b2c3d479:*"

# Manually purge an entire session
DEL "f47ac10b-58cc-4372-a567-0e02b2c3d479:PERSON:PATIENT_001" \
    "f47ac10b-58cc-4372-a567-0e02b2c3d479:PHONE:PHONE_001" \
    "f47ac10b-58cc-4372-a567-0e02b2c3d479:DATE:DATE_001"
```

### Data Layout Diagram

```
Redis Instance (DB 0)
│
├── f47ac10b-58cc-4372-a567-0e02b2c3d479:PERSON:PATIENT_001  = "John Smith"     [TTL: 1800s]
├── f47ac10b-58cc-4372-a567-0e02b2c3d479:DATE:DATE_001       = "12/03/1990"     [TTL: 1800s]
├── f47ac10b-58cc-4372-a567-0e02b2c3d479:PHONE:PHONE_001     = "9876543210"    [TTL: 1800s]
│
├── b2c3d479-f47a-4372-a567-0e02b2c3d480:PERSON:PATIENT_001  = "Sarah Johnson"  [TTL: 1800s]
└── b2c3d479-f47a-4372-a567-0e02b2c3d480:PERSON:DOCTOR_001  = "Dr. Adams"      [TTL: 1800s]
```

Each session is fully isolated by its UUID prefix.

---

## 4. Code Examples

### Connecting to Redis

The project uses a connection pool via `vault/redis_client.py`:

```python
import os
import redis

class RedisClient:
    def __init__(
        self,
        host: str = None,
        port: int = 6379,
        db: int = 0,
        password: str = None,
    ):
        self.host = host or os.getenv("REDIS_HOST", "localhost")
        self.port = port
        self.password = password or os.getenv("REDIS_PASSWORD")
        self.pool = redis.ConnectionPool(
            host=self.host,
            port=self.port,
            db=db,
            password=self.password,
            decode_responses=True,  # Return strings, not bytes
        )
        self.client = redis.Redis(connection_pool=self.pool)

    def ping(self) -> bool:
        try:
            return self.client.ping()
        except redis.ConnectionError:
            return False
```

### Storing a Token Mapping

```python
import uuid

SESSION_TTL = 1800  # 30 minutes

def store_mapping(
    redis_client: redis.Redis,
    session_id: str,
    entity_type: str,
    token: str,
    original_value: str,
) -> None:
    key = f"{session_id}:{entity_type}:{token}"
    redis_client.set(key, original_value, ex=SESSION_TTL)
```

### Retrieving Original Value from Token

```python
def get_original_value(
    redis_client: redis.Redis,
    session_id: str,
    entity_type: str,
    token: str,
) -> str | None:
    key = f"{session_id}:{entity_type}:{token}"
    return redis_client.get(key)
```

### Setting / Refreshing TTL

```python
def refresh_session_ttl(
    redis_client: redis.Redis,
    session_id: str,
    ttl: int = 1800,
) -> int:
    """Extend TTL on all keys belonging to a session."""
    pattern = f"{session_id}:*"
    keys = redis_client.keys(pattern)
    if not keys:
        return 0
    pipe = redis_client.pipeline()
    for key in keys:
        pipe.expire(key, ttl)
    pipe.execute()
    return len(keys)
```

### Clearing Session Data

```python
def clear_session(
    redis_client: redis.Redis,
    session_id: str,
) -> int:
    """Delete all vault keys for a session. Returns count of keys removed."""
    pattern = f"{session_id}:*"
    keys = redis_client.keys(pattern)
    if keys:
        return redis_client.delete(*keys)
    return 0
```

### Complete Vault Usage in the Pipeline

```python
session_id = str(uuid.uuid4())
redis_client = RedisClient().get_client()

# Store mappings after detection
store_mapping(redis_client, session_id, "PERSON", "PATIENT_001", "John Smith")
store_mapping(redis_client, session_id, "DATE",   "DATE_001",    "12/03/1990")
store_mapping(redis_client, session_id, "PHONE",  "PHONE_001",   "9876543210")

# ... send pseudonymized text to AI, receive response ...

# Reverse mapping
ai_response = "PATIENT_001 should follow up on DATE_001."
restored = ai_response.replace(
    "PATIENT_001",
    get_original_value(redis_client, session_id, "PERSON", "PATIENT_001"),
)
restored = restored.replace(
    "DATE_001",
    get_original_value(redis_client, session_id, "DATE", "DATE_001"),
)

# Cleanup (optional — TTL handles this automatically)
clear_session(redis_client, session_id)
```

---

## 5. Security Considerations

### 5.1 Why TTL Is Critical for PHI Data

| Without TTL | With TTL |
|-------------|----------|
| Mappings persist indefinitely in Redis memory | Keys auto-delete after session timeout |
| Process crash leaves orphaned PHI | Expired keys are garbage-collected by Redis |
| Compliance violation (unnecessary retention) | Aligns with HIPAA minimum-necessary principle |
| Manual cleanup required (error-prone) | Zero-maintenance automatic purge |

**Policy:** Every vault key **must** be created with an `EX` (seconds) or `EXPIRE` command. Keys without TTL should trigger a monitoring alert.

### 5.2 Never Log Redis Values

Audit logs and application logs must **never** contain:

- Original PHI values stored as Redis values
- Full Redis keys that include session IDs linked to identifiable patients
- AI request/response bodies

**Safe to log:**

```python
logger.info("Vault store", extra={
    "session_id": session_id,
    "entity_type": "PERSON",
    "token": "PATIENT_001",
    # original_value intentionally omitted
})
```

### 5.3 Production Redis Configuration

```bash
# redis.conf (production)

# Require authentication
requirepass ${REDIS_PASSWORD}

# Bind to private network interface only
bind 10.0.0.5

# Disable persistence for vault data (optional — mappings are ephemeral)
save ""
appendonly no

# Memory limit with eviction
maxmemory 256mb
maxmemory-policy allkeys-lru

# Rename dangerous commands
rename-command FLUSHALL ""
rename-command FLUSHDB  ""
rename-command KEYS       ""
```

**Environment variables (`.env` — never commit to git):**

```bash
REDIS_HOST=10.0.0.5
REDIS_PORT=6379
REDIS_PASSWORD=<strong-random-password>
REDIS_TLS=true
VAULT_TTL_SECONDS=1800
```

**Python connection with password:**

```python
redis_client = RedisClient(
    host=os.getenv("REDIS_HOST"),
    password=os.getenv("REDIS_PASSWORD"),
)
```

### 5.4 Additional Hardening

| Control | Recommendation |
|---------|---------------|
| Network | Redis accessible only from the API proxy server (private VPC / firewall) |
| Encryption in transit | Use `rediss://` (TLS) in production |
| Encryption at rest | Enable Redis ACLs + disk encryption on the host |
| Access control | Separate Redis DB index (`db=1`) dedicated to the vault |
| Monitoring | Alert on keys without TTL, memory usage spikes, auth failures |

---

## 6. Local Setup Instructions

### macOS (Homebrew)

```bash
# Install Redis
brew install redis

# Start Redis as a background service
brew services start redis

# Verify
redis-cli ping
# Expected: PONG

# Connect to Redis CLI
redis-cli

# Stop Redis
brew services stop redis
```

### Windows (WSL)

```bash
# Open WSL terminal (Ubuntu)
sudo apt update
sudo apt install redis-server -y

# Start Redis
sudo service redis-server start

# Verify
redis-cli ping
# Expected: PONG

# Stop Redis
sudo service redis-server stop
```

### Docker (All Platforms — Recommended)

```bash
# Start Redis in a container
docker run -d \
  --name phi-vault \
  -p 6379:6379 \
  redis:7-alpine

# Verify
docker exec -it phi-vault redis-cli ping
# Expected: PONG

# Stop and remove
docker stop phi-vault && docker rm phi-vault
```

### Verify Python Connection

```bash
# From project root with venv activated
python -c "
from vault.redis_client import RedisClient
client = RedisClient()
print('Connected:', client.ping())
"
```

---

## 7. Testing Without a Live Redis Instance

The project uses `fakeredis` for unit tests — no running Redis server required:

```python
import fakeredis

def test_store_and_retrieve():
    fake_redis = fakeredis.FakeRedis(decode_responses=True)
    store_mapping(fake_redis, "test-session", "PERSON", "PATIENT_001", "John Smith")
    result = get_original_value(fake_redis, "test-session", "PERSON", "PATIENT_001")
    assert result == "John Smith"
```

Run vault tests:

```bash
pytest tests/test_vault.py -v
```

---

## Related Documentation

| Document | Description |
|----------|-------------|
| [architecture.md](./architecture.md) | Full system architecture and data flow |
| [token_mapping.md](./token_mapping.md) | Pseudonymization and reverse mapping logic |

---

<p align="center"><em>Document maintained by Jash — Infotact Solutions HealthTech Intern Team</em></p>
