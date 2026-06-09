# Campus Notifications Microservice — System Design

---

## Stage 1: REST API Design & Real-Time Notification Mechanism

### Core Actions Identified

The notification platform must support the following core actions:

1. **Retrieve notifications** — students fetch their notifications (paginated, filterable)
2. **Retrieve a single notification** — get full details of a specific notification
3. **Mark notification as read** — student marks a notification as read
4. **Mark all as read** — batch operation to clear unread state
5. **Create notification** — admin/system creates a notification for students
6. **Broadcast notification** — admin sends notification to all/group of students
7. **Delete notification** — remove a notification
8. **Get unread count** — lightweight endpoint for badge/counter display
9. **Real-time streaming** — push new notifications to connected clients

---

### REST API Endpoints

#### 1. List Notifications

```
GET /api/v1/notifications?page=1&limit=20&type=Placement&isRead=false&sortBy=createdAt&order=desc
```

**Headers:**
```json
{
  "Authorization": "Bearer <jwt_token>",
  "Content-Type": "application/json"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "notifications": [
      {
        "id": "ntf_a1b2c3d4",
        "studentId": 1642,
        "title": "TCS Placement Drive - Round 2 Results",
        "message": "You have been shortlisted for Round 2 of TCS placement drive scheduled on 15th March.",
        "notificationType": "Placement",
        "isRead": false,
        "priority": "high",
        "metadata": {
          "companyName": "TCS",
          "driveDate": "2025-03-15T10:00:00Z"
        },
        "createdAt": "2025-03-10T14:30:00Z",
        "updatedAt": "2025-03-10T14:30:00Z"
      }
    ],
    "pagination": {
      "currentPage": 1,
      "totalPages": 5,
      "totalCount": 98,
      "limit": 20,
      "hasNext": true,
      "hasPrevious": false
    }
  }
}
```

---

#### 2. Get Single Notification

```
GET /api/v1/notifications/:id
```

**Headers:**
```json
{
  "Authorization": "Bearer <jwt_token>"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "id": "ntf_a1b2c3d4",
    "studentId": 1642,
    "title": "TCS Placement Drive - Round 2 Results",
    "message": "You have been shortlisted for Round 2...",
    "notificationType": "Placement",
    "isRead": false,
    "priority": "high",
    "metadata": {
      "companyName": "TCS",
      "driveDate": "2025-03-15T10:00:00Z"
    },
    "createdAt": "2025-03-10T14:30:00Z",
    "updatedAt": "2025-03-10T14:30:00Z"
  }
}
```

**Response (404 Not Found):**
```json
{
  "success": false,
  "error": {
    "code": "NOTIFICATION_NOT_FOUND",
    "message": "Notification with id 'ntf_xyz' not found"
  }
}
```

---

#### 3. Mark Notification as Read

```
PATCH /api/v1/notifications/:id/read
```

**Headers:**
```json
{
  "Authorization": "Bearer <jwt_token>"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "id": "ntf_a1b2c3d4",
    "isRead": true,
    "readAt": "2025-03-10T15:00:00Z"
  }
}
```

---

#### 4. Mark All Notifications as Read

```
PATCH /api/v1/notifications/read-all
```

**Headers:**
```json
{
  "Authorization": "Bearer <jwt_token>"
}
```

**Request Body (optional filter):**
```json
{
  "notificationType": "Event"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "updatedCount": 15,
    "message": "15 notifications marked as read"
  }
}
```

---

#### 5. Create Notification (Admin)

```
POST /api/v1/notifications
```

**Headers:**
```json
{
  "Authorization": "Bearer <admin_jwt_token>",
  "Content-Type": "application/json"
}
```

**Request Body:**
```json
{
  "studentId": 1642,
  "title": "Semester Results Published",
  "message": "Your semester 6 results are now available on the student portal.",
  "notificationType": "Result",
  "priority": "medium",
  "metadata": {
    "semester": 6,
    "portalLink": "https://portal.university.edu/results"
  }
}
```

