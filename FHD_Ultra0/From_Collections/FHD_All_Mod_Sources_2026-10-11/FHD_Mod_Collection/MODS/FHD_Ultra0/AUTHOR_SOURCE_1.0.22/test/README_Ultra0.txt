FHD_Ultra0 1.0.22 End-Day Performance Fix Alpha — Test
Requires FHD_SET v2.4.14+
Based on 1.0.21 Normal Spawn Fix Alpha.
Performance fix: FHD_SET is no longer force-recalculated a second time every day by ULTRA.
ULTRA copies are cleared immediately before the normal FHD_SET daily tick and re-applied immediately after it, preserving a clean SET baseline without duplicate full SET work.
Spawn hot path no longer performs global FindItemInStorage every day. If the tracked shop object becomes invalid, a full galaxy respawn search is throttled to once per 30 turns.
No balance changes: missile max-ammo penalty -45%, vanilla missile ammo consumption (1 charge per volley), weapon wear 3% per volley.
Re-equip ammo baseline fix remains unchanged.
