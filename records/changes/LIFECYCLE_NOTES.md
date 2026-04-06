
### 2026-03-30 — operational record layout
- **Object changed:** operational record layout
- **Change type:** structure cleanup
- **Reason:** Grouped generated and append-style outputs into a dedicated records tree
- **Impact:** Cleaner workstation root and more predictable operator output paths
- **Replacement / rollback:** Override -TargetFile for legacy locations or revert helper defaults if needed

