# Audio Visualizer

A real-time audio spectrum visualizer developed in Python using Pygame and Fast Fourier Transform (FFT).

## Course Information
- Course: Computer Graphics
- Supervisor: Dr. Ali Qaderiyan
- University: Islamic Azad University, Central Tehran Branch
- Faculty: Faculty of Convergent and Quantum Sciences and Technologies
- By: Mohammad Hossein Meftah
- Date: 2025

  
## Project Overview
This project captures real-time audio input from either a microphone or system audio
and visualizes the frequency spectrum using a dynamic, bar-based interface.
The visualization is divided into LOW, MID, and HIGH frequency ranges
and updates in real time based on the incoming sound signal.

The application supports switching between microphone input and system audio (WASAPI loopback)
and includes smoothing and decay mechanisms for more natural visual motion.

## Important Audio Configuration Notes
- When using **system audio**, the correct **input and output devices must be selected**
  in the operating system’s audio settings (Stereo Mix / Loopback device).
- In Windows, the user should ensure that the desired playback device is set correctly
  and that the loopback input is available and active.
- Audio visualization intensity is directly affected by **system volume** and **input gain**.
  Higher playback volume results in stronger FFT magnitudes and higher visualized bars.
- The overall sensitivity of frequency bands can be adjusted in real time using the keyboard.

## Features
- Real-time FFT-based audio spectrum analysis
- Microphone and system audio support (WASAPI loopback)
- Logarithmic frequency scaling (40 Hz – 16 kHz)
- Smooth bar animation with decay physics
- Frequency grid with LOW / MID / HIGH labeling
- Adjustable sensitivity during runtime

## Controls
- Click the top-left button to switch between **MIC** and **SYSTEM** audio input
- Arrow Up / Arrow Down keys to increase or decrease sensitivity

## Technologies Used
- Python
- Pygame
- NumPy
- PyAudio (WASAPI loopback)

## How to Run
1. Install dependencies:
pip install pygame numpy pyaudiowpatch
2. Run the application:

## Demo Video
A demonstration video showing the real-time audio visualization,
input switching between microphone and system audio,
and sensitivity adjustment based on volume levels.

Demo Video (Google Drive):
https://drive.google.com/file/d/147sdy1D8exhdAi0EPskCucSO9hpMbH4T/view
