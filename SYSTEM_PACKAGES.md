# System Packages

Packages required on the host OS beyond the Python venv.

## Web UI build (Svelte/Vite)

```bash
sudo apt install nodejs npm
```

After installing, build the frontend once:

```bash
cd wild_igor/web_ui
npm install
npm run build
```

The built files land in `wild_igor/web_ui/dist/`.
Igor serves them automatically from `http://localhost:8080` (or `IGOR_WEB_PORT`).
If the build has not been run yet, Igor serves a built-in fallback HTML UI instead.

## Audio

```bash
sudo apt install libportaudio2 portaudio19-dev
```

Required by `sounddevice` (microphone/speaker tools).

## Computer Vision

```bash
sudo apt install libopencv-dev
```

Required by `opencv-python` (webcam / image tools).