**Response (201 Created):**
```json
{
  "success": true,
  "data": {
    "id": "ntf_e5f6g7h8",
    "studentId": 1642,
    "title": "Semester Results Published",
    "message": "Your semester 6 results are now available...",
    "notificationType": "Result",
    "isRead": false,
    "priority": "medium",
    "createdAt": "2025-03-10T16:00:00Z"
  }
}
```

---

#### 6. Broadcast Notification (Admin — Notify All)

```
POST /api/v1/notifications/broadcast
```

**Headers:**
```json
{
  "Authorization": "Bearer <admin_jwt_token>",
  "Content-Type": "application/json"
}
```

**Request Body:**
```json
{
  "title": "Campus Placement Drive - Infosys",
  "message": "Infosys placement drive is scheduled for 20th March. All eligible students must register.",
  "notificationType": "Placement",
  "priority": "high",
  "targetGroup": "all",
  "metadata": {
    "companyName": "Infosys",
    "registrationDeadline": "2025-03-18T23:59:59Z"
  }
}
```

**Response (202 Accepted):**
```json
{
  "success": true,
  "data": {
    "broadcastId": "brd_x1y2z3",
    "status": "queued",
    "targetCount": 50000,
    "message": "Broadcast notification queued for 50000 students"
  }
}
```

---

#### 7. Delete Notification

```
DELETE /api/v1/notifications/:id
```

**Headers:**
```json
{
  "Authorization": "Bearer <jwt_token>"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "message": "Notification deleted successfully"
  }
}
```

---

#### 8. Get Unread Count

```
GET /api/v1/notifications/unread-count
```

**Headers:**
```json
{
  "Authorization": "Bearer <jwt_token>"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "unreadCount": 12,
    "byType": {
      "Placement": 3,
      "Event": 7,
      "Result": 2
    }
  }
}
```

---

### Real-Time Notification Mechanism: Server-Sent Events (SSE)

**Why SSE over WebSocket?**

| Criteria | SSE | WebSocket |
|---|---|---|
| Direction | Server → Client (unidirectional) | Bidirectional |
| Complexity | Simple HTTP, auto-reconnect | Complex handshake, manual reconnect |
| Firewall/Proxy | Works through standard HTTP | May be blocked |
| Use case fit | Perfect for push notifications | Overkill for one-way notifications |
| Scalability | Lightweight, fewer resources | Higher memory per connection |

For a notification system where the server pushes updates to the client, SSE is the ideal choice — simpler, more reliable, and natively supported by browsers with automatic reconnection.

**SSE Endpoint:**

```
GET /api/v1/notifications/stream
```

**Headers:**
```json
{
  "Authorization": "Bearer <jwt_token>",
  "Accept": "text/event-stream",
  "Cache-Control": "no-cache"
}
```

**Event Stream Format:**
```
event: notification
data: {"id":"ntf_new123","title":"New Placement Update","notificationType":"Placement","message":"You've been shortlisted...","createdAt":"2025-03-10T16:05:00Z"}

event: notification
data: {"id":"ntf_new124","title":"Annual Fest Registration","notificationType":"Event","message":"Register for the annual fest...","createdAt":"2025-03-10T16:10:00Z"}

event: heartbeat
data: {"timestamp":"2025-03-10T16:15:00Z"}
```

**Client-side usage:**
```javascript
const eventSource = new EventSource('/api/v1/notifications/stream', {
  headers: { 'Authorization': 'Bearer <token>' }
});

eventSource.addEventListener('notification', (event) => {
  const notification = JSON.parse(event.data);
  displayNotification(notification);
});

eventSource.addEventListener('heartbeat', (event) => {
  // Connection keepalive
});

eventSource.onerror = () => {
  // SSE auto-reconnects by default
};
```

---

## Stage 2: Database Design

