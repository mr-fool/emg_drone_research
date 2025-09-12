# EMG Crosshair Control Research Platform

A proof-of-concept system demonstrating real-time crosshair/HUD control using electromyography (EMG) signals from a single arm. This research validates affordable EMG acquisition hardware for human-machine interface applications.

**Repository**: https://github.com/mr-fool/emg_drone_research

## Hardware Components

- **BioAmp EXG Pill** - 4-channel EMG acquisition module (using 2 channels)
- **Arduino Uno R4** - Signal processing and serial communication
- **Standard EMG electrodes** - Ag/AgCl surface electrodes
- **Python application** - Real-time visualization and data logging

## Hardware Connection

### BioAmp EXG Pill to Arduino Connection
```
BioAmp EXG Pill    Arduino Uno R4
─────────────────  ──────────────
VCC             →  3.3V
GND             →  GND
OUT1            →  A0 (Left/Right)
OUT2            →  A1 (Up/Down)
OUT3            →  (Not used)
OUT4            →  (Not used)
```

## EMG Sensor Placement (Single Arm Configuration)

```
Right Arm EMG Sensor Placement:
                                    
    Shoulder                        
        |                           
        |                           
        |                           
    Upper Arm                       
        |                           
        |                           
        |                           
    ────┴────                       
     Elbow                          
    ────┬────                       
        |                           
        |   [A1] - Forearm Extensor (Up/Down Control)
        |    ●●                     
    Forearm                         
        |    ●●                     
        |   [A0] - Forearm Flexor (Left/Right Control)
        |                           
    ────┴────                       
     Wrist                          
        |                           
      Hand                 
```

### Channel Mapping
- **A0 (Left/Right)**: Forearm flexor muscles - Wrist flexion → Horizontal crosshair movement
- **A1 (Up/Down)**: Forearm extensor muscles - Wrist extension → Vertical crosshair movement

### Muscle Movement Instructions
For crosshair control, the actual muscle movements are:

- **A0 (Left/Right)**: Forearm flexor - When you flex your wrist (bend it down toward your palm), this moves the crosshair left or right
- **A1 (Up/Down)**: Forearm extensor - When you extend your wrist (bend it back up), this moves the crosshair up or down

## Installation

### Arduino Setup
1. Connect BioAmp EXG Pill to Arduino Uno R4 using the wiring diagram above
2. Upload `arduino_emg_code.ino` to the Arduino
3. Connect EMG electrodes according to the placement diagram above

### Python Environment
```bash
git clone https://github.com/mr-fool/emg_drone_research.git
cd emg_drone_research
pip install -r requirements.txt
```

### Dependencies
- Python 3.8+
- pygame>=2.5.0
- pyserial>=3.5

## Usage

### Running the Demo
```bash
python main.py
```

The system will automatically detect the Arduino connection. If no Arduino is found, keyboard controls are available for testing:
- **WASD**: Crosshair movement
- **R**: Reset crosshair position
- **ESC**: Exit

### EMG Calibration
1. Launch the application with Arduino connected
2. Keep arm relaxed during initial calibration phase
3. System will automatically establish baseline values
4. Begin EMG control once calibration completes

## Research Features

### Real-Time Visualization
- Dynamic crosshair with EMG-controlled movement
- Live EMG signal strength indicators with color-coded activity levels
- Hardware status and signal quality monitoring
- Control input visualization with real-time feedback bars
- Corner targeting brackets for precision aiming assistance

### Data Collection
- Comprehensive CSV logging with timestamp precision
- Raw EMG values and processed control signals
- Crosshair position tracking for accuracy analysis
- Signal quality metrics for hardware validation
- Session metadata for research reproducibility

### Hardware Validation Metrics
- **Signal Acquisition Rate**: Real-time sampling frequency monitoring
- **Signal Quality Assessment**: SNR and baseline stability tracking
- **Control Latency**: Time from muscle activation to crosshair response
- **Position Accuracy**: Precision of EMG-based positional control

## Research Applications

This platform validates EMG-based human-machine interfaces for:
- Gaming and interactive entertainment systems
- Assistive technology development
- Prosthetic device control systems
- Hands-free interface design
- Biomedical signal processing research
- HUD and targeting system control

## Technical Specifications

### EMG Processing
- **Sampling Rate**: 500 Hz per channel
- **Signal Filtering**: Muscle-specific Butterworth filters (70-160 Hz)
- **Envelope Detection**: Real-time amplitude demodulation
- **Adaptive Thresholding**: Dynamic baseline tracking and noise rejection

### Control Mapping
- **Signal Range**: 0-1023 (10-bit ADC resolution)
- **Control Sensitivity**: Adaptive thresholding with baseline compensation
- **Update Rate**: 60 Hz visualization with 6 Hz data logging
- **Movement Constraints**: Bounded workspace for safety and repeatability
- **Visual Feedback**: Color-coded crosshair indicating muscle activity level

## Data Output Format

Research data is automatically saved to `data_output/emg_crosshair_YYYYMMDD_HHMMSS.csv`:

```csv
timestamp,left_right_raw,up_down_raw,left_right_processed,up_down_processed,crosshair_x,crosshair_y,signal_quality,acquisition_rate
```

## Safety Considerations

- Use only certified medical-grade electrodes
- Ensure proper skin preparation and electrode placement
- Monitor for skin irritation during extended sessions
- Discontinue use if any discomfort occurs
- This system is for research purposes only

## License

This research platform is released under the MIT License for academic and research use.