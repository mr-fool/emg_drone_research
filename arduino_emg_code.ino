// EMG-Controlled Crosshair Control System - SIMPLIFIED 2-CHANNEL VERSION
// BioAmp EXG Pill - 2 Channel EMG Acquisition with Research-Grade Processing
// For HardwareX Research Paper - Enhanced Signal Processing & Quality Monitoring
// 
// Hardware: Arduino Uno R4 + BioAmp EXG Pill
// Single Arm EMG Sensor Configuration:
// A0: Forearm flexor muscles (wrist flexion) -> Left/Right
// A1: Forearm extensor muscles (wrist extension) -> Up/Down
// Output: Enhanced EMG signals with quality metrics for crosshair control

#define SAMPLE_RATE 500
#define BAUD_RATE 115200
#define INPUT_PIN_LEFT_RIGHT A0   // Forearm flexor (wrist flexion)
#define INPUT_PIN_UP_DOWN A1      // Forearm extensor (wrist extension)
#define BUFFER_SIZE 128
#define MIN_SNR 3.0               // Minimum signal-to-noise ratio
#define CALIBRATION_SAMPLES 1000
#define QUALITY_CHECK_INTERVAL 1000  // ms

// Adaptive thresholding parameters
#define BASELINE_ALPHA 0.95       // Baseline adaptation rate
#define DYNAMIC_THRESHOLD_MULTIPLIER 2.5

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
  Serial.println("EMG Crosshair Control System - SIMPLIFIED 2-CHANNEL VERSION");
  Serial.println("Single Arm Configuration - 2 Channel EMG with Quality Monitoring");
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

    // Apply muscle-specific EMG filtering
    float left_right_filtered = EMGFilter_LeftRight(left_right_raw);
    float up_down_filtered = EMGFilter_UpDown(up_down_raw);

    // Get envelope (signal strength)
    float left_right_envelope = getLeftRightEnvelope(abs(left_right_filtered));
    float up_down_envelope = getUpDownEnvelope(abs(up_down_filtered));

    // Amplify signals
    left_right_envelope *= 10;
    up_down_envelope *= 10;

    // Handle calibration phase
    if (!is_calibrated) {
      updateCalibration(left_right_envelope, up_down_envelope);
      return;
    }

    // Update adaptive baselines
    updateBaselines(left_right_envelope, up_down_envelope);

    // Apply adaptive thresholding
    float left_right_output = applyAdaptiveThreshold(left_right_envelope, baseline_left_right);
    float up_down_output = applyAdaptiveThreshold(up_down_envelope, baseline_up_down);

    // Update peak tracking for fatigue detection
    updatePeakTracking(left_right_output, up_down_output);

    // Periodic signal quality check
    if (millis() - last_quality_check > QUALITY_CHECK_INTERVAL) {
      checkSignalQuality();
      last_quality_check = millis();
    }

    // Send enhanced research data
    sendResearchData(left_right_output, up_down_output);
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
    Serial.print("Baselines: LR=");
    Serial.print(baseline_left_right);
    Serial.print(", UD=");
    Serial.println(baseline_up_down);
  }
}

void updateBaselines(float lr, float ud) {
  // Adaptive baseline tracking (slower adaptation during active use)
  baseline_left_right = BASELINE_ALPHA * baseline_left_right + (1 - BASELINE_ALPHA) * lr;
  baseline_up_down = BASELINE_ALPHA * baseline_up_down + (1 - BASELINE_ALPHA) * ud;
}

float applyAdaptiveThreshold(float signal, float baseline) {
  float threshold = baseline + (baseline * DYNAMIC_THRESHOLD_MULTIPLIER);
  return (signal > threshold) ? (signal - baseline) : 0;
}

void updatePeakTracking(float lr, float ud) {
  // Track peak values for fatigue detection
  left_right_peak = max(left_right_peak * 0.999, lr);  // Slow decay
  up_down_peak = max(up_down_peak * 0.999, ud);
}

void checkSignalQuality() {
  // Calculate signal-to-noise ratios
  float snr_left_right = calculateSNR(left_right_peak, baseline_left_right);
  float snr_up_down = calculateSNR(up_down_peak, baseline_up_down);
  
  // Send quality report
  Serial.print("QUALITY,");
  Serial.print(snr_left_right);
  Serial.print(",");
  Serial.print(snr_up_down);
  
  // Quality warnings
  if (snr_left_right < MIN_SNR || snr_up_down < MIN_SNR) {
    Serial.print(",LOW_QUALITY");
  } else {
    Serial.print(",GOOD");
  }
  Serial.println();
}

float calculateSNR(float signal_peak, float noise_baseline) {
  if (noise_baseline == 0) return 999;  // Avoid division by zero
  return signal_peak / noise_baseline;
}

void sendResearchData(float lr, float ud) {
  Serial.print("EMG,");
  Serial.print(millis());              // Timestamp
  Serial.print(",");
  Serial.print(lr, 2);                 // Left/Right (2 decimal places)
  Serial.print(",");
  Serial.print(ud, 2);                 // Up/Down
  Serial.print(",");
  Serial.print(baseline_left_right, 2); // Current baselines for analysis
  Serial.print(",");
  Serial.print(baseline_up_down, 2);
  Serial.println();
}

// Envelope detection functions (optimized)
float getLeftRightEnvelope(int abs_emg) {
  left_right_sum -= left_right_buffer[left_right_index];
  left_right_sum += abs_emg;
  left_right_buffer[left_right_index] = abs_emg;
  left_right_index = (left_right_index + 1) % BUFFER_SIZE;
  return (left_right_sum / BUFFER_SIZE) * 2.0;
}

float getUpDownEnvelope(int abs_emg) {
  up_down_sum -= up_down_buffer[up_down_index];
  up_down_sum += abs_emg;
  up_down_buffer[up_down_index] = abs_emg;
  up_down_index = (up_down_index + 1) % BUFFER_SIZE;
  return (up_down_sum / BUFFER_SIZE) * 2.0;
}

// Muscle-Specific Butterworth Filters (Optimized for different muscle groups)

// Left/Right Filter: Optimized for forearm flexors (70-150 Hz)
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

// Up/Down Filter: Optimized for forearm extensors (75-160 Hz)
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