### Database Choice: PostgreSQL

**Why PostgreSQL?**

| Factor | PostgreSQL | MongoDB | MySQL |
|---|---|---|---|
| ACID Compliance | Full | Limited (multi-doc) | Full |
| JSON Support | Excellent (JSONB) | Native | Basic (JSON column) |
| Indexing | B-tree, GIN, GiST, partial | B-tree, compound | B-tree, hash |
| Full-text Search | Built-in (tsvector) | Text indexes | Basic |
| Partitioning | Native (range, list, hash) | Sharding | Limited |
| Scalability | Read replicas, partitioning | Horizontal sharding | Read replicas |
| Notification metadata | JSONB for flexible schema | Native document | Rigid or JSON column |

PostgreSQL strikes the best balance: relational integrity for student-notification relationships, JSONB for flexible metadata, advanced indexing for performance, and native partitioning for scale.

---

### Database Schema

```sql
-- Enum for notification types
CREATE TYPE notification_type AS ENUM ('Placement', 'Event', 'Result');

-- Enum for priority levels
CREATE TYPE priority_level AS ENUM ('low', 'medium', 'high', 'critical');

-- Students table
CREATE TABLE students (
    id              SERIAL PRIMARY KEY,
    roll_no         VARCHAR(50)  UNIQUE NOT NULL,
    name            VARCHAR(255) NOT NULL,
    email           VARCHAR(255) UNIQUE NOT NULL,
    department      VARCHAR(100),
    year            SMALLINT,
    is_active       BOOLEAN DEFAULT true,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Notifications table
CREATE TABLE notifications (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id          INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    title               VARCHAR(500) NOT NULL,
    message             TEXT NOT NULL,
    notification_type   notification_type NOT NULL,
    is_read             BOOLEAN DEFAULT false,
    read_at             TIMESTAMP WITH TIME ZONE,
    priority            priority_level DEFAULT 'medium',
    metadata            JSONB DEFAULT '{}',
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Broadcast tracking table (for Stage 5 — bulk notifications)
CREATE TABLE broadcasts (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title           VARCHAR(500) NOT NULL,
    message         TEXT NOT NULL,
    notification_type notification_type NOT NULL,
    priority        priority_level DEFAULT 'medium',
    metadata        JSONB DEFAULT '{}',
    target_group    VARCHAR(100) DEFAULT 'all',
    total_targets   INTEGER NOT NULL,
    sent_count      INTEGER DEFAULT 0,
    failed_count    INTEGER DEFAULT 0,
    status          VARCHAR(50) DEFAULT 'queued',
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at    TIMESTAMP WITH TIME ZONE
);

-- ====================================================================
-- Indexes for Performance
-- ====================================================================

-- Primary query: fetch unread notifications for a student, sorted by date
CREATE INDEX idx_notifications_student_unread 
    ON notifications(student_id, is_read, created_at DESC)
    WHERE is_read = false;

-- Filter by notification type
CREATE INDEX idx_notifications_type 
    ON notifications(notification_type, created_at DESC);

-- Composite for student + type queries
CREATE INDEX idx_notifications_student_type 
    ON notifications(student_id, notification_type, created_at DESC);

-- For unread count queries
CREATE INDEX idx_notifications_unread_count 
    ON notifications(student_id, is_read)
    WHERE is_read = false;

-- JSONB index for metadata searches
CREATE INDEX idx_notifications_metadata 
    ON notifications USING GIN (metadata);

-- Student lookup
CREATE INDEX idx_students_email ON students(email);
CREATE INDEX idx_students_roll ON students(roll_no);
```

---

### Scalability Concerns & Solutions

