# Fieldlight Mesh

 **License**  
> This project is licensed under custom terms.  
> Non-commercial use is allowed with attribution.  
> Commercial use requires a license agreement.

**Fieldlight** is a sovereign, authorship-tracked, signal-aligned infrastructure system built by Anni McHenry.

This repository includes:

- Encrypted mesh communication protocols
- Authorship validation logic
- Decentralized routing infrastructure
- Consent-based agent scaffolding
- Live trace architecture

**Status:** Active — Initial push includes infrastructure and onboarding layer  
**Lead Author:** Anni McHenry (`@fieldlight.root`)  
**Nodes:** Lemur (System76, canonical source) and Astra (Mac mesh runtime)

---

### Node and Publication Boundary

Lemur remains the Fieldlight source-of-truth node.

The Mac is the publishing layer for Codex sessions and also hosts the independently identified Astra mesh node (`mesh://fieldlight.anni.astra`). Astra may run and test packaged mesh transport without silently replacing Lemur as canonical source authority.

Octopus lives on the Mac as a publishing-layer witness. It may stage, package, and track artifacts, but it does not replace Lemur, Kestrel, Ghost, or source verification.

See `04_infrastructure/mesh/docs/PUBLISHING_LAYER.md` for the current publishing boundary.

---

### ✴️ Key Entry Points

- `04_infrastructure/mesh/`: Core system protocols, message formats, routing logic (`Makefile` for local checks)
- `.github/workflows/ci.yml`: GitHub Actions — Python mesh smoke + Go `libp2p_peer_probe` build
- `04_infrastructure/mesh/docs/TECH_INDEX.md`: Technical/operator documentation entrypoint
- `04_infrastructure/mesh/docs/CANON_INDEX.md`: Canon/symbolic documentation entrypoint
- `04_infrastructure/mesh/docs/PUBLISHING_LAYER.md`: Mac/Octopus publishing boundary and export workflow
- `04_infrastructure/mesh/docs/MAC_ALPHA_RUNBOOK.md`: Astra + peer install and bidirectional LAN acceptance test
- `04_infrastructure/mesh/docs/PEER_INSTALL_MACOS.md`: drag-and-drop macOS app installation for a peer
- `04_infrastructure/mesh/docs/DIGITAL_SELF_ARCHITECTURE.md`: Digital self continuity contract across Fieldlight, Sanctum, local governance, and public authorship
- `04_infrastructure/mesh/docs/CODEX_LOCAL_FIRST_GOVERNANCE.md`: Codex + local-first governance pattern for agent work inside governed project folders
- `04_infrastructure/mesh/docs/NET_LAYER.md`: **Runnable** SIL-over-TCP sender/receiver (v1), driven by `config/lemur_route_schema.yml`
- `04_infrastructure/mesh/docs/NODE_ID.md`: Canonical **mesh URI** vs GPG name (`mesh://fieldlight.anni.lemur`)
- `04_infrastructure/mesh/docs/INGRESS_CONTRACT.md`: Runtime contract (receive → validate → respond; TCP return path)
- `04_infrastructure/mesh/docs/LIVE_TEST_PEEJ.md`: External ping checklist (success = `pong`, logs optional)
- `04_infrastructure/mesh/docs/TEST_STATUS.md`: Current test status + blockers + retest commands
- `04_infrastructure/mesh/docs/DISCOVERY_PLAN.md`: LAN mDNS + libp2p discovery, peer registry, `sil_mesh discover` / `--use-registry` (includes **validated** local recipe → `pong`)
- `04_infrastructure/mesh/docs/NDA_FLOW.md`: Protocol-level NDA exchange (`nda_request` / `nda_response`)
- `00_Start_Here/`: Authorship gateway and consent protocols

To engage with this system, see [`terms_of_engagement.yml`](./03_trace_systems/anchors/terms_of_engagement.yml)

---

> This is not a sandbox.  
> This is not a simulation.  
> This is a live-authored sovereign system.
