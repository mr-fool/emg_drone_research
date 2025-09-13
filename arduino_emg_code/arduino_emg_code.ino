// EMG-Controlled Crosshair Control System - ENHANCED GAIN VERSION
// BioAmp EXG Pill - 2 Channel EMG with AGGRESSIVE AMPLIFICATION
// For HardwareX Research Paper - Enhanced for Low-Level Signals
// 
// Hardware: Arduino Uno R4 + BioAmp EXG Pill
// Single Arm EMG Sensor Configuration:
// A0: Forearm flexor muscles (wrist flexion) -> Left/Right
// A1: Forearm extensor muscles (wrist extension) -> Up/Down

#define SAMPLE_RATE 500
#define BAUD_RATE 115200
#define INPUT_PIN_LEFT_RIGHT A0   // Forearm flexor (wrist flexion)
#define INPUT_PIN_UP_DOWN A1      // Forearm extensor (wrist extension)
#define BUFFER_SIZE 64            // Smaller buffer for faster response
#define MIN_SNR 2.0               // Lower minimum SNR for sensitivity
#define CALIBRATION_SAMPLES 500   // Faster calibration
#define QUALITY_CHECK_INTERVAL 1000

// ENHANCED AMPLIFICATION PARAMETERS
#define BASELINE_ALPHA 0.98       // Slower baseline adaptation for stability
#define DYNAMIC_THRESHOLD_MULTIPLIER 1.5  // Lower threshold for easier activation
#define SIGNAL_AMPLIFICATION 50.0 // MASSIVE amplification for small signals

// Circular buffers for envelope detection
int left_right_buffer[BUFFER_SIZE];
int up_down_buffer[BUFFER_SIZE];

// Buffer indices
int left_right_index = 0;
int up_down_index = 0;

// Running sums for efficient averaging
float left_right_sum = 0;
float up_down_sum = 0;

// Adaptive baseline tracking
float baseline_left_right = 0;
float baseline_up_down = 0;

// Signal quality metrics
float left_right_variance = 0;
float up_down_variance = 0;

// Calibration state
bool is_calibrated = false;
int calibration_counter = 0;
unsigned long last_quality_check = 0;

// Peak detection for fatigue monitoring
float left_right_peak = 0;
float up_down_peak = 0;

void setup() {
  Serial.begin(BAUD_RATE);
  
  // Initialize buffers
  for(int i = 0; i < BUFFER_SIZE; i++) {
    left_right_buffer[i] = 0;
    up_down_buffer[i] = 0;
  }
  
  // Startup message
  Serial.println("EMG Crosshair Control System - ENHANCED GAIN VERSION");
  Serial.println("High Sensitivity 2-Channel EMG for Small Signals");
  Serial.println("Starting calibration phase - please relax arm muscles...");
  delay(2000);
}

void loop() {
  // Calculate elapsed time for precise sampling
  static unsigned long past = 0;
  unsigned long present = micros();
  unsigned long interval = present - past;
  past = present;

  // Sampling timer
  static long timer = 0;
  timer -= interval;

  // Sample at defined rate
  if(timer < 0) {
    timer += 1000000 / SAMPLE_RATE;

    // Read 2 EMG channels
    int left_right_raw = analogRead(INPUT_PIN_LEFT_RIGHT);
    int up_down_raw = analogRead(INPUT_PIN_UP_DOWN);

    // Apply enhanced EMG filtering
    float left_right_filtered = EMGFilter_LeftRight(left_right_raw);
    float up_down_filtered = EMGFilter_UpDown(up_down_raw);

    // Get envelope with aggressive amplification
    float left_right_envelope = getLeftRightEnvelope(abs(left_right_filtered));
    float up_down_envelope = getUpDownEnvelope(abs(up_down_filtered));

    // MASSIVE AMPLIFICATION for small signals
    left_right_envelope *= SIGNAL_AMPLIFICATION;
    up_down_envelope *= SIGNAL_AMPLIFICATION;

    // Handle calibration phase
    if (!is_calibrated) {
      updateCalibration(left_right_envelope, up_down_envelope);
      return;
    }

    // Update adaptive baselines
    updateBaselines(left_right_envelope, up_down_envelope);

    // Apply adaptive thresholding with lower threshold
    float left_right_output = applyAdaptiveThreshold(left_right_envelope, baseline_left_right);
    float up_down_output = applyAdaptiveThreshold(up_down_envelope, baseline_up_down);

    // Additional gain boost for output
    left_right_output *= 2.0;
    up_down_output *= 2.0;

    // Update peak tracking
    updatePeakTracking(left_right_output, up_down_output);

    // Periodic signal quality check
    if (millis() - last_quality_check > QUALITY_CHECK_INTERVAL) {
      checkSignalQuality();
      last_quality_check = millis();
    }

    // Send enhanced data with clear movement indicators
    sendEnhancedData(left_right_output, up_down_output);
  }
}

void updateCalibration(float lr, float ud) {
  // Accumulate baseline values during rest
  baseline_left_right += lr;
  baseline_up_down += ud;
  
  calibration_counter++;
  
  if (calibration_counter >= CALIBRATION_SAMPLES) {
    // Calculate baseline averages
    baseline_left_right /= CALIBRATION_SAMPLES;
    baseline_up_down /= CALIBRATION_SAMPLES;
    
    is_calibrated = true;
    Serial.println("CALIBRATION_COMPLETE");
    Serial.print("Enhanced Baselines: LR=");
    Serial.print(baseline_left_right);
    Serial.print(", UD=");
    Serial.println(baseline_up_down);
    Serial.println("MOVEMENT GUIDE:");
    Serial.println("- Flex wrist DOWN = Move RIGHT");
    Serial.println("- Extend wrist UP = Move UP");
    Serial.println("- Relax = Return to center");
  }
}