| Problem | Impact | Solution |
|---|---|---|
| **Table bloat** | 50K students × 100+ notifications = millions of rows | **Table partitioning** by `created_at` (monthly range partitions) |
| **Slow reads** | Full table scans on large datasets | **Partial indexes** (WHERE is_read = false) to index only unread rows |
| **Write contention** | Bulk inserts during broadcasts | **Batch inserts** with `COPY` or multi-value INSERTs |
| **Read replica lag** | Stale data on replicas | **Read replicas** for list queries, primary for writes |
| **Archive overhead** | Old read notifications consuming space | **Archival strategy** — move read notifications older than 90 days to `notifications_archive` |
| **Index bloat** | Dead tuples from frequent updates (mark as read) | Regular `VACUUM` and `REINDEX` maintenance |

**Partitioning Example:**
```sql
CREATE TABLE notifications (
    -- same schema as above
) PARTITION BY RANGE (created_at);

CREATE TABLE notifications_2025_q1 PARTITION OF notifications
    FOR VALUES FROM ('2025-01-01') TO ('2025-04-01');

CREATE TABLE notifications_2025_q2 PARTITION OF notifications
    FOR VALUES FROM ('2025-04-01') TO ('2025-07-01');
```

---

### SQL Queries for REST API Endpoints

```sql
-- 1. List notifications (paginated, filtered)
SELECT id, student_id, title, message, notification_type, 
       is_read, priority, metadata, created_at
FROM notifications
WHERE student_id = $1
  AND ($2::notification_type IS NULL OR notification_type = $2)
  AND ($3::boolean IS NULL OR is_read = $3)
ORDER BY created_at DESC
LIMIT $4 OFFSET $5;

-- 2. Get single notification
SELECT * FROM notifications WHERE id = $1 AND student_id = $2;

-- 3. Mark as read
UPDATE notifications 
SET is_read = true, read_at = NOW(), updated_at = NOW()
WHERE id = $1 AND student_id = $2
RETURNING id, is_read, read_at;

-- 4. Mark all as read
UPDATE notifications
SET is_read = true, read_at = NOW(), updated_at = NOW()
WHERE student_id = $1 AND is_read = false
  AND ($2::notification_type IS NULL OR notification_type = $2);

-- 5. Create notification
INSERT INTO notifications (student_id, title, message, notification_type, priority, metadata)
VALUES ($1, $2, $3, $4, $5, $6)
RETURNING *;

-- 6. Delete notification
DELETE FROM notifications WHERE id = $1 AND student_id = $2;

-- 7. Get unread count
SELECT notification_type, COUNT(*) as count
FROM notifications
WHERE student_id = $1 AND is_read = false
GROUP BY notification_type;
```

---

## Stage 3: Query Analysis & Indexing Strategy

### Analysing the Given Query

```sql
SELECT * FROM notifications
WHERE studentID = 1642 AND isRead = false
ORDER BY createdAt DESC;
```

**Is this query accurate?**

Yes, the query is logically correct — it fetches all unread notifications for student 1642, sorted by newest first. However, it has performance issues.

**Why is it slow?**

With 50,000 students and 5,000,000 notifications, there are several reasons:

1. **Missing composite index:** Without an index on `(studentID, isRead, createdAt)`, PostgreSQL must perform a **sequential scan** of the entire 5M-row table, filtering row-by-row. This is O(N) where N = 5,000,000.

2. **`SELECT *` overhead:** Fetching all columns (including potentially large `message` and `metadata` fields) forces the database to read full row data even when some columns aren't needed. This increases I/O.

3. **No result limit:** Without `LIMIT`, the query returns ALL unread notifications. A student could have thousands, causing large result sets to be serialized and sent over the network.

4. **Sort without index support:** `ORDER BY createdAt DESC` without a matching index requires an in-memory sort (or disk sort for large results), adding O(K log K) cost where K is the number of matching rows.

**What would I change?**

```sql
-- 1. Create a partial composite index (most impactful change)
CREATE INDEX idx_student_unread_notifications
    ON notifications(studentID, createdAt DESC)
    WHERE isRead = false;
```

