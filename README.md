# TimeTwister

*SK R&D — 2025 Edition*

TimeTwister is a lightweight Flask application for running live events. It lets staff control multiple event timers, post announcements, and display an optional image per event on a public-facing screen.

## Features

- Manage up to three concurrent event timers with start, pause, resume, reset, and preset controls.
- Toggle announcements and timers on or off per event without deleting content.
- Upload, preview, and display images alongside each event.
- Built-in buzzer support with manual triggers and per-event auto buzz when timers expire.
- Adjustable buzzer volume slider so the display audio matches venue noise levels.
- Dedicated control dashboard (`/`) and display view (`/display`) designed for kiosk/projector setups.

## Prerequisites

- Python 3.10 or newer (3.11+ recommended).
- `pip` for package management.
- Git for cloning the repository (optional if transferring via other means).

## Quick Start (local workstation)

```bash
# Clone the repository (or copy it to the target machine)
git clone https://github.com/BaxterKrug/TimeTwister.git
cd TimeTwister

# Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Launch the app (development server)
python main.py
```

The Flask development server defaults to `http://0.0.0.0:8000`.

- Open `http://localhost:8000/` for the staff control panel.
- Open `http://localhost:8000/display` (ideally on a separate screen or device) for the public display.

## Raspberry Pi Deployment

The production setup assumes a Raspberry Pi (any 64-bit model running Raspberry Pi OS or another Debian-based distro) connected to the venue network. The Pi hosts the Flask app; laptops on the same network reach it in a browser.

1. **Prepare the Pi**

   ```bash
   sudo apt update
   sudo apt install -y python3 python3-venv python3-pip git
   ```

2. **Clone and install**

   ```bash
   git clone https://github.com/BaxterKrug/TimeTwister.git
   cd TimeTwister
   python3 -m venv .venv
   source .venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

3. **Launch the server**

   ```bash
   source /home/pi/TimeTwister/.venv/bin/activate
   python /home/pi/TimeTwister/main.py
   ```

   By default the app binds to `0.0.0.0:8000`. Leave this terminal running while the app is in use. For unattended service, create a `systemd` unit or use a process manager such as `supervisor` to run the same command at boot.

4. **Find the Pi's address**

   ```bash
   hostname -I
   ```

   Note the IPv4 address (e.g., `192.168.1.45`). Use this address in place of `localhost` on other devices.

5. **Connect from shop laptops**

   - **Windows**: Open Microsoft Edge/Chrome and visit `http://192.168.1.45:8000/` for the control panel and `http://192.168.1.45:8000/display` for the public screen.
   - **Fedora Linux**: Open Firefox/Chrome and use the same URLs. If firewall rules exist on Fedora, ensure outbound traffic to port 8000 is allowed (default is open).

   Keep both the Pi and laptops on the same LAN/VLAN. If you need access across different networks or over the internet, place the Pi behind a VPN or reverse proxy and secure the traffic with HTTPS and authentication.

6. **Persist uploads**

   The Pi stores uploaded images in `TimeTwister/uploads/`. Back up this directory if you rebuild the Pi or deploy from scratch.

## Deployment Notes

- The app writes uploaded images to the `uploads/` directory. Ensure the service account running the app has read/write access to that folder.
- For production or kiosk use, consider running the app behind a process manager (e.g., `systemd`, `supervisor`, or Docker) and reverse proxy (e.g., Nginx).
- If serving over HTTPS, terminate TLS at the proxy and forward requests to the Flask process.

## Operating Instructions

1. Use the **Add Event** button to create up to three events. Each event card contains:
   - **Event Name** field: updates immediately on blur.
    - **Timer controls**: enter minutes and start, tap one of the built-in presets
       (Pokemon, MTG, Yu-Gi-Oh, Weiss, Godzilla, Gundam, UA, FAB, Riftbound, FF) with the
       configured tournament durations, pause, resume, or reset without losing the remaining time.
   - **Announcements**: type a quick message and click *Set*.
   - **Display Image**: upload a PNG/JPEG/GIF; click *Remove Image* to clear it.
    - **Feature toggles**: disable timer, announcements, or auto buzzer without deleting data.
    - **Buzzer tools**: use *Play Buzzer* for a manual alert, or leave **Auto Buzzer** enabled
       to fire automatically when the timer hits zero.
    - **Buzzer Volume slider** (top of the page): drag between 0–100% to adjust how loud the
       buzzer plays on the public display without touching the TV remote.
2. The display view polls once per second to keep the timer and message current with minimal flicker.
    - The first click or key press on the display page unlocks audio autoplay so the buzzer can play.
3. Removing an event automatically clears any uploaded image associated with it.

## Updating Dependencies

Whenever you change `requirements.txt`, run:

```bash
pip install -r requirements.txt
pip freeze > requirements.lock
```

Creating a locked file (`requirements.lock`) is optional but useful for reproducible deployments.

## Troubleshooting

- **Port already in use**: stop the other service or run `python main.py --port 8080` after adding a CLI argument handler (or set the `PORT` environment variable if you modify the app accordingly).
- **Image uploads failing**: confirm the file is under 3 MB and has an allowed extension (`png`, `jpg`, `jpeg`, `gif`).
- **Display not updating**: make sure the browser allows JavaScript and the network can reach `/api/state`.

## License

This project is released under the [GNU General Public License v3.0 (GPL-3.0)](LICENSE).
