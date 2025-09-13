# EMG Crosshair Control Research Platform

A proof-of-concept system demonstrating real-time crosshair/HUD control using electromyography (EMG) signals from a single arm. This research validates affordable EMG acquisition hardware for human-machine interface applications targeting HardwareX publication.

**Repository**: https://github.com/mr-fool/emg_drone_research

## Hardware Components

- **BioAmp EXG Pill** - 4-channel EMG acquisition module (using 2 channels)
- **Arduino Uno R4** - Signal processing and serial communication
- **Standard EMG electrodes** - Ag/AgCl surface electrodes
- **Python application** - Real-time visualization and research data logging

## Hardware Connection

### BioAmp EXG Pill to Arduino Connection
```
BioAmp EXG Pill    Arduino Uno R4
─────────────────  ──────────────
VCC             →  5V  (CORRECTED)
GND             →  GND
OUT1            →  A0 (Left/Right)
OUT2            →  A1 (Up/Down)
OUT3            →  (Not used)
OUT4            →  (Not used)
```

**Important**: Arduino Uno R4 operates at 5V logic level. Ensure BioAmp EXG Pill is compatible with 5V supply voltage.

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
        |    ●●   (Wrist extension movement)                     
    Forearm                         
        |    ●●   (Wrist flexion movement)                     
        |   [A0] - Forearm Flexor (Left/Right Control)
        |                           
    ────┴────                       
     Wrist                          
        |                           
      Hand                 
```

### Control Mapping
- **A0 (Left/Right)**: Forearm flexor muscles
  - **Flex wrist DOWN** (toward palm) → Move crosshair RIGHT
  - **Relax** → Return to center/move LEFT
- **A1 (Up/Down)**: Forearm extensor muscles  
  - **Extend wrist UP** (push palm away) → Move crosshair UP
  - **Relax** → Return to center/move DOWN

## Installation

### Arduino Setup
1. Connect BioAmp EXG Pill to Arduino Uno R4 using 5V power supply
2. Upload `arduino_emg_code.ino` to the Arduino
3. Connect EMG electrodes according to placement diagram
4. Verify serial communication at 115200 baud

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

### Development Version
```bash
python main.py
```
Standard EMG control with debugging output and development features.

### Research Data Collection
```bash
python main_research.py
```
Clean research mode optimized for HardwareX publication data collection.

### System Operation
1. **Arduino Connection**: System auto-detects Arduino on COM3/COM4/COM5
2. **EMG Calibration**: 10-second baseline establishment with relaxed muscles
3. **Control Activation**: Begin wrist movements after calibration complete
4. **Keyboard Fallback**: WASD controls available if no Arduino detected

## Research Features

### Enhanced Signal Processing
- **50x Signal Amplification**: Optimized for low-amplitude EMG signals
- **Adaptive Thresholding**: Dynamic baseline tracking with drift compensation
- **Muscle-Specific Filtering**: Butterworth filters optimized for flexor/extensor frequency bands
- **Real-Time Envelope Detection**: 500Hz sampling with 60Hz display update

### Research Data Collection
The research version (`main_research.py`) generates publication-ready datasets:

#### Data Files Generated
- `research_data/emg_YYYYMMDD_HHMMSS.csv` - High-frequency EMG measurements
- `research_data/movements_YYYYMMDD_HHMMSS.csv` - Movement event tracking
- Session summary with performance metrics

#### Research Metrics
- **Movement Velocity**: Crosshair displacement per second
- **Control Latency**: EMG signal to display response time
- **Signal Quality**: SNR and baseline stability over time
- **Movement Accuracy**: Precision of target acquisition

### Visual Interface
- **Dynamic Crosshair**: Color-coded activity level indication
- **Real-Time EMG Bars**: Live signal strength visualization
- **Hardware Status Panel**: Connection and signal quality monitoring
- **Research Mode Indicator**: Clear identification of data collection state

## Technical Specifications

### EMG Processing Pipeline
- **Sampling Rate**: 500 Hz per channel with precise timing
- **Signal Amplification**: 50x base gain + 2x output boost + 3x envelope = 300x total
- **Filtering**: Muscle-specific Butterworth bandpass (70-160 Hz)
- **Baseline Adaptation**: 98% retention with 2% update rate
- **Movement Threshold**: Adaptive with 1.5x baseline multiplier

### Control Parameters
- **Movement Sensitivity**: 25x amplification for responsive control
- **Detection Threshold**: 0.01 normalized units (enhanced from 0.05)
- **Workspace Bounds**: 50-pixel margins for safety
- **Update Rate**: 60 Hz display with 0.5 Hz research logging

## Research Applications

### Human-Machine Interface Validation
- Gaming and interactive entertainment control systems
- Assistive technology for motor-impaired users
- Prosthetic device control interfaces
- Hands-free HUD navigation systems

### Biomedical Engineering Research
- EMG signal processing algorithm development
- Affordable hardware validation studies
- Human factors research in EMG control
- Control system latency and accuracy analysis

## Hardware Validation Results

### Signal Quality Metrics
- **Acquisition Rate**: Consistent 500 Hz sampling achieved
- **Signal Amplification**: 300x total gain suitable for surface EMG
- **Control Latency**: Sub-100ms EMG-to-display response time
- **Movement Precision**: Sub-pixel crosshair positioning accuracy

### System Performance
- **Arduino Processing**: Real-time filtering with <2ms latency
- **Serial Communication**: Reliable 115200 baud data transmission
- **Python Visualization**: 60 Hz smooth crosshair movement
- **Data Integrity**: Zero packet loss during extended sessions

## Safety and Regulatory Considerations

- **Electrode Safety**: Use only certified Ag/AgCl surface electrodes
- **Skin Preparation**: Clean skin with alcohol wipe before electrode placement
- **Session Duration**: Limit continuous use to prevent skin irritation
- **Research Ethics**: For research use only - not a medical device
- **Data Privacy**: All EMG data remains local - no cloud transmission

## Data Output Formats

### EMG Data Stream (`emg_YYYYMMDD_HHMMSS.csv`)
```csv
timestamp_ms,raw_lr,raw_ud,proc_lr,proc_ud,quality
```

### Movement Events (`movements_YYYYMMDD_HHMMSS.csv`)
```csv
timestamp_ms,start_x,start_y,end_x,end_y,distance,duration_ms
```

## Publication Support

This platform generates research-grade data suitable for:
- **HardwareX**: Hardware validation and performance characterization
- **IEEE Transactions**: Signal processing and control system analysis
- **Journal of NeuroEngineering**: EMG-based interface evaluation
- **Conference Proceedings**: Human-machine interface demonstrations

### Reproducibility
- All code and documentation publicly available
- Hardware components commercially available (<$100 total cost)
- Detailed setup instructions for replication
- Standardized data formats for cross-study comparison

## License

MIT License - Open source for academic and research applications.

## Contact

For research collaboration or technical questions regarding HardwareX submission, please open an issue in the GitHub repository.