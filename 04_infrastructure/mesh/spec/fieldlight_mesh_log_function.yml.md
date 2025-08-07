
```YAML
logs:

  routing_log:
    file: routing_log.yml
    purpose: Unified log for all routed messages
    includes_fields:
      - sys
      - type
      - origin
      - destination
      - ttl
      - trust_level
      - auth
      - status
      - timestamp
    default_behavior: log all messages unless explicitly excluded
    notes:
      - All messages must carry a `sys` value for response matching
      - Can be filtered by type or peer for analysis

  presence_log:
    file: presence.log
    purpose: Tracks vault drop events and local file activity
    auto_trigger: yes
    scope: /mnt/sanctum/obsidian_vault

  echo_log:
    file: lemur_echo_test_log.yml
    purpose: Stores results from `lemur_echo_test.py`
    notes: Dedicated to echo test cycles; not used for live routing

  fallback_log:
    file: lemur_fallback_routes.yml
    purpose: Map TTL drops, retries, and offline routes
    trigger_conditions:
      - TTL expiration
      - Unreachable peer
      - Fallback routing path engaged
    status: enabled

  peerlink_test_log:
    file: lemur_peerlink_test_01.yml
    purpose: Records results of simulated peer handshake tests
    config_options:
      - expected_peer_id
      - test_payload
      - verify_sig
      - reply_timeout

  ghost_behavior_log:
    file: ghost_behavior_reference.yml
    purpose: Documents ghost node reflection behavior
    includes_fields:
      - reflected_msg_id
      - origin
      - return_path
      - received_timestamp
      - reflected_timestamp
    notes:
      - Ghosts do not persist logs themselves; this is node-local

  message_audit_log:
    file: message_audit_log.yml
    purpose: General audit of all messages sent and received
    includes_fields:
      - msg_id
      - message_type
      - direction
      - origin
      - destination
      - result
      - timestamp
    notes:
      - Useful for pattern analysis, debugging, and anomaly tracking
      - Separate from routing_log to avoid duplication noise

```

