# Repository Guidelines

## Project Structure & Module Organization
Firmware that runs on the Pico W lives in `firmware/` (e.g., `main.py`, `wifi.py`, `ws_server.py`) and must remain MicroPython-safe. The desktop controller plus its dependencies reside in `controller/`, while `scripts/` holds host utilities such as `setup_hotspot.sh` and LCD helpers. Hardware drawings live under `schematics/`, and deeper walkthroughs stay in `docs/`.

## Build, Test, and Development Commands
Recommended bootstrap:
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r controller/requirements.txt
sudo ./scripts/setup_hotspot.sh start && ./scripts/setup_hotspot.sh status
mpremote connect /dev/ttyACM0 cp firmware/*.py : && mpremote reset
python3 controller/controller_xbox.py 10.42.0.123
```
Replace the IP with the value shown on the LCD. Use `./scripts/setup_hotspot.sh stop` when finished so system networking is restored.

## Coding Style & Naming Conventions
Use 4-space indentation, keep lines ≤100 chars, and favor type hints plus docstrings on host-side code. Functions, modules, and files use `snake_case`; classes use `CamelCase`; constants use `ALL_CAPS`. MicroPython modules should avoid heavy imports, dynamic allocation in loops, and blocking sleeps longer than `MAIN_LOOP_MS`. Comment only when intent or timing constraints are non-obvious, and encapsulate hardware access behind helper functions (see `motor.py`) to ease simulated testing.

## Testing Guidelines
There is no automated CI yet, so rely on quick hardware smoke tests: (1) run the controller against a fake address (`python3 controller/controller_xbox.py 10.42.0.999`) to confirm joystick polling, (2) flash firmware and verify LCD states step through BOOT → NET_UP → DRIVE, and (3) measure packet cadence with `scapy` or `tcpdump` when networking code changes. Future unit tests should live in `controller/tests/test_<feature>.py` using pytest and joystick stubs; firmware tests belong in `firmware/tests/` and should mock `machine` APIs.

## Commit & Pull Request Guidelines
Follow the existing imperative subject style (`Add:`, `Fix:`, `Update:`). Keep messages under 72 characters, describe context plus verification steps in the body, and reference issues (`Refs #42`). Pull requests need: concise summary, testing proof (commands above, screenshots of LCD or controller output when UI changes), and notes on cross-component compatibility. Request review from an owner of the touched subsystem before merging.

## Security & Configuration Tips
Do not commit live Wi-Fi credentials or hotspot passwords; keep them in local `.env` files and only edit `firmware/config.py` placeholders. Run privileged scripts (`setup_hotspot.sh`, `install_lcd_driver.sh`) with `sudo` sparingly and reset any distro-specific edits before pushing. Strip MAC addresses, IPs, and GPS metadata from logs or photos before uploading to `docs/` or issues.
