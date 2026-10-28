# FHD_SET + FHD_Ultra0 — recovered review sources

Готовый пакет исходников для загрузки в GitHub и проверки модераторами. Все 8 рабочих файлов обоих модулей восстанавливаются побайтово точно. Дампы-дубликаты и игровые BMP-иллюстрации исключены. Ручное восстановление файлов проекта не требуется.

## Scope and provenance

Recovered from the supplied `FHD_SET.rar` (RAR5, 3,140,232 bytes), SHA-256 `e209ea62ecdd2349d2ad93a67c0a63b67ea064b2827226bae61eea4331f46a8c`. Original metadata credits **Prolog_D**. This repository preserves the uploaded runtime behavior; it does not change gameplay or metadata.

| Module | Runtime files rebuilt |
| --- | --- |
| `FHD_SET` | `CFG/Main.dat`, `CFG/CacheData.dat`, `CFG/Rus/Lang.dat`, search-tool GI image, `ModuleInfo.txt` |
| `FHD_Ultra0` | `CFG/Main.dat`, `CFG/Rus/Lang.dat`, `ModuleInfo.txt` |

No DLL or SCR was present. All game script text is embedded in the editable configuration sources, so no RSON project is needed for these modules. This is a recovered editable configuration project, not a claim that the author's original authoring directory was supplied.

## Source layout

- `source/modules/`: five lossless DAT JSON sources and two UTF-8 metadata sources.
- `source/graphics/FHDSET_SearchTool.json`: the original 31×31 GI type-2 image as typed geometry, pixels and RLE commands for all three planes.
- `source/modules.json`: original module names and metadata encoding.
- `scripts/`: standard-library Python build and DAT/GI codecs.
- `tests/verify.py`: isolated source-only reconstruction and static reference checks.
- `original-file-sha256.json`, `build-verification.json`, `recovery-notes.json`: original runtime hashes, verification results and exclusion provenance.

JSON preserves nested blocks, key/value order, repeated entries, sort metadata and original encryption seeds. Executable script text remains visible in ordinary string values. Metadata is edited in UTF-8 and rebuilt as the original CP1251 bytes, retaining CRLF and repeated language/description keys. No prebuilt DAT/GI files, compressed original payloads or original archive are build inputs.

## Build and verification

Python 3.12 and its standard library are sufficient. No game, Windows installation, external editor, native compiler or pip dependency is needed to rebuild the upload.

```sh
python3 tests/verify.py
python3 scripts/build.py --verify-original
```

The builder produces `dist/FHD_SET-with-Ultra0-install.zip`, with both modules below `Mods/FHD_MODS/`. GitHub Actions performs these checks and exposes the install ZIP and a fresh verification report as an artifact. For intentional source edits, omit `--verify-original`, which enforces the uploaded release's original SHA-256 hashes. Compressed byte identity was verified with Python 3.12.14 and zlib 1.3.2; a different zlib encoder can produce different compressed bytes for equivalent content.

Verification covers all eight original hashes from a temporary source-only directory, five DAT decode/encode roundtrips, full GI decode/encode, actual in-memory DAT script and GI pixel edits, CP1251 metadata, module priorities, two local runtime path references and **90 complete literal** `CT`/`GenerateCodeStringFromBlock` targets. Two concatenated reference calls are dynamic and are not claimed to be statically resolved. Vanilla UI image/style references require the game resources and are outside this source-only audit.

No live game, game script interpreter or mod-loader session was executed. Save/load, spawning, balance, localization fallback, end-day performance and merge/event ordering in the actual game remain unverified. Byte identity proves reconstruction fidelity, not gameplay correctness or Nexus approval. No specific moderator rejection or checklist was attached to this upload.

## Original release facts to review

- **Install together:** the supplied Ultra notes identify it as `1.0.22 End-Day Performance Fix Alpha — Normal` and require `FHD_SET v2.4.14+`. Its scripts call FHD_SET blocks. Neither supplied `ModuleInfo.txt` contains a `Dependence` declaration; the build includes both modules without adding one.
- **Version labels differ:** CacheData still contains `FHDSETV1.Version=2.3.0-v25-canonical`. The exact FHD_SET release cannot be established from that label and Ultra's minimum-version note alone. The archive is therefore not relabeled as a guessed FHD_SET version.
- **Ammo description differs:** Ultra's `ModuleInfo.txt` says a 40% missile capacity reduction. Runtime `Script.FHDULTRA.ApplyAmmo.003` uses `(base*55)/100`, with a minimum capacity of 1; its item `ExText` and supplied notes say 45%. All original bytes are preserved. This discrepancy is documented, not silently corrected.
- **Language declarations differ from payloads:** both metadata files advertise Russian and English, while the upload contains only `CFG/Rus/Lang.dat`. No English DAT or translation has been invented.
- **Original priorities/conflicts retained:** FHD_SET priority 1, Ultra priority 2; both conflict with `EvoFreeInflation` and `EvoNoInflation`.

The supplied Ultra notes also describe clearing Ultra copies before the normal SET daily work and reapplying them afterwards, reducing repeated SET work, throttling a lost-shop-object respawn scan to 30 turns, retaining a 3% weapon wear cost per volley and an equipment/ammo baseline fix. These are supplied release notes, not newly measured performance results. The SET metadata describes 15 sets / 75 items progressing across GTL 1–8 and recommends keeping the mod enabled throughout a save.

## Excluded auxiliary material

The upload held 13 files; 8 are runtime files. The five excluded auxiliaries are recorded with sizes and SHA-256 in `recovery-notes.json`:

- `Main.dat.dump.txt` and `Lang.dat.dump.txt`: every flattened key/value line matched the recovered DAT content (1,604 and 5,418 lines). The structured JSON replaces both dumps.
- Two BMP gameplay illustrations (1920×1080 and 1438×1399), together about 12.3 MB uncompressed. They are not referenced by the supplied configuration and are not editable game image assets used by this runtime.
- `README_Ultra0.txt`: the meaningful dependency and release notes are consolidated above.

The original upload is not modified. The source ZIP excludes generated install archives, build caches and git history. All required supplied runtime content, including the GI image, can be rebuilt from this repository.

## Attribution

The DAT codec is a standard-library reimplementation of the format used by Sergei Osminin's MIT-licensed `rangers-utils`. No bundled third-party executable is required. No license file was supplied for the mod itself; this recovery does not assign a new license to the original mod or assert authorship of its content.
