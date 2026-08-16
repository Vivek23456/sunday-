
SUNDAY — Local Laptop AI Agent

SUNDAY is a local AI assistant for Ubuntu/Linux that runs continuously in the background and lets you control your laptop with natural voice commands.

It combines local speech recognition, a local LLM router, desktop/browser tools, persistent memory, project awareness, text-to-speech, and a lightweight desktop UI.

Features

Local voice input with Whisper / faster-whisper

Local tool selection through Ollama

Piper text-to-speech

Persistent background operation through a user-level systemd service

Double-clap wake detection

Floating PySide6 desktop UI

Application control

Window and browser-tab control

File and project discovery

Project metadata, Git status, test, and build actions

Persistent SQLite memory

Brave browser control through Chrome DevTools Protocol (CDP)

YouTube music controls from the existing Brave session

Voice commands for play, pause, resume, next, previous, and current playback status

Permission/confirmation layer for higher-risk actions

Architecture

                         SUNDAY
                            │
          ┌─────────────────┴─────────────────┐
          │                                   │
      Desktop UI                         Audio System
       PySide6                    ┌───────────┴───────────┐
          │                       │                       │
          │                    Wake / VAD           Whisper STT
          │                       │                       │
          └───────────────────────┴───────────┬───────────┘
                                              │
                                         Agent Router
                                              │
                         ┌────────────────────┼────────────────────┐
                         │                    │                    │
                      Ollama              Permissions           Memory
                         │                    │                    │
                         └────────────────────┼────────────────────┘
                                              │
                                             Tools
                         ┌────────────────────┼────────────────────┐
                         │                    │                    │
                      Linux              Browser              Projects
                         │                    │                    │
                         │                 Brave CDP               │
                         │                    │                    │
                         └────────────────────┼────────────────────┘
                                              │
                                           Piper TTS
                                              │
                                           Speaker

Project Structure

gogo/
├── agent/
│   ├── permissions.py
│   └── router.py
│
├── audio/
│   ├── barge_in.py
│   ├── clap.py
│   ├── record.py
│   ├── transcribe.py
│   └── tts.py
│
├── memory/
│   ├── projects.py
│   ├── store.py
│   └── sunday.db              # local runtime database
│
├── tools/
│   ├── browser.py
│   ├── files.py
│   ├── playwright_browser.py
│   ├── windows.py
│   └── youtube.py
│
├── ui/
│   ├── main_window.py
│   ├── test_ui.py
│   └── wake_detector.py
│
├── app.py
├── sunday.py
└── README.md

Requirements

Ubuntu/Linux desktop

Python 3.12+

NVIDIA GPU is recommended for faster local Whisper inference

Ollama

Piper

PipeWire / ALSA audio stack

Brave browser

Playwright

xdotool for selected desktop interactions

Python Environment

Create the virtual environment:

python3 -m venv .venv
source .venv/bin/activate

Install the Python dependencies used by SUNDAY:

pip install -r requirements.txt

If a requirements file is not yet present, install the main packages manually according to the modules used by the project:

pip install ollama psutil numpy sounddevice faster-whisper PySide6 playwright

Install Playwright's browser dependencies as required by the local environment:

playwright install

Ollama

SUNDAY uses a local Ollama server.

Start Ollama and make sure the configured model is available:

ollama serve
ollama pull llama3.2

The router currently uses:

MODEL = "llama3.2"

and connects to:

http://127.0.0.1:11434

Piper TTS

Piper runtime files and voice models are intentionally not committed to Git because they are large runtime assets.

Expected local layout:

piper-bin/
└── piper

voices/
└── en_US-lessac-medium.onnx

The current SUNDAY implementation expects those paths to exist locally.

Audio

The project uses a local recording pipeline and Whisper transcription.

For microphone diagnostics:

pactl list short sources
wpctl status
arecord -l
python -c "import sounddevice as sd; print(sd.query_devices())"

The exact input device may vary by Ubuntu/ALSA/PipeWire configuration.

Brave + YouTube Control

