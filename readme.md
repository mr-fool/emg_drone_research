# EMG Flight Control Research Platform

A proof-of-concept system demonstrating real-time flight control using electromyography (EMG) signals from a single arm. This research validates affordable EMG acquisition hardware for human-machine interface applications.

**Repository**: https://github.com/mr-fool/emg_drone_research

## Hardware Components

- **BioAmp EXG Pill** - 4-channel EMG acquisition module
- **Arduino Uno R4** - Signal processing and serial communication
- **Standard EMG electrodes** - Ag/AgCl surface electrodes
- **Python application** - Real-time visualization and data logging

## EMG Sensor Placement (Single Arm Configuration)

```
Right Arm EMG Sensor Placement:
                                    
    Shoulder                        
        |                           
        |   [A2] - Bicep Brachii (Pitch Control)
        |    ●●                     
    Upper Arm                       
        |    ●●                     
        |   [A3] - Tricep Brachii (Roll Control)
        |                           
    ────┴────                       
     Elbow                          
    ────┬────                       
        |                           
        |   [A1] - Forearm Extensor (Yaw Control)
        |    ●●                     
    Forearm                         
        |    ●●                     
        |   [A0] - Forearm Flexor (Throttle Control)
        |                           
    ────┴────                       
     Wrist                          
        |                           
      Hand                 
```

### Channel Mapping
- **A0 (Throttle)**: Forearm flexor muscles - Wrist flexion → Vertical movement
- **A1 (Yaw)**: Forearm extensor muscles - Wrist extension → Left/Right rotation  
- **A2 (Pitch)**: Bicep brachii - Elbow flexion → Forward/Backward movement
- **A3 (Roll)**: Tricep brachii - Elbow extension → Banking/Roll rotation

## Installation

### Arduino Setup
1. Connect BioAmp EXG Pill to Arduino Uno R4
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
- **WASD**: Pitch/Yaw control
- **Space**: Throttle (vertical movement)
- **Q/E**: Roll control
- **R**: Reset drone position
- **ESC**: Exit

### EMG Calibration
1. Launch the application with Arduino connected
2. Keep arm relaxed during initial calibration phase
3. System will automatically establish baseline values
4. Begin EMG control once calibration completes

## Research Features

### Real-Time Visualization
- Third-person drone view with 6DOF movement visualization
- Live EMG signal strength indicators
- Hardware status and signal quality monitoring
- Control input visualization with real-time feedback

### Data Collection
- Comprehensive CSV logging with timestamp precision
- Raw EMG values and processed control signals
- Drone position tracking for accuracy analysis
- Signal quality metrics for hardware validation
- Session metadata for research reproducibility

### Hardware Validation Metrics
- **Signal Acquisition Rate**: Real-time sampling frequency monitoring
- **Signal Quality Assessment**: SNR and baseline stability tracking
- **Control Latency**: Time from muscle activation to system response
- **Position Accuracy**: Precision of EMG-based positional control

## Research Applications

This platform validates EMG-based human-machine interfaces for:
- Assistive technology development
- Prosthetic device control systems
- Hands-free interface design
- Biomedical signal processing research

## Technical Specifications

### EMG Processing
- **Sampling Rate**: 500 Hz per channel
- **Signal Filtering**: Muscle-specific Butterworth filters (70-190 Hz)
- **Envelope Detection**: Real-time amplitude demodulation
- **Adaptive Thresholding**: Dynamic baseline tracking and noise rejection

### Control Mapping
- **Signal Range**: 0-1023 (10-bit ADC resolution)
- **Control Sensitivity**: Adaptive thresholding with baseline compensation
- **Update Rate**: 60 Hz visualization with 6 Hz data logging
- **Movement Constraints**: Bounded workspace for safety and repeatability

## Data Output Format

Research data is automatically saved to `data_output/emg_validation_YYYYMMDD_HHMMSS.csv`:

```csv
timestamp,throttle_raw,yaw_raw,pitch_raw,roll_raw,throttle_processed,yaw_processed,pitch_processed,roll_processed,drone_x,drone_y,drone_z,signal_quality,acquisition_rate
```

## Safety Considerations

- Use only certified medical-grade electrodes
- Ensure proper skin preparation and electrode placement
- Monitor for skin irritation during extended sessions
- Discontinue use if any discomfort occurs
- This system is for research purposes only

## License

This research platform is released under the MIT License for academic and research use.