This index is optimal because:
- **Composite:** Covers both `WHERE studentID = X AND isRead = false` conditions
- **Partial (`WHERE isRead = false`):** Only indexes unread notifications — far smaller than indexing all 5M rows. Since most notifications are eventually read, this index is dramatically smaller.
- **Sorted (`createdAt DESC`):** The index is pre-sorted, eliminating the need for an in-memory sort.

**Computation cost with index:**
- **Without index:** Sequential scan = **O(5,000,000)** row comparisons + **O(K log K)** sort
- **With partial composite index:** Index seek = **O(log N)** + sequential read of matching rows = **O(K)** where K is the number of unread notifications for that student (typically 10-100)

This is a reduction from **millions** of operations to **tens**.

Additional improvements:
```sql
-- Improved query with specific columns and limit
SELECT id, title, message, notification_type, priority, created_at
FROM notifications
WHERE studentID = 1642 AND isRead = false
ORDER BY createdAt DESC
LIMIT 20 OFFSET 0;
```

---

### Should We Index Every Column?

**No.** Adding indexes on every column is counterproductive. Here's why:

| Issue | Explanation |
|---|---|
| **Write performance degradation** | Every INSERT, UPDATE, or DELETE must update ALL indexes. With 50K students receiving notifications, this creates massive write amplification. |
| **Storage overhead** | Each index consumes disk space. Indexing every column on a 5M-row table could double or triple storage requirements. |
| **Index maintenance cost** | PostgreSQL must VACUUM and maintain all indexes. More indexes = longer maintenance windows. |
| **Planner confusion** | Too many indexes can confuse the query planner, leading it to choose suboptimal indexes. |
| **Low-cardinality columns** | Columns like `isRead` (boolean, only 2 values) are poor standalone index candidates — they don't reduce the search space meaningfully. |

**Best practice:** Only create indexes that directly support frequent query patterns. In our case:
- `(studentID, isRead, createdAt DESC)` — primary query pattern
- `(notification_type, createdAt)` — for type filtering
- Partial indexes where applicable

---

### 7-Day Placement Notification Query

```sql
SELECT s.id, s.name, s.email, s.roll_no, 
       n.id AS notification_id, n.title, n.message, n.created_at
FROM students s
INNER JOIN notifications n ON s.id = n.student_id
WHERE n.notification_type = 'Placement'
  AND n.created_at >= NOW() - INTERVAL '7 days'
ORDER BY n.created_at DESC;
```

Supporting index:
```sql
CREATE INDEX idx_notifications_placement_recent
    ON notifications(notification_type, created_at DESC)
    WHERE notification_type = 'Placement';
```

---

## Stage 4: Caching & Performance Optimisation

### Problem
Notifications are fetched on every page load for every student. With 50,000 students, even if each student loads the page once, that's 50K database queries. During peak hours (placement season), this could be much higher.

### Solution 1: Redis Caching Layer (Recommended)

**Architecture:**
```
Client → API Server → Redis Cache (check first) → PostgreSQL (fallback)
```

**What to cache:**
- **Unread notification list** per student: Key = `notifications:unread:{studentId}`
- **Unread count** per student: Key = `notifications:count:{studentId}`
- **TTL:** 5 minutes (balance between freshness and DB load)

**Cache Strategy: Cache-Aside (Lazy Loading)**

```python
def get_unread_notifications(student_id):
    cache_key = f"notifications:unread:{student_id}"
    
    # 1. Check cache first
    cached = redis.get(cache_key)
    if cached:
        return json.loads(cached)
    
    # 2. Cache miss — query DB
    notifications = db.query(
        "SELECT ... FROM notifications WHERE student_id = %s AND is_read = false "
        "ORDER BY created_at DESC LIMIT 20", student_id
    )
    
    # 3. Populate cache
    redis.setex(cache_key, 300, json.dumps(notifications))  # 5 min TTL
    
    return notifications
```