void updateBaselines(float lr, float ud) {
  // Very slow baseline adaptation to prevent drift
  baseline_left_right = BASELINE_ALPHA * baseline_left_right + (1 - BASELINE_ALPHA) * lr;
  baseline_up_down = BASELINE_ALPHA * baseline_up_down + (1 - BASELINE_ALPHA) * ud;
}

float applyAdaptiveThreshold(float signal, float baseline) {
  // Lower threshold for easier activation
  float threshold = baseline + (baseline * DYNAMIC_THRESHOLD_MULTIPLIER);
  float output = (signal > threshold) ? (signal - baseline) : 0;
  
  // Apply smooth scaling for better control
  if (output > 0) {
    output = sqrt(output) * 5.0;  // Square root scaling for smoother control
  }
  
  return output;
}

void updatePeakTracking(float lr, float ud) {
  // Track peak values with faster decay for responsiveness
  left_right_peak = max(left_right_peak * 0.995, lr);
  up_down_peak = max(up_down_peak * 0.995, ud);
}

void checkSignalQuality() {
  // Calculate enhanced SNRs
  float snr_left_right = calculateSNR(left_right_peak, baseline_left_right);
  float snr_up_down = calculateSNR(up_down_peak, baseline_up_down);
  
  // Send quality report
  Serial.print("QUALITY,");
  Serial.print(snr_left_right);
  Serial.print(",");
  Serial.print(snr_up_down);
  
  // Enhanced quality assessment
  if (snr_left_right < MIN_SNR || snr_up_down < MIN_SNR) {
    Serial.print(",LOW_QUALITY");
  } else {
    Serial.print(",GOOD");
  }
  Serial.println();
}

float calculateSNR(float signal_peak, float noise_baseline) {
  if (noise_baseline == 0) return 999;
  return signal_peak / noise_baseline;
}

void sendEnhancedData(float lr, float ud) {
  Serial.print("EMG,");
  Serial.print(millis());              // Timestamp
  Serial.print(",");
  Serial.print(lr, 3);                 // Left/Right (3 decimal places for precision)
  Serial.print(",");
  Serial.print(ud, 3);                 // Up/Down
  Serial.print(",");
  Serial.print(baseline_left_right, 3); // Current baselines
  Serial.print(",");
  Serial.print(baseline_up_down, 3);
  Serial.println();
  
  // Debug output for movement detection
  if (lr > 0.1 || ud > 0.1) {
    Serial.print("MOVEMENT_DETECTED,LR=");
    Serial.print(lr);
    Serial.print(",UD=");
    Serial.println(ud);
  }
}

// Enhanced envelope detection with smaller buffers for faster response
float getLeftRightEnvelope(int abs_emg) {
  left_right_sum -= left_right_buffer[left_right_index];
  left_right_sum += abs_emg;
  left_right_buffer[left_right_index] = abs_emg;
  left_right_index = (left_right_index + 1) % BUFFER_SIZE;
  return (left_right_sum / BUFFER_SIZE) * 3.0;  // Extra amplification
}

float getUpDownEnvelope(int abs_emg) {
  up_down_sum -= up_down_buffer[up_down_index];
  up_down_sum += abs_emg;
  up_down_buffer[up_down_index] = abs_emg;
  up_down_index = (up_down_index + 1) % BUFFER_SIZE;
  return (up_down_sum / BUFFER_SIZE) * 3.0;  // Extra amplification
}

// Same EMG filters as before (they're working fine)
float EMGFilter_LeftRight(float input) {
  float output = input;
  {
    static float z1, z2;
    float x = output - 0.05159732*z1 - 0.36347401*z2;
    output = 0.01856301*x + 0.03712602*z1 + 0.01856301*z2;
    z2 = z1;
    z1 = x;
  }
  {
    static float z1, z2;
    float x = output - -0.53945795*z1 - 0.39764934*z2;
    output = 1.00000000*x + -2.00000000*z1 + 1.00000000*z2;
    z2 = z1;
    z1 = x;
  }
  {
    static float z1, z2;
    float x = output - 0.47319594*z1 - 0.70744137*z2;
    output = 1.00000000*x + 2.00000000*z1 + 1.00000000*z2;
    z2 = z1;
    z1 = x;
  }
  {
    static float z1, z2;
    float x = output - -1.00211112*z1 - 0.74520226*z2;
    output = 1.00000000*x + -2.00000000*z1 + 1.00000000*z2;
    z2 = z1;
    z1 = x;
  }
  return output;
}

float EMGFilter_UpDown(float input) {
  float output = input;
  {
    static float a1, a2;
    float x = output - 0.04892389*a1 - 0.35654096*a2;
    output = 0.01947178*x + 0.03894356*a1 + 0.01947178*a2;
    a2 = a1;
    a1 = x;
  }
  {
    static float a1, a2;
    float x = output - -0.52158473*a1 - 0.40192847*a2;
    output = 1.00000000*x + -2.00000000*a1 + 1.00000000*a2;
    a2 = a1;
    a1 = x;
  }
  {
    static float a1, a2;
    float x = output - 0.45832156*a1 - 0.71245678*a2;
    output = 1.00000000*x + 2.00000000*a1 + 1.00000000*a2;
    a2 = a1;
    a1 = x;
  }
  {
    static float a1, a2;
    float x = output - -0.98754321*a1 - 0.75123456*a2;
    output = 1.00000000*x + -2.00000000*a1 + 1.00000000*a2;
    a2 = a1;
    a1 = x;
  }
  return output;
}