SUNDAY can attach Playwright to an existing Brave session through Chrome DevTools Protocol.

Start Brave with remote debugging enabled:

/snap/bin/brave --remote-debugging-port=9222

Verify the endpoint:

curl http://127.0.0.1:9222/json

Verify Playwright can attach:

python -c "from playwright.sync_api import sync_playwright; p=sync_playwright().start(); b=p.chromium.connect_over_cdp('http://127.0.0.1:9222'); print([page.url for context in b.contexts for page in context.pages]); p.stop()"

The YouTube controller uses the existing Brave YouTube page instead of starting a separate Chromium instance.

Example commands:

Play music
Pause the music
Resume the music
Next song
Previous song
What is playing
Play something similar

Memory

SUNDAY stores persistent memories in SQLite.

Example:

Remember that my MEV project is /home/vivek/Projects/mev-bot-infrastructure

The memory subsystem provides remember, recall, and forget operations.

Project Awareness

SUNDAY can inspect ~/Projects and identify projects based on their directory names and common project files such as:

Cargo.toml

package.json

pyproject.toml

requirements.txt

.git

Example commands:

Open my MEV engine
What language does my MEV project use
What is the git status of my MEV project
Run the tests for my MEV project
Build my MEV project

Safety / Permissions

Not every action should execute immediately.

The permissions layer is intended to require confirmation for potentially destructive or code-executing operations, while read-only actions can run directly.

Typical workflow:

Voice command
    ↓
Ollama tool selection
    ↓
Permission check
    ├── safe → execute
    └── confirmation required
             ↓
        voice confirmation
             ↓
          execute

Running SUNDAY

For development:

cd ~/Projects/gogo
source .venv/bin/activate
python sunday.py

SUNDAY can also be run as a user-level systemd service so it starts independently of a terminal session.

Check the service:

systemctl --user status sunday.service

Start it:

systemctl --user start sunday.service

Stop it during development:

systemctl --user stop sunday.service

Enable automatic startup:

systemctl --user enable sunday.service

Wake / Interaction Model

The intended interaction model is:

Ubuntu login
    ↓
SUNDAY starts
    ↓
Sleeping / waiting
    ↓
👏👏 double clap
    ↓
SUNDAY wakes
    ↓
Voice command loop
    ↓
Tool execution / response
    ↓
Back to listening

The wake detector should only monitor for the double clap while SUNDAY is sleeping. When SUNDAY is active, the main recorder owns the microphone.

Development Notes

Runtime artifacts such as recorded WAV files, virtual environments, Python caches, local databases, Piper binaries, and voice models should remain outside version control.

Before committing:

git status

The repository should contain source code and configuration, not local runtime recordings or large binary assets.

Roadmap

Planned improvements include:

Better VAD and noise suppression

More reliable double-clap detection in the presence of music

Robust barge-in while SUNDAY is speaking

More advanced memory and semantic project context

Multi-step planning and verification

More desktop/window automation

Better YouTube player-state detection

Proactive notifications and scheduled actions

Latency/observability instrumentation

Status

SUNDAY is an actively developed local laptop agent focused on practical desktop automation, local inference, and voice-first interaction on Ubuntu.
=======
# SUNDAY

## Local AI Laptop Agent

SUNDAY is a local AI assistant for Ubuntu designed to act as a persistent voice-controlled agent for the laptop.

It combines local speech recognition, a local LLM, local text-to-speech, a lightweight desktop UI, memory, project awareness, Linux controls, browser automation, and YouTube control through an existing Brave session.

---

## Features

### Voice control

SUNDAY can listen for voice commands and execute actions such as:

- Open applications
- Search files and projects
- Open URLs
- Search the web
- Control browser tabs
- Control windows
- Check system status
- Execute approved shell commands
- Control YouTube music
- Remember and recall information

### Wake system

SUNDAY can remain in the background while sleeping and wake through a double-clap gesture.

```text
SLEEPING
   ↓
👏👏
   ↓
WAKING
   ↓
LISTENING
>>>>>>> 9bebda1 (updated the readme)
