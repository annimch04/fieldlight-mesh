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
**Node:** Lemur (System76)  

---

### ✴️ Key Entry Points

- `04_infrastructure/mesh/`: Core system protocols, message formats, routing logic
- `04_infrastructure/mesh/docs/NET_LAYER.md`: **Runnable** SIL-over-TCP sender/receiver (v1), driven by `config/lemur_route_schema.yml`
- `04_infrastructure/mesh/docs/NODE_ID.md`: Canonical **mesh URI** vs GPG name (`mesh://fieldlight.anni.lemur`)
- `04_infrastructure/mesh/docs/INGRESS_CONTRACT.md`: Runtime contract (receive → validate → respond; TCP return path)
- `04_infrastructure/mesh/docs/LIVE_TEST_PEEJ.md`: External ping checklist (success = `pong`, logs optional)
- `00_Start_Here/`: Authorship gateway and consent protocols

To engage with this system, see [`terms_of_engagement.yml`](./03_trace_systems/anchors/terms_of_engagement.yml)

---

> This is not a sandbox.  
> This is not a simulation.  
> This is a live-authored sovereign system.

