# Smart-Tank Auto-Clean

Automate print-head cleaning on HP Smart Tank / OfficeJet printers  
(**verified on a Smart Tank 550, firmware 2024-10-08**).

* 1 – 3 cleaning passes
* optional verification sheet after every pass
* any cron schedule you can write
* lightweight Python 3.12-slim Docker image

---

## 1 · Run from Python (no Docker)

```bash
pip install requests

# one clean, no sheet  (defaults)
python clean.py --printer 192.168.178.30

# one clean + verification sheet
python clean.py --printer 192.168.178.30 --verify

# two cleans, no sheets
python clean.py --printer 192.168.178.30 --cycles 2

# three cleans, each followed by a sheet
python clean.py --printer 192.168.178.30 --cycles 3 --verify
````

| flag / env var             | default | description                                     |
| -------------------------- | ------- | ----------------------------------------------- |
| `--printer` / `PRINTER_IP` | —       | **required** - printer IP / hostname            |
| `--cycles` / `CYCLES`      | `1`     | cleaning passes (1 – 3)                         |
| `--verify` / `VERIFY=true` | off     | print a verification sheet after **every** pass |

---

## 2 · Docker / Compose

### 2-a · Build the image

```bash
git clone https://github.com/you/smarttank-clean.git
cd smarttank-clean
docker build -t smarttank-clean .
```

### 2-b · One-shot run

```bash
docker run --rm \
  -e PRINTER_IP=192.168.178.30 \
  smarttank-clean --cycles 2
```

Anything after the image name is forwarded to `clean.py`, so you can add
`--verify`, `--cycles`, etc.

### 2-c · Scheduled service (cron inside the container)

1. **Edit `config/schedule.txt`**

Edit `config/schedule.txt` to set up your cron jobs. The file is
mounted as a volume in the container. E.g. the following line runs
one cleaning cycle every Sunday at 02:00 AM:

```cron
0 2 * * 0  python /app/clean.py --printer ${PRINTER_IP} --cycles 1
```

`${PRINTER_IP}` is replaced by the container at runtime.

2. **Compose up**

Comment in all lines in `docker-compose.yml`, that are commented out by default.

```bash
docker compose up 
```

#### Advanced schedule example

*This example runs one cycle every Wednesday at 02:00 AM, two cycles with a
verification sheet on the first Sunday of the month, and one cycle without
a sheet on every other Sunday.*

```cron
# Wed 02:00 run one cycle without verification sheet
0 2 * * 3  python /app/smarttankclean.py --printer ${PRINTER_IP} --cycles 1
# Every first Sunday (dates 1-7) run two cycles with verification sheet
0 2 1-7 * 0  python /app/smarttankclean.py --printer ${PRINTER_IP} --cycles 2
# Every other Sunday (dates 8-31) run one cycle without sheet
0 2 8-31 * 0  python /app/smarttankclean.py --printer ${PRINTER_IP} --cycles 
```

---

## 3 · Repository layout

```
smarttankclean.py              ← CLI tool
entrypoint.sh         ← starts cron or runs immediate job
config/schedule.txt   ← your cron jobs (bind-mounted or copied)
Dockerfile
docker-compose.yml
requirements.txt
```

---

## 5 · Disclaimers

* **Not affiliated with HP.**
  “HP”, “Smart Tank”, and “OfficeJet” are trademarks of HP Inc.
* Tested only on **Smart Tank 550**; other models may work but are unverified.
* The script uses the same undocumented LEDM endpoints as the printer’s web UI.
  **Use at your own risk** — excessive cleaning consumes ink and may shorten
  print-head life.
* Bug reports and pull requests are welcome!

```
