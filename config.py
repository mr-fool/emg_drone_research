# EMG Research Configuration
ARDUINO_BAUD_RATE = 115200
SAMPLE_RATE_HZ = 60
DATA_LOG_INTERVAL = 10  # frames

# Display settings
WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 700

# EMG channel mapping
EMG_CHANNELS = {
    'throttle': 'A0_forearm_flexor',
    'yaw': 'A1_forearm_extensor', 
    'pitch': 'A2_bicep_brachii',
    'roll': 'A3_tricep_brachii'
}