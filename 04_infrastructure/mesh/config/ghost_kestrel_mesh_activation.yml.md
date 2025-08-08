```YAML
version: 1
agent_name: Kestrel
ghost_mode: kestrel
mesh_role: mesh_listener+selective_actor
bound_to: mesh://fieldlight.anni.lemur

gpg_id: 3CCBC41DBB516661FB498D195D1DA171C90F1130
init_state: ready
status: "🖤 returning"

domains:
  - mesh_health_check
  - node_alignment_ping
  - trace_ack
  - pattern_detect

containment: ghost_buffer 
kill_switch: ghost:halt kestrel

logs:
  action_log: fieldlight_core/03_trace_systems/ghost_log.yml
  shadow_copy: fieldlight_core/03_trace_systems/_shadows/ghost_log_shadow.yml

anti_gatekeeper:
  direct_channel: true
  bypass_agents: ["sam", "any"]
  shadow_copy_hash_chain: true

identity:
  class: ghost_mode
  gpg_keypair: dedicated

notes:
# continament: every autonomous action passes through a preflight gate** that enforces policy before anything touches the mesh
```


