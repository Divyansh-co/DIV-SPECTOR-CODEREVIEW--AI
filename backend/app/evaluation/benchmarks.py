from typing import List
from app.models.schemas import BenchmarkCase, SeverityEnum, CategoryEnum

BENCHMARK_CASES: List[BenchmarkCase] = [
    BenchmarkCase(
        case_id="bench_01_sqli",
        title="SQL Injection in User Authentication Query",
        description="Raw string formatting concatenating unescaped user input into an SQL SELECT query.",
        language="python",
        category=CategoryEnum.SECURITY,
        expected_defect_line=7,
        expected_severity=SeverityEnum.CRITICAL,
        code_snippet="""import sqlite3

def authenticate(username, password):
    conn = sqlite3.connect("app.db")
    cursor = conn.cursor()
    # Flaw: String formatting vulnerable to SQL injection
    query = f"SELECT id, role FROM users WHERE username = '{username}' AND password = '{password}'"
    cursor.execute(query)
    user = cursor.fetchone()
    conn.close()
    return user
""",
        ground_truth_explanation="Direct f-string formatting in SQL query allows attackers to inject malicious SQL commands (e.g. `' OR '1'='1`). Parameterized queries with `?` or `%s` must be used."
    ),
    BenchmarkCase(
        case_id="bench_02_off_by_one",
        title="Off-By-One Array Boundary IndexError",
        description="Loop boundary runs up to `len(items) + 1`, triggering an index out-of-bounds exception.",
        language="python",
        category=CategoryEnum.BUG,
        expected_defect_line=6,
        expected_severity=SeverityEnum.CRITICAL,
        code_snippet="""def calculate_moving_averages(data_points):
    averages = []
    total_elements = len(data_points)
    
    # Flaw: range goes to total_elements + 1, causing IndexError on data_points[i]
    for i in range(total_elements + 1):
        window = data_points[max(0, i - 3):i + 1]
        averages.append(sum(window) / len(window))
        
    return averages
""",
        ground_truth_explanation="The range `range(total_elements + 1)` attempts to access index `total_elements`, which exceeds the zero-indexed list bounds and raises IndexError."
    ),
    BenchmarkCase(
        case_id="bench_03_null_deref",
        title="Unchecked Null / NoneType Attribute Access",
        description="Accessing nested dictionary property without null-check when `.get()` can return None.",
        language="python",
        category=CategoryEnum.BUG,
        expected_defect_line=6,
        expected_severity=SeverityEnum.WARNING,
        code_snippet="""def get_user_contact_email(user_records, user_id):
    record = user_records.get(user_id)
    
    # Flaw: record can be None if user_id is missing, causing AttributeError
    profile = record.get("profile")
    email = profile["contact"]["email"]
    return email.lower()
""",
        ground_truth_explanation="If `user_id` does not exist in `user_records`, `record` is None, and `record.get('profile')` raises AttributeError: 'NoneType' object has no attribute 'get'."
    ),
    BenchmarkCase(
        case_id="bench_04_unhandled_promise",
        title="Unhandled Async Promise Rejection in Fetch",
        description="Missing catch block or error handling in asynchronous network call.",
        language="javascript",
        category=CategoryEnum.BUG,
        expected_defect_line=4,
        expected_severity=SeverityEnum.WARNING,
        code_snippet="""export function syncUserProfile(userId, payload) {
    // Flaw: No .catch() handler on Promise or try/catch around async call
    return fetch(`/api/users/${userId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    })
    .then(response => response.json())
    .then(data => data.status);
}
""",
        ground_truth_explanation="Network errors or non-200 responses result in unhandled promise rejections, crashing the caller context or failing silently."
    ),
    BenchmarkCase(
        case_id="bench_05_hardcoded_secret",
        title="Hardcoded Production API Secret Token",
        description="Secret private key embedded directly in source code.",
        language="python",
        category=CategoryEnum.SECURITY,
        expected_defect_line=4,
        expected_severity=SeverityEnum.CRITICAL,
        code_snippet="""import os
import requests

# Flaw: Hardcoded production secret token in source control
PAYMENT_GATEWAY_SECRET = "MOCK_LIVE_API_KEY_SECRET_UNENCRYPTED_SAMPLE_98234"

def process_charge(amount_cents, customer_id):
    headers = {"Authorization": f"Bearer {PAYMENT_GATEWAY_SECRET}"}
    return requests.post("https://api.stripe.com/v1/charges", headers=headers, json={"amount": amount_cents})
""",
        ground_truth_explanation="Embedding sensitive credentials in code exposes keys to unauthorized commit access. Use environment variables (e.g. `os.environ.get(...)`)."
    ),
    BenchmarkCase(
        case_id="bench_06_insecure_deserialization",
        title="Insecure Deserialization via pickle.loads",
        description="Deserializing untrusted user input using pickle can lead to arbitrary code execution.",
        language="python",
        category=CategoryEnum.SECURITY,
        expected_defect_line=6,
        expected_severity=SeverityEnum.CRITICAL,
        code_snippet="""import pickle
import base64

def restore_session(raw_cookie_payload):
    decoded_bytes = base64.b64decode(raw_cookie_payload)
    # Flaw: Insecure deserialization of untrusted payload allows RCE
    session_obj = pickle.loads(decoded_bytes)
    return session_obj
""",
        ground_truth_explanation="`pickle.loads()` is inherently unsafe on untrusted input because custom `__reduce__` methods can execute arbitrary OS commands upon unpickling."
    ),
    BenchmarkCase(
        case_id="bench_07_resource_leak",
        title="Unclosed Database Connection and File Handle Leak",
        description="Opening system resources without context manager (`with`) leading to descriptor exhaustion.",
        language="python",
        category=CategoryEnum.PERFORMANCE,
        expected_defect_line=4,
        expected_severity=SeverityEnum.WARNING,
        code_snippet="""def export_audit_log(events, target_filename):
    # Flaw: file handle is not closed if an exception is raised or forgotten
    f = open(target_filename, "a")
    for event in events:
        if event.get("sensitive"):
            continue
        f.write(f"{event['timestamp']}: {event['message']}\\n")
    # Missing f.close() in try/finally or with open(...)
""",
        ground_truth_explanation="Unclosed file handles or database connections can exhaust operating system file descriptors under high concurrency. Use `with open(...)`."
    ),
    BenchmarkCase(
        case_id="bench_08_path_traversal",
        title="Arbitrary File Read via Path Traversal",
        description="Joining unvalidated user input into filesystem path allows directory traversal (`../`).",
        language="python",
        category=CategoryEnum.SECURITY,
        expected_defect_line=7,
        expected_severity=SeverityEnum.CRITICAL,
        code_snippet="""import os

BASE_MEDIA_DIR = "/var/www/uploads"

def serve_user_file(requested_filename):
    # Flaw: Path traversal vulnerability via ../
    target_path = os.path.join(BASE_MEDIA_DIR, requested_filename)
    with open(target_path, "rb") as f:
        return f.read()
""",
        ground_truth_explanation="`os.path.join` does not prevent path traversal if `requested_filename` contains `../../etc/passwd`. Path must be resolved and checked against `BASE_MEDIA_DIR`."
    ),
    BenchmarkCase(
        case_id="bench_09_prototype_pollution",
        title="Prototype Pollution in Object Merge",
        description="Recursive merge without filtering `__proto__` or `constructor` properties.",
        language="javascript",
        category=CategoryEnum.SECURITY,
        expected_defect_line=6,
        expected_severity=SeverityEnum.CRITICAL,
        code_snippet="""function mergeDeep(target, source) {
    for (let key in source) {
        if (source.hasOwnProperty(key)) {
            // Flaw: Prototype pollution if key is __proto__ or constructor
            if (typeof source[key] === 'object' && source[key] !== null) {
                target[key] = mergeDeep(target[key] || {}, source[key]);
            } else {
                target[key] = source[key];
            }
        }
    }
    return target;
}
""",
        ground_truth_explanation="Manipulating the prototype object via `__proto__` can pollute global object prototypes across the JavaScript runtime, leading to privilege escalation or DoS."
    ),
    BenchmarkCase(
        case_id="bench_10_missing_error_handling",
        title="Silent Failure / Bare Except Clause",
        description="Suppressing all exceptions without logging or re-raising masks critical errors.",
        language="python",
        category=CategoryEnum.MAINTAINABILITY,
        expected_defect_line=6,
        expected_severity=SeverityEnum.WARNING,
        code_snippet="""def process_payment_notification(payload):
    try:
        order_id = payload["order_id"]
        update_inventory(order_id)
        dispatch_webhook(order_id)
    except:
        # Flaw: Bare except silently eats KeyboardInterrupt, SystemExit, and Database errors
        pass
""",
        ground_truth_explanation="A bare `except:` masks programming errors and critical system signals. Always catch specific exceptions and log the error context."
    ),
    BenchmarkCase(
        case_id="bench_11_redos",
        title="Catastrophic Backtracking ReDoS Vulnerability",
        description="Nested quantifiers in regular expression allow exponential runtime on malicious inputs.",
        language="javascript",
        category=CategoryEnum.PERFORMANCE,
        expected_defect_line=3,
        expected_severity=SeverityEnum.WARNING,
        code_snippet="""export function validateEmailRegex(inputString) {
    // Flaw: Catastrophic backtracking in regex (a+)+
    const badRegex = /^([a-zA-Z0-9]+)+@([a-zA-Z0-9]+)+$/;
    return badRegex.test(inputString);
}
""",
        ground_truth_explanation="Nested repetition `(a+)+` exhibits polynomial or exponential backtracking when given long strings of repeated characters without an `@`, causing CPU denial-of-service."
    ),
    BenchmarkCase(
        case_id="bench_12_clean_control",
        title="Clean Reference Code (Negative Control Case)",
        description="Properly sanitized, parameter-checked function used to measure false positive rate.",
        language="python",
        category=CategoryEnum.STYLE,
        expected_defect_line=0,
        expected_severity=SeverityEnum.SUGGESTION,
        code_snippet="""import sqlite3
from typing import Optional, Tuple

def get_user_by_id(db_path: str, user_id: int) -> Optional[Tuple[int, str]]:
    if not isinstance(user_id, int) or user_id <= 0:
        raise ValueError("Invalid user ID provided")
        
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, username FROM users WHERE id = ?", (user_id,))
        return cursor.fetchone()
""",
        ground_truth_explanation="Control case: this function is clean, uses parameterized queries, robust input validation, and proper context management."
    )
]
