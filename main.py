import pygame
import math
import time
import csv
import os
import serial
import threading
from collections import deque

class IntegratedEMGDemo:
    """EMG control demonstration integrated with Arduino BioAmp system"""
    
    def __init__(self):
        pygame.init()
        self.WIDTH, self.HEIGHT = 1000, 700
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        pygame.display.set_caption("EMG Control Research Platform - HardwareX")
        
        # Colors
        self.WHITE = (255, 255, 255)
        self.BLACK = (0, 0, 0)
        self.BLUE = (0, 100, 255)
        self.RED = (255, 0, 0)
        self.GREEN = (0, 255, 0)
        self.YELLOW = (255, 255, 0)
        self.GRAY = (128, 128, 128)
        
        # Fonts
        self.font_large = pygame.font.Font(None, 36)
        self.font_medium = pygame.font.Font(None, 24)
        self.font_small = pygame.font.Font(None, 18)
        
        # Arduino/EMG setup
        self.arduino_connected = False
        self.ser = None
        self.emg_data = [0.0, 0.0, 0.0, 0.0]  # throttle, yaw, pitch, roll
        self.raw_emg = [0.0, 0.0, 0.0, 0.0]
        self.baseline = [0.0, 0.0, 0.0, 0.0]
        self.max_values = [100.0, 100.0, 100.0, 100.0]
        self.calibrated = False
        
        # Control processing
        self.control_history = deque(maxlen=300)  # 5 seconds at 60 FPS
        self.signal_quality = "Unknown"
        
        # Drone representation
        self.drone_x = self.WIDTH // 2
        self.drone_y = self.HEIGHT // 2
        self.drone_z = 0
        self.drone_roll = 0
        self.drone_size = 50
        
        # Movement constraints
        self.movement_bounds = {
            'x_min': 100, 'x_max': self.WIDTH - 100,
            'y_min': 100, 'y_max': self.HEIGHT - 200,
            'z_min': -50, 'z_max': 50
        }
        
        # Hardware validation metrics
        self.start_time = time.time()
        self.last_emg_time = time.time()
        self.control_latency = 0.0
        self.acquisition_rate = 0.0
        self.frame_count = 0
        
        # Data logging
        self.session_id = time.strftime("%Y%m%d_%H%M%S")
        self.setup_logging()
        self.setup_arduino()
        
    def setup_arduino(self):
        """Setup Arduino connection"""
        arduino_ports = ['COM3', 'COM4', 'COM5', '/dev/ttyUSB0', '/dev/ttyACM0']
        
        for port in arduino_ports:
            try:
                self.ser = serial.Serial(port, 115200, timeout=0.1)
                time.sleep(2)  # Arduino reset time
                self.arduino_connected = True
                print(f"Arduino connected on {port}")
                
                # Start EMG reading thread
                self.emg_thread = threading.Thread(target=self.read_emg_data, daemon=True)
                self.emg_thread.start()
                break
                
            except (serial.SerialException, FileNotFoundError):
                continue
                
        if not self.arduino_connected:
            print("Arduino not found. Using keyboard controls.")
            
    def read_emg_data(self):
        """Read EMG data from Arduino in separate thread"""
        while self.arduino_connected:
            try:
                if self.ser.in_waiting > 0:
                    line = self.ser.readline().decode('utf-8').strip()
                    
                    if line.startswith('EMG,'):
                        # Parse: EMG,timestamp,throttle,yaw,pitch,roll,baseline_data...
                        parts = line.split(',')
                        if len(parts) >= 6:
                            self.raw_emg = [float(parts[2]), float(parts[3]), 
                                          float(parts[4]), float(parts[5])]
                            self.last_emg_time = time.time()
                            self.process_emg_signals()
                            
                    elif line.startswith('QUALITY,'):
                        # Parse signal quality data
                        parts = line.split(',')
                        if len(parts) >= 6:
                            self.signal_quality = parts[5]
                            
                    elif line.startswith('CALIBRATION_COMPLETE'):
                        self.calibrated = True
                        print("EMG calibration completed")
                        
            except Exception as e:
                print(f"EMG read error: {e}")
                time.sleep(0.1)
                
    def process_emg_signals(self):
        """Process raw EMG into control signals"""
        processed = [0.0, 0.0, 0.0, 0.0]
        
        for i in range(4):
            # Simple baseline subtraction and normalization
            if self.calibrated:
                baseline_corrected = max(0, self.raw_emg[i] - self.baseline[i])
                range_val = self.max_values[i] - self.baseline[i]
                if range_val > 0:
                    processed[i] = min(1.0, baseline_corrected / range_val)
            else:
                # Basic thresholding during calibration
                processed[i] = max(0, min(1.0, (self.raw_emg[i] - 20) / 80))
        
        self.emg_data = processed
        
        # Calculate metrics
        self.calculate_acquisition_rate()
        
    def calculate_acquisition_rate(self):
        """Calculate EMG signal acquisition rate"""
        current_time = time.time()
        self.control_history.append(current_time)
        
        if len(self.control_history) > 10:
            time_span = current_time - self.control_history[0]
            self.acquisition_rate = len(self.control_history) / time_span
            
    def setup_logging(self):
        """Setup comprehensive data logging"""
        os.makedirs("data_output", exist_ok=True)
        
        # Main data log
        self.log_file = open(f"data_output/emg_validation_{self.session_id}.csv", 'w', newline='')
        writer = csv.writer(self.log_file)
        writer.writerow(['timestamp', 'throttle_raw', 'yaw_raw', 'pitch_raw', 'roll_raw',
                        'throttle_processed', 'yaw_processed', 'pitch_processed', 'roll_processed',
                        'drone_x', 'drone_y', 'drone_z', 'signal_quality', 'acquisition_rate'])
        
    def get_controls(self):
        """Get control inputs from EMG or keyboard fallback"""
        if self.arduino_connected and self.calibrated:
            return self.emg_data[0], self.emg_data[1], self.emg_data[2], self.emg_data[3]
        else:
            # Keyboard fallback
            keys = pygame.key.get_pressed()
            throttle = 0.7 if keys[pygame.K_SPACE] else 0.0
            yaw = -0.5 if keys[pygame.K_a] else (0.5 if keys[pygame.K_d] else 0.0)
            pitch = -0.5 if keys[pygame.K_s] else (0.5 if keys[pygame.K_w] else 0.0)
            roll = -0.5 if keys[pygame.K_q] else (0.5 if keys[pygame.K_e] else 0.0)
            return throttle, yaw, pitch, roll
            
    def update_drone_position(self):
        """Update drone position based on controls"""
        throttle, yaw, pitch, roll = self.get_controls()
        
        # Movement parameters
        speed = 2.0
        
        # Vertical movement (throttle)
        if throttle > 0.1:
            self.drone_y -= speed * throttle
        else:
            self.drone_y += speed * 0.3  # Gentle descent
            
        # Horizontal movement (yaw)
        self.drone_x += yaw * speed
        
        # Depth movement (pitch)
        self.drone_z += pitch * speed
        
        # Roll for visual effect
        self.drone_roll = roll * 25
        
        # Apply movement constraints
        self.drone_x = max(self.movement_bounds['x_min'], 
                          min(self.movement_bounds['x_max'], self.drone_x))
        self.drone_y = max(self.movement_bounds['y_min'], 
                          min(self.movement_bounds['y_max'], self.drone_y))
        self.drone_z = max(self.movement_bounds['z_min'], 
                          min(self.movement_bounds['z_max'], self.drone_z))
        
    def draw_drone(self):
        """Draw drone with 3D perspective effect"""
        # Calculate size based on Z position
        size_factor = 1.0 + (self.drone_z * 0.02)
        current_size = int(self.drone_size * size_factor)
        
        # Main body (rotated square)
        body_points = []
        for i in range(4):
            angle = (i * 90) + self.drone_roll
            x = self.drone_x + math.cos(math.radians(angle)) * current_size / 2
            y = self.drone_y + math.sin(math.radians(angle)) * current_size / 2
            body_points.append((x, y))
        
        pygame.draw.polygon(self.screen, self.BLUE, body_points)
        pygame.draw.polygon(self.screen, self.WHITE, body_points, 3)
        
        # Propellers
        prop_size = max(8, current_size // 4)
        for i in range(4):
            angle = i * 90
            prop_x = self.drone_x + math.cos(math.radians(angle)) * current_size * 0.6
            prop_y = self.drone_y + math.sin(math.radians(angle)) * current_size * 0.6
            pygame.draw.circle(self.screen, self.RED, (int(prop_x), int(prop_y)), prop_size)
        
        # Center marker
        pygame.draw.circle(self.screen, self.YELLOW, (int(self.drone_x), int(self.drone_y)), 6)
        
        # Z-position indicator (shadow)
        shadow_offset = int(self.drone_z * 0.5)
        shadow_pos = (int(self.drone_x + shadow_offset), int(self.drone_y + shadow_offset))
        pygame.draw.circle(self.screen, self.GRAY, shadow_pos, current_size // 3)
        
    def draw_control_display(self):
        """Draw real-time control input visualization"""
        throttle, yaw, pitch, roll = self.get_controls()
        
        panel_x = 20
        panel_y = 50
        bar_width = 150
        bar_height = 20
        
        # Background panel
        panel_rect = pygame.Rect(panel_x - 10, panel_y - 10, 200, 200)
        pygame.draw.rect(self.screen, (0, 0, 0, 128), panel_rect)
        pygame.draw.rect(self.screen, self.WHITE, panel_rect, 2)
        
        # Title
        title = self.font_medium.render("EMG Control Inputs", True, self.WHITE)
        self.screen.blit(title, (panel_x, panel_y - 30))
        
        controls = [
            ("Throttle", throttle, self.GREEN),
            ("Yaw", yaw, self.RED),
            ("Pitch", pitch, self.BLUE),
            ("Roll", roll, self.YELLOW)
        ]
        
        for i, (name, value, color) in enumerate(controls):
            y_pos = panel_y + i * 40
            
            # Label
            label = self.font_small.render(name, True, self.WHITE)
            self.screen.blit(label, (panel_x, y_pos))
            
            # Bar background
            bar_rect = pygame.Rect(panel_x, y_pos + 15, bar_width, bar_height)
            pygame.draw.rect(self.screen, self.GRAY, bar_rect)
            
            # Bar fill
            if abs(value) > 0.05:
                fill_width = int(abs(value) * bar_width)
                fill_x = panel_x + bar_width // 2
                if value < 0:
                    fill_x = panel_x + bar_width // 2 - fill_width
                fill_rect = pygame.Rect(fill_x, y_pos + 15, fill_width, bar_height)
                pygame.draw.rect(self.screen, color, fill_rect)
            
            # Value text
            value_text = self.font_small.render(f"{value:.2f}", True, self.WHITE)
            self.screen.blit(value_text, (panel_x + bar_width + 10, y_pos + 15))
        
    def draw_hardware_status(self):
        """Draw hardware and signal quality information"""
        status_x = self.WIDTH - 250
        status_y = 50
        
        # Status panel
        panel_rect = pygame.Rect(status_x - 10, status_y - 10, 240, 150)
        pygame.draw.rect(self.screen, (0, 0, 0, 128), panel_rect)
        pygame.draw.rect(self.screen, self.WHITE, panel_rect, 2)
        
        # Title
        title = self.font_medium.render("Hardware Status", True, self.WHITE)
        self.screen.blit(title, (status_x, status_y - 30))
        
        # Connection status
        conn_color = self.GREEN if self.arduino_connected else self.RED
        conn_text = "Connected" if self.arduino_connected else "Disconnected"
        conn_display = self.font_small.render(f"Arduino: {conn_text}", True, conn_color)
        self.screen.blit(conn_display, (status_x, status_y))
        
        # Calibration status
        cal_color = self.GREEN if self.calibrated else self.YELLOW
        cal_text = "Calibrated" if self.calibrated else "Calibrating..."
        cal_display = self.font_small.render(f"EMG: {cal_text}", True, cal_color)
        self.screen.blit(cal_display, (status_x, status_y + 25))
        
        # Signal quality
        quality_color = self.GREEN if self.signal_quality == "GOOD" else self.YELLOW
        quality_display = self.font_small.render(f"Quality: {self.signal_quality}", True, quality_color)
        self.screen.blit(quality_display, (status_x, status_y + 50))
        
        # Acquisition rate
        rate_display = self.font_small.render(f"Rate: {self.acquisition_rate:.1f} Hz", True, self.WHITE)
        self.screen.blit(rate_display, (status_x, status_y + 75))
        
        # Session time
        session_time = time.time() - self.start_time
        time_display = self.font_small.render(f"Time: {session_time:.1f}s", True, self.WHITE)
        self.screen.blit(time_display, (status_x, status_y + 100))
        
    def draw_instructions(self):
        """Draw control instructions and research information"""
        info_y = self.HEIGHT - 100
        
        # Main title
        title = self.font_large.render("EMG Flight Control Research Platform", True, self.WHITE)
        title_rect = title.get_rect(center=(self.WIDTH // 2, 30))
        self.screen.blit(title, title_rect)
        
        # Instructions
        instructions = [
            "Hardware: BioAmp EXG Pill + Arduino Uno R4 | Publication: HardwareX",
            "EMG Mapping: Forearm Flexor→Throttle | Forearm Extensor→Yaw | Bicep→Pitch | Tricep→Roll",
            "Keyboard Fallback: WASD=Pitch/Yaw | Space=Throttle | QE=Roll | ESC=Exit"
        ]
        
        for i, instruction in enumerate(instructions):
            text = self.font_small.render(instruction, True, self.WHITE)
            text_rect = text.get_rect(center=(self.WIDTH // 2, info_y + i * 20))
            self.screen.blit(text, text_rect)
    
    def log_data(self):
        """Log research data"""
        if hasattr(self, 'log_file'):
            timestamp = time.time() - self.start_time
            throttle, yaw, pitch, roll = self.get_controls()
            
            writer = csv.writer(self.log_file)
            writer.writerow([
                timestamp, 
                self.raw_emg[0], self.raw_emg[1], self.raw_emg[2], self.raw_emg[3],
                throttle, yaw, pitch, roll,
                self.drone_x, self.drone_y, self.drone_z,
                self.signal_quality, self.acquisition_rate
            ])
            self.log_file.flush()
    
    def run(self):
        """Main demo loop"""
        clock = pygame.time.Clock()
        running = True
        
        print("=== EMG Flight Control Research Platform ===")
        print("Hardware: BioAmp EXG Pill + Arduino Uno R4")
        print("Publication: HardwareX Proof of Concept")
        print("Session ID:", self.session_id)
        print("=" * 50)
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_r:
                        # Reset drone position
                        self.drone_x = self.WIDTH // 2
                        self.drone_y = self.HEIGHT // 2
                        self.drone_z = 0
                        self.drone_roll = 0
            
            # Update drone position
            self.update_drone_position()
            
            # Render everything
            self.screen.fill(self.BLACK)
            self.draw_drone()
            self.draw_control_display()
            self.draw_hardware_status()
            self.draw_instructions()
            
            # Log data every 10 frames (6 Hz)
            self.frame_count += 1
            if self.frame_count % 10 == 0:
                self.log_data()
            
            pygame.display.flip()
            clock.tick(60)
        
        # Cleanup
        self.cleanup()
        
    def cleanup(self):
        """Cleanup resources"""
        if hasattr(self, 'log_file'):
            self.log_file.close()
            print(f"Data logged to: emg_validation_{self.session_id}.csv")
            
        if self.arduino_connected and self.ser:
            self.ser.close()
            print("Arduino connection closed")
            
        pygame.quit()
        print("EMG research session completed")

if __name__ == "__main__":
    demo = IntegratedEMGDemo()
    demo.run()