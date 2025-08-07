```YAML
routes:

  handshake:
    trust_required: peer                # Direct trusted peer only
    ttl: 2                              # 2 hops max
    fallback: [proxy]                   # Use proxy if peer unreachable
    destination_format: mesh://{peer_id}
    auth: gpg_sig                       # GPG signature required
    log: true
    msg_id: auto

  trace:
    trust_required: peer
    ttl: 5
    fallback: [proxy, ghost]
    destination_format: mesh://{node_id}/trace
    auth: gpg_sig
    log: true
    msg_id: auto

  query:
    trust_required: peer
    ttl: 3
    fallback: [ghost]
    destination_format: mesh://{target}/query
    auth: gpg_sig
    log: true
    msg_id: auto

  echo:
    trust_required: ghost                # Ghosts only reflect
    ttl: 1
    fallback: []
    destination_format: self
    auth: none
    log: true
    msg_id: auto

  ping:
    trust_required: any                  # Accepts from any node
    ttl: 1
    fallback: [ghost]
    destination_format: mesh://{target}/ping
    auth: optional                       # Auth preferred but not required
    log: true
    msg_id: auto

  response:
    trust_required: peer
    ttl: 3
    fallback: [proxy]
    destination_format: mesh://{originator}/response
    auth: gpg_sig
    log: true
    msg_id: auto

```