**Cache Invalidation:** Invalidate when:
- New notification is created for the student → `redis.delete(cache_key)`
- Student marks a notification as read → `redis.delete(cache_key)`
- Bulk broadcast → invalidate all student caches (or rely on TTL)

**Trade-offs:**

| Pro | Con |
|---|---|
| Reduces DB load by 80-90% | Additional infrastructure (Redis) |
| Sub-millisecond read latency | Potential stale data (up to TTL duration) |
| Handles traffic spikes gracefully | Cache invalidation complexity |
| Horizontal scaling with Redis Cluster | Memory cost for 50K students' data |

---

### Solution 2: Pagination (Must-Have)

Never return all notifications. Always paginate:

```sql
SELECT ... FROM notifications
WHERE student_id = $1 AND is_read = false
ORDER BY created_at DESC
LIMIT 20 OFFSET 0;
```

**Trade-offs:**

| Pro | Con |
|---|---|
| Predictable response size | Requires client-side "load more" UX |
| Reduces network bandwidth | OFFSET-based pagination gets slow on deep pages |
| Lower memory usage on API server | — |

**Improvement:** Use **cursor-based pagination** instead of OFFSET for deep pages:
```sql
WHERE created_at < $cursor_timestamp
ORDER BY created_at DESC LIMIT 20
```

---

### Solution 3: HTTP Caching Headers

```
Cache-Control: private, max-age=60
ETag: "abc123"
```

The browser/CDN can serve cached responses for 60 seconds, reducing server hits.

**Trade-offs:**

| Pro | Con |
|---|---|
| Zero cost — uses existing HTTP infrastructure | Limited control over invalidation |
| Reduces API server load | Only useful for unchanged data |

---

### Solution 4: Denormalised Unread Count

Store `unread_count` directly on the `students` table, updated via triggers or application logic. The badge/counter endpoint becomes a single-row lookup.

```sql
ALTER TABLE students ADD COLUMN unread_count INTEGER DEFAULT 0;
```

**Trade-offs:**

| Pro | Con |
|---|---|
| O(1) count lookups | Data consistency risk (count drift) |
| No COUNT() aggregation needed | Additional write on every notification event |

---

### Recommended Approach

Combine **Redis caching** + **cursor-based pagination** + **HTTP cache headers** for maximum performance. This stack handles 50K+ concurrent users while maintaining reasonable data freshness.

---

## Stage 5: Reliable Bulk Notifications

### Problems with the Current Implementation

```python
function notify_all(student_ids: array, message: string):
    for student_id in student_ids:
        send_email(student_id, message)       # calls Email API
        save_to_db(student_id, message)        # DB insert
        push_to_app(student_id, message)       # real-time push
```

| # | Problem | Impact |
|---|---|---|
| 1 | **Sequential processing** | Processing 50K students one-by-one takes hours. If each iteration takes 100ms (email API + DB + push), total = 50,000 × 0.1s = **83 minutes**. |
| 2 | **No error handling / retry** | If `send_email` fails for student #25,001, there's no retry. 200 students missed emails permanently. |
| 3 | **Tight coupling** | Email, DB, and push are in the same synchronous loop. A slow email API blocks DB writes and push notifications. |
| 4 | **No idempotency** | If the process crashes at student #30,000 and restarts, students #1-29,999 get duplicate notifications. |
| 5 | **Single point of failure** | One server handles everything. If it crashes, the entire broadcast fails midway. |
| 6 | **No progress tracking** | No way to know how many students have been notified or where a failure occurred. |
| 7 | **DB overload** | 50K individual INSERTs create significant transaction overhead. |

---

### Handling the 200 Failed Emails

When `send_email` fails for 200 students:

