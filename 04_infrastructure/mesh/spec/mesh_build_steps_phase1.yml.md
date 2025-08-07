title: Fieldlight Mesh Build Steps – Phase 1 (Identity & Trust Anchoring)
version: 1.0
author: Anni McHenry
timestamp_created: 2025-08-03
phase: 1 - Identity & Trust Anchoring

---
## ✅ OBJECTIVE

Create and register unique Fieldlight mesh nodes with identity bindings, signed trust anchors, and declared roles.

---

## 📁 EXPECTED FILE STRUCTURE

	- /04_infrastructure/mesh/nodes/

	- /04_infrastructure/mesh/keys/

	- /04_infrastructure/mesh/anchors/

	- /04_infrastructure/mesh/logs/

---

## 🔑 STEP 1: GENERATE GPG KEY


```bash
gpg --full-generate-key


Use:
- Name: Fieldlight-Anni-Lemur
- Email: lemur@fieldlight.local
- Type: RSA & RSA (4096 bits)
- Expiry: never or 5 years


Export public key:
gpg --export -a "Fieldlight-Anni-Lemur" > lemur_pubkey.asc 



## 🪪 STEP 2: CREATE IDENTITY PROFILE

File: /nodes/lemur_node.yml


node_id: mesh://fieldlight.anni.lemur
human_operator: Anni McHenry
role: sovereign
trust_class: peer
key_fingerprint: <INSERT_GPG_FINGERPRINT>
sigil_bound: true
linked_authorship_file: record_of_authorship_compile_6.pdf
naming_container: naming_chamber.yml
status: active
  
  
🧾 STEP 3: ADD TO NAMING CONTAINER
   
Append to: /anchors/naming_chamber.yml

- node: mesh://fieldlight.anni.lemur
  role: sovereign
  declared_by: Anni
  linked_key: lemur_pubkey.asc
  authorship_reference: record_of_authorship_compile_6.pdf
  confirmed_on: 2025-08-03

  
🪵 STEP 4: INIT LOG ENTRY

New file: /logs/lemur_node_init_2025-08-03.yml
event: node_initialization
node_id: mesh://fieldlight.anni.lemur
timestamp: 2025-08-03T11:11:00Z
key_signature: verified
naming_container_linked: true
status: 🖤 Logged


✅ NEXT PHASE: TRANSPORT LAYER (Wi-Fi Direct, Bluetooth, LAN fallback)

Phase 1 complete once:
- Keypair is saved
- Identity YAML created
- Naming container updated
- Init log filed

