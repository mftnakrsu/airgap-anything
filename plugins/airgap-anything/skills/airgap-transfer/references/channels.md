# Channels

Every channel ends as a folder of files, so the bundle is the same. `transfer.channel` changes only how files are split and in which order they are sent (`references/bundle.md`, "Packing").

| Channel | Rule |
|---|---|
| `removable_media` | Files above 4 GiB minus one byte are split on `fat32`; any file larger than one medium is split. Volumes hold `medium.capacity_gb` minus a 2 % reserve, largest files first, and every volume carries the shared files (`SHA256SUMS`, `PARTS.sha256`, `VOLUMES.txt`, `INVENTORY.md`, the runbook files), so that any one volume tells what the set holds and what is missing. |
| `data_diode` | Nothing comes back, so the bundle must be complete and check itself. `channel.max_file_gb` sets splitting; one volume. `SEND-ORDER.txt` lists the files in sending order, the checksum lists first, so that the inside can check files as they arrive. |
| `staging_host` | The bundle lands on the staging host, where it is scanned; the checksum steps of the runbook can run there too, before the move inside. `channel.max_file_gb` sets splitting; one volume. |
| `other` | As `removable_media` when a medium is named; with `medium.capacity_gb` = `none`, one volume and no splitting. |

## Scanning stations

On any channel the files may pass a scanning station first:

- `INVENTORY.md` names the kind, source and license of every item, largest first: scanning hundreds of gigabytes takes time.
- Model weights are safetensors unless the user allowed pickle files for a model; the inventory says so.
- Publisher checksums were checked on the connected side. Publisher signatures are not checked by this skill; say so when someone asks.