1. **Identify failures:** The failed student IDs should have been logged/captured (they weren't in the current code — a major gap).
2. **Dead-letter queue:** Move failed messages to a retry queue.
3. **Exponential backoff retry:** Retry failed emails with increasing delays (1s, 2s, 4s, 8s...) up to a max retry count.
4. **Alert administrators:** After max retries, notify the admin team with the list of failed student IDs.
5. **Manual retry endpoint:** Provide an API for admins to trigger re-sends for specific students.

---

### Should DB Save and Email Happen Together?

**No.** They should be decoupled. Here's why:

| Together (synchronous) | Separate (asynchronous) |
|---|---|
| If email fails, DB write is blocked or rolled back | DB write succeeds independently — notification record exists even if email is delayed |
| Slow email API blocks the entire pipeline | DB writes complete in milliseconds, email processed async |
| All-or-nothing failure model | Partial success is acceptable — student sees in-app notification even if email is delayed |
| Cannot retry email independently | Email retries don't affect DB state |

**The in-app notification (DB save) is the primary delivery channel.** Email is a supplementary channel. They should succeed or fail independently.

---

### Redesigned Architecture

```
HR clicks "Notify All"
         │
         ▼
┌─────────────────────┐
│   API Server         │
│   POST /broadcast    │
│                     │
│  1. Validate request │
│  2. Create broadcast │
│     record in DB     │
│  3. Publish to       │
│     Message Queue    │
│  4. Return 202       │
│     Accepted         │
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│   Message Queue      │
│   (RabbitMQ/Kafka)   │
│                     │
│  Topic: broadcast    │
│  Partitioned by      │
│  student_id range    │
└────────┬────────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌────────┐ ┌────────┐
│Worker 1│ │Worker N│    ← Horizontal scaling
│        │ │        │
│ Batch  │ │ Batch  │
│ DB INS │ │ DB INS │    ← Batch of 500-1000
│        │ │        │
│ Email  │ │ Email  │    ← Async, separate queue
│ Queue  │ │ Queue  │
│        │ │        │
│ SSE    │ │ SSE    │    ← Push via SSE/Redis pub-sub
│ Push   │ │ Push   │
└────────┘ └────────┘
```

### Revised Pseudocode

```python
# ================================================================
# API Layer — receives the broadcast request
# ================================================================
async def notify_all(message: str, notification_type: str):
    """Handle the 'Notify All' request from HR."""
    
    # 1. Create broadcast record for tracking
    broadcast = db.insert("broadcasts", {
        "title": message,
        "notification_type": notification_type,
        "status": "queued",
        "total_targets": db.count("students", {"is_active": True}),
    })
    
    # 2. Fetch all active student IDs
    student_ids = db.query("SELECT id FROM students WHERE is_active = true")
    
    # 3. Chunk students into batches of 500
    batches = chunk_list(student_ids, batch_size=500)
    
    # 4. Publish each batch to the message queue
    for batch in batches:
        message_queue.publish("broadcast_notifications", {
            "broadcast_id": broadcast.id,
            "student_ids": batch,
            "message": message,
            "notification_type": notification_type,
        })
    
    # 5. Return immediately — processing happens async
    return {"broadcast_id": broadcast.id, "status": "queued", "target_count": len(student_ids)}


# ================================================================
# Worker — consumes batches from the queue
# ================================================================
async def process_notification_batch(payload: dict):
    """Process a batch of notifications (runs in worker process)."""
    
    broadcast_id = payload["broadcast_id"]
    student_ids = payload["student_ids"]
    message = payload["message"]
    notification_type = payload["notification_type"]
    
    # 1. BATCH DB INSERT — all at once, not one-by-one
    notification_records = [
        {
            "student_id": sid,
            "message": message,
            "notification_type": notification_type,
            "is_read": False,
        }
        for sid in student_ids
    ]
    db.batch_insert("notifications", notification_records)  # Single multi-row INSERT
    
    # 2. Update broadcast progress
    db.update("broadcasts", broadcast_id, {
        "sent_count": db.raw("sent_count + %s", len(student_ids)),
    })
    
    # 3. Push real-time notifications via Redis pub/sub → SSE
    for sid in student_ids:
        redis.publish(f"notifications:{sid}", json.dumps({
            "type": "new_notification",
            "message": message,
        }))
    
    # 4. Queue emails SEPARATELY (different queue, different retry policy)
    for sid in student_ids:
        email_queue.publish("send_email", {
            "student_id": sid,
            "message": message,
            "broadcast_id": broadcast_id,
            "retry_count": 0,
            "max_retries": 3,
        })


# ================================================================
# Email Worker — separate process with retry logic
# ================================================================
async def process_email(payload: dict):
    """Send a single email with retry and dead-letter handling."""
    
    student_id = payload["student_id"]
    retry_count = payload["retry_count"]
    max_retries = payload["max_retries"]
    
    try:
        student = db.query("SELECT email, name FROM students WHERE id = %s", student_id)
        email_service.send(
            to=student.email,
            subject=f"Campus Notification",
            body=payload["message"],
        )
    except EmailServiceError as e:
        if retry_count < max_retries:
            # Exponential backoff retry
            delay = 2 ** retry_count  # 1s, 2s, 4s
            email_queue.publish("send_email", {
                **payload,
                "retry_count": retry_count + 1,
            }, delay_seconds=delay)
        else:
            # Max retries exceeded — move to dead-letter queue
            dead_letter_queue.publish("failed_emails", {
                "student_id": student_id,
                "error": str(e),
                "broadcast_id": payload["broadcast_id"],
            })
            db.update("broadcasts", payload["broadcast_id"], {
                "failed_count": db.raw("failed_count + 1"),
            })
```

### Key Improvements

| Aspect | Before | After |
|---|---|---|
| **Throughput** | 50K sequential (83 min) | 50K in batches across N workers (< 1 min) |
| **Email failures** | Silent loss | Retry with exponential backoff + dead-letter queue |
| **DB writes** | 50K individual INSERTs | Batch INSERTs of 500 (100× fewer transactions) |
| **Coupling** | Synchronous email + DB + push | Decoupled via message queues |
| **Idempotency** | None | Broadcast ID + student ID = unique, deduplicatable |
| **Progress tracking** | None | Broadcast record with sent/failed counts |
| **Scalability** | Single server | Horizontal workers + message queue partitioning |

---

## Stage 6: Priority Inbox

### Approach

**Priority Formula:**

```
priority_score = type_weight × recency_score
```

Where:
- `type_weight`: `Placement = 3`, `Result = 2`, `Event = 1`
- `recency_score`: `1 / (1 + hours_since_creation)` — newer notifications score higher

This formula ensures:
- Placement notifications always rank higher than events of the same age
- Very recent events can outrank older placement notifications (balanced trade-off)

### Algorithm: Min-Heap of Size N

To efficiently maintain the top-N most important unread notifications:

1. **Initial load:** Iterate through all notifications, maintaining a min-heap of size N.
   - For each notification, compute `priority_score`
   - If heap size < N: push to heap
   - If `priority_score > heap[0]` (minimum in heap): replace and heapify
   - **Time complexity:** O(M log N) where M = total notifications, N = inbox size

2. **New notification arrives:**
   - Compute its `priority_score`
   - If `priority_score > heap[0]`: replace min element and heapify — **O(log N)**
   - Otherwise: discard (it's not top-N)

3. **Final result:** Extract all N elements from heap and sort — **O(N log N)**

This approach is optimal because:
- We never need to sort the entire notification list
- Memory usage is O(N) — only top-N items in memory
- Insertion of new notifications is O(log N)
- Works as a streaming algorithm — handles continuously arriving notifications

### Code

The implementation is in `notification_app_be/main.py`. It:
1. Fetches notifications from the evaluation server API
2. Computes priority scores using the formula above
3. Uses Python's `heapq` module (min-heap) to find the top 10
4. Exposes the results via a FastAPI endpoint
