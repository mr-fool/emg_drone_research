// EMG-Controlled Vertical Crosshair Control - SINGLE CHANNEL
// BioAmp EXG Pill - 1 Channel EMG for Up/Down Movement
// For HardwareX Research Paper - Single-Channel Configuration
// 
// Hardware: Arduino Uno R4 + BioAmp EXG Pill (1-channel mode)
// Single Channel EMG Sensor Configuration:
// A0: Forearm muscle (wrist flexion/extension) -> Up/Down movement
// Bidirectional control: Strong flex = UP, Relax = CENTER, Strong extend = DOWN

#define SAMPLE_RATE 500
#define BAUD_RATE 115200
#define INPUT_PIN A0              // Single channel for vertical control
#define BUFFER_SIZE 64            
#define MIN_SNR 2.0               
#define CALIBRATION_SAMPLES 500   
#define QUALITY_CHECK_INTERVAL 1000

// SINGLE CHANNEL PARAMETERS
#define BASELINE_ALPHA 0.98       
#define DYNAMIC_THRESHOLD_MULTIPLIER 1.3
#define SIGNAL_AMPLIFICATION 20.0 

// Circular buffer for envelope detection
int signal_buffer[BUFFER_SIZE];
int buffer_index = 0;
float signal_sum = 0;

// Adaptive baseline tracking
float baseline = 0;
float noise_floor = 0;

// Calibration state
bool is_calibrated = false;
int calibration_counter = 0;
unsigned long last_quality_check = 0;

// Peak detection
float signal_peak = 0;

void setup() {
  Serial.begin(BAUD_RATE);
  
  // Initialize buffer
  for(int i = 0; i < BUFFER_SIZE; i++) {
    signal_buffer[i] = 0;
  }
  
  // Startup message
  Serial.println("EMG Vertical Control System - SINGLE CHANNEL");
  Serial.println("1-Channel EMG for Up/Down Movement");
  Serial.println("ELECTRODE PLACEMENT:");
  Serial.println("Channel A0: Forearm muscle (ulnar nerve area)");
  Serial.println("Reference: Bony part of wrist or hand");
  Serial.println("Starting calibration - relax arm muscles...");
  delay(3000);
}

void loop() {
  static unsigned long past = 0;
  unsigned long present = micros();
  unsigned long interval = present - past;
  past = present;

  static long timer = 0;
  timer -= interval;

  if(timer < 0) {
    timer += 1000000 / SAMPLE_RATE;

    // Read single EMG channel
    int raw = analogRead(INPUT_PIN);

    // Apply EMG filtering
    float filtered = EMGFilter(raw);

    // Get envelope with amplification
    float envelope = getEnvelope(abs(filtered));
    envelope *= SIGNAL_AMPLIFICATION;

    // Handle calibration phase
    if (!is_calibrated) {
      updateCalibration(envelope);
      return;
    }

    // Update adaptive baseline
    updateBaseline(envelope);

    // Apply adaptive thresholding for vertical movement
    float vertical_output = applyAdaptiveThreshold(envelope);

    // Update peak tracking
    updatePeakTracking(vertical_output);

    // Periodic signal quality check
    if (millis() - last_quality_check > QUALITY_CHECK_INTERVAL) {
      checkSignalQuality();
      last_quality_check = millis();
    }

    // Send vertical control data
    sendData(vertical_output);
  }
}

void updateCalibration(float signal) {
  baseline += signal;
  calibration_counter++;
  
  // Progress indicator
  if (calibration_counter % 100 == 0) {
    Serial.print("Calibration progress: ");
    Serial.print((calibration_counter * 100) / CALIBRATION_SAMPLES);
    Serial.println("%");
  }
  
  if (calibration_counter >= CALIBRATION_SAMPLES) {
    baseline /= CALIBRATION_SAMPLES;
    noise_floor = baseline * 1.1;
    
    is_calibrated = true;
    Serial.println("CALIBRATION_COMPLETE");
    Serial.print("Baseline: ");
    Serial.print(baseline);
    Serial.print(", Noise floor: ");
    Serial.println(noise_floor);
    Serial.println("");
    Serial.println("VERTICAL CONTROL MAPPING:");
    Serial.println("- Strong muscle contraction = Move UP");
    Serial.println("- Relax = Return to CENTER");
    Serial.println("- Very relaxed = Drift DOWN");
  }
}

void updateBaseline(float signal) {
  baseline = BASELINE_ALPHA * baseline + (1 - BASELINE_ALPHA) * signal;
}

float applyAdaptiveThreshold(float signal) {
  float threshold = max(baseline + (baseline * DYNAMIC_THRESHOLD_MULTIPLIER), noise_floor);
  float output = (signal > threshold) ? (signal - baseline) : 0;
  
  // Apply smooth scaling for better control
  if (output > 0) {
    output = sqrt(output) * 4.0;  // Scaled for vertical sensitivity
  }
  
  return output;
}

void updatePeakTracking(float signal) {
  signal_peak = max(signal_peak * 0.995, signal);
}

void checkSignalQuality() {
  float snr = calculateSNR(signal_peak, baseline);
  
  Serial.print("QUALITY,");
  Serial.print(snr);
  
  if (snr < MIN_SNR) {
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

void sendData(float vertical) {
  Serial.print("EMG,");
  Serial.print(millis());           // Timestamp
  Serial.print(",");
  Serial.print(vertical, 3);        // Vertical movement value
  Serial.print(",");
  Serial.print(baseline, 3);        // Current baseline
  Serial.println();
  
  // Debug output for movement detection
  if (vertical > 0.1) {
    Serial.print("MOVEMENT_UP,");
    Serial.println(vertical);
  }
}

float getEnvelope(int abs_emg) {
  signal_sum -= signal_buffer[buffer_index];
  signal_sum += abs_emg;
  signal_buffer[buffer_index] = abs_emg;
  buffer_index = (buffer_index + 1) % BUFFER_SIZE;
  return (signal_sum / BUFFER_SIZE) * 2.5;
}

// EMG filter optimized for single channel
float EMGFilter(float input) {
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