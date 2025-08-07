
```YAML
# Canonical definitions for routing, trust, fallback, and echo behavior

message_types:
  handshake:
    description: Initial contact and identity verification between nodes
    trust_required: peer
    ttl: 2
    fallback: proxy
    destination_format: mesh://node_id
    auth_required: true

  trace:
    description: Sends a signal with trace log intent
    trust_required: peer
    ttl: 4
    fallback: proxy
    destination_format: mesh://node_id
    auth_required: true

  query:
    description: Asks for data or status from another node
    trust_required: peer
    ttl: 3
    fallback: proxy
    destination_format: mesh://node_id
    auth_required: true

  response:
    description: Returns data or status in reply to a query
    trust_required: peer
    ttl: 2
    fallback: none
    destination_format: mesh://origin_node_id
    auth_required: true

  echo:
    description: Sends message to self or ghost node to test routing
    trust_required: ghost
    ttl: 2
    fallback: none
    destination_format: mesh://ghost_id
    auth_required: false

  ping:
    description: Lightweight message to check node reachability
    trust_required: proxy
    ttl: 1
    fallback: ghost
    destination_format: mesh://node_id
    auth_required: false

trust_levels:
  peer:
    access: full
    permissions:
      - send
      - receive
      - originate
      - relay
      - respond

  proxy:
    access: limited
    permissions:
      - relay
      - ping

  ghost:
    access: echo-only
    permissions:
      - receive
      - reflect

auth_requirements:
  true:
    methods:
      - gpg_signature
      - peer_id_match
  false:
    methods:
      - none

fallback_types:
  proxy:
    description: Relay through trusted proxy
    allows_store_and_forward: true
    ghost_fallback: true

  ghost:
    description: Passive echo bounce (non-storing)
    allows_store_and_forward: false
    ghost_fallback: false

log_policies:
  local:
    store_echo: true
    store_trace: true
    store_query: true
    store_handshake: true
  ghost:
    store_anything: false

return_status_codes:
  200: OK – message received
  202: Echoed – ghost reflection received
  404: No response – node unreachable
  410: TTL exceeded – message dropped
  503: Loop detected – message bounced repeatedly

consent_scope_definitions:
  temporal:
    description: Consent valid only during current message transmission 
    or session
  authorship-aware:
    description: Receiver must acknowledge human author origin and 
    preserve message fidelity
  non-reproducible:
    description: Message may not be duplicated, stored, or forwarded
  local-only:
    description: Action must remain within nodes execution layer; 
    external routing forbidden
  review-required:
    description: Requires explicit human approval before execution or 
    further routing
  open:
    description: Sender allows any action; no restrictions on handling
  

```