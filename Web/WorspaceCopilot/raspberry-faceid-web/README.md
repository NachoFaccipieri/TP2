# Raspberry Face ID Project

## Overview
This project implements a Face ID system using a Raspberry Pi with a connected camera. The system captures images, processes them to extract facial embeddings, and recognizes faces. It communicates with a web interface via MQTT to notify users of recognized faces.

## Project Structure
```
raspberry-faceid-web
├── public
│   ├── index.html        # HTML structure for the web interface
│   ├── style.css         # CSS styles for the web interface
│   └── script.js         # JavaScript for handling user interactions and MQTT communication
├── server
│   ├── regRostro.py      # Flask application for face registration and recognition
│   ├── mqtt_bridge.py     # Bridge between face recognition logic and MQTT broker
│   └── requirements.txt   # Python dependencies for the server-side code
├── .vscode
│   └── launch.json       # Debugging configuration for the development environment
└── README.md             # Documentation for the project
```

## Setup Instructions

1. **Install Dependencies**:
   Navigate to the `server` directory and install the required Python packages listed in `requirements.txt`:
   ```
   pip install -r requirements.txt
   ```

2. **Run the MQTT Broker**:
   Ensure that the Mosquitto MQTT broker is installed and running on your Raspberry Pi.

3. **Start the Flask Server**:
   In the `server` directory, run the Flask application:
   ```
   python regRostro.py
   ```

4. **Open the Web Interface**:
   Open `public/index.html` in a web browser to access the Face ID web interface.

## Usage
- **Register a New Face**: Click the "Registrar nuevo rostro" button to register a new face. Follow the prompts to enter the name.
- **Ring the Bell**: Click the "Tocar timbre" button to check for recognized faces. The system will notify you if a match is found.

## Notes
- Ensure that the camera is properly connected and configured on the Raspberry Pi.
- The embeddings for recognized faces are stored locally on the Raspberry Pi.
- The project is designed to run entirely on the Raspberry Pi, with no external database required. All data is processed and stored locally.

## License
This project is licensed under the MIT License.