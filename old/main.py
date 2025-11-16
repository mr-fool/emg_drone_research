import pygame
import math
import time
import csv
import os
import serial
import threading
from collections import deque

class SimplifiedEMGDemo:
    """Simplified 2-channel EMG crosshair control for HardwareX proof-of-concept"""
    
    def setup_debug_logging(self):
        """Setup comprehensive debug logging"""
        self.debug_file = open(f"data_output/debug_log_{self.session_id}.txt", 'w')
        self.debug_file.write("=== EMG Crosshair Control Debug Log ===\n")
        self.debug_file.write(f"Session ID: {self.session_id}\n")
        self.debug_file.write(f"Start Time: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        self.debug_file.write("=" * 50 + "\n\n")
        
    def log_debug_info(self, event_type, message):
        """Log debug information with timestamp"""
        if hasattr(self, 'debug_file'):
            timestamp = time.time() - self.start_time
            debug_line = f"[{timestamp:8.3f}s] {event_type:12} | {message}\n"
            self.debug_file.write(debug_line)
            self.debug_file.flush()
            print(f"DEBUG: {debug_line.strip()}")

    def __init__(self):
        pygame.init()
        self.WIDTH, self.HEIGHT = 1000, 700
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        pygame.display.set_caption("EMG Crosshair Control - HardwareX Research")
        
        # Colors
        self.WHITE = (255, 255, 255)
        self.BLACK = (0, 0, 0)
        self.GREEN = (0, 255, 0)
        self.RED = (255, 0, 0)
        self.BLUE = (0, 150, 255)
        self.YELLOW = (255, 255, 0)
        self.GRAY = (128, 128, 128)
        
        # Fonts
        self.font_large = pygame.font.Font(None, 36)
        self.font_medium = pygame.font.Font(None, 24)
        self.font_small = pygame.font.Font(None, 18)
        
        # Arduino/EMG setup (2 channels only)
        self.arduino_connected = False
        self.ser = None
        self.emg_data = [0.0, 0.0]  # left/right, up/down
        self.raw_emg = [0.0, 0.0]
        self.baseline = [0.0, 0.0]
        self.max_values = [100.0, 100.0]
        self.calibrated = False
        
        # Crosshair position and tracking
        self.crosshair_x = self.WIDTH // 2
        self.crosshair_y = self.HEIGHT // 2
        self.crosshair_size = 20  # Fixed size for simplicity
        self.target_positions = deque(maxlen=100)  # For accuracy tracking
        
        # Movement constraints
        self.crosshair_bounds = {
            'x_min': 50, 'x_max': self.WIDTH - 50,
            'y_min': 50, 'y_max': self.HEIGHT - 50
        }
        
        # Control processing
        self.control_history = deque(maxlen=300)
        self.signal_quality = "Unknown"
        
        # Hardware validation metrics
        self.start_time = time.time()
        self.last_emg_time = time.time()
        self.acquisition_rate = 0.0
        self.frame_count = 0
        self.position_accuracy = 0.0
        
        # Data logging
        self.session_id = time.strftime("%Y%m%d_%H%M%S")
        self.setup_logging()
        self.setup_debug_logging()
        self.setup_arduino()
        
    def setup_arduino(self):
        """Setup Arduino connection with debug logging"""
        arduino_ports = ['COM3', 'COM4', 'COM5', '/dev/ttyUSB0', '/dev/ttyACM0']
        
        self.log_debug_info("INIT", "Starting Arduino connection attempt")
        
        for port in arduino_ports:
            try:
                self.log_debug_info("ARDUINO", f"Attempting connection on {port}")
                self.ser = serial.Serial(port, 115200, timeout=0.1)
                time.sleep(2)
                self.arduino_connected = True
                self.log_debug_info("ARDUINO", f"Successfully connected on {port}")
                
                self.emg_thread = threading.Thread(target=self.read_emg_data, daemon=True)
                self.emg_thread.start()
                self.log_debug_info("THREAD", "EMG reading thread started")
                break
                
            except (serial.SerialException, FileNotFoundError) as e:
                self.log_debug_info("ARDUINO", f"Failed to connect on {port}: {e}")
                continue
                
        if not self.arduino_connected:
            self.log_debug_info("ARDUINO", "No Arduino found - using keyboard mode")
            
    def read_emg_data(self):
        """Read EMG data from Arduino with debug logging"""
        self.log_debug_info("EMG", "Starting EMG data reading loop")
        emg_packet_count = 0
        
        while self.arduino_connected:
            try:
                if self.ser.in_waiting > 0:
                    line = self.ser.readline().decode('utf-8').strip()
                    
                    if line.startswith('EMG,'):
                        emg_packet_count += 1
                        parts = line.split(',')
                        if len(parts) >= 6:  # Arduino sends timestamp,lr,ud,baseline_lr,baseline_ud
                            self.raw_emg = [float(parts[2]), float(parts[3])]
                            # Auto-update baseline from Arduino
                            self.baseline = [float(parts[4]), float(parts[5])]
                            self.last_emg_time = time.time()
                            self.process_emg_signals()
                            
                            if emg_packet_count % 100 == 0:
                                self.log_debug_info("EMG", f"Processed {emg_packet_count} EMG packets. Latest: {self.raw_emg}")
                        else:
                            self.log_debug_info("EMG_ERROR", f"Invalid EMG packet format: {line}")
                            
                    elif line.startswith('QUALITY,'):
                        parts = line.split(',')
                        if len(parts) >= 4:
                            self.signal_quality = parts[3]
                            self.log_debug_info("QUALITY", f"Signal quality updated: {self.signal_quality}")
                            
                    elif line.startswith('CALIBRATION_COMPLETE'):
                        self.calibrated = True
                        self.log_debug_info("CALIBRATION", "EMG calibration completed successfully")
                        
                    elif line.strip():
                        self.log_debug_info("ARDUINO_MSG", f"Unknown message: {line}")
                        
            except Exception as e:
                self.log_debug_info("EMG_ERROR", f"Error reading EMG data: {e}")
                time.sleep(0.1)
                
    def process_emg_signals(self):
        """Process raw EMG into control signals - ENHANCED FOR BETTER MOVEMENT"""
        processed = [0.0, 0.0]
        
        for i in range(2):
            # Your EMG values are very small (0.1-0.4), so we need aggressive scaling
            if self.raw_emg[i] > 0.08:  # Lower threshold for detection
                # Scale from 0.08-0.5 range to 0.0-1.0, then amplify
                normalized = (self.raw_emg[i] - 0.08) / 0.42  # 0.5 - 0.08 = 0.42
                processed[i] = min(1.0, normalized) * 3.0  # 3x amplification
            else:
                processed[i] = 0.0
        
        # Log significant control changes with lower threshold
        old_emg = getattr(self, 'emg_data', [0, 0])
        max_change = max(abs(processed[i] - old_emg[i]) for i in range(2))
        
        if max_change > 0.02:  # Even lower threshold to see activity
            self.log_debug_info("CONTROL", f"Control change: {old_emg} -> {processed}")
        
        self.emg_data = processed
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
        
        self.log_file = open(f"data_output/emg_crosshair_{self.session_id}.csv", 'w', newline='')
        writer = csv.writer(self.log_file)
        writer.writerow(['timestamp', 'left_right_raw', 'up_down_raw',
                        'left_right_processed', 'up_down_processed',
                        'crosshair_x', 'crosshair_y', 'signal_quality', 'acquisition_rate'])
        
    def get_controls(self):
        """Get control inputs from EMG or keyboard fallback"""
        if self.arduino_connected:  # Remove calibration requirement
            return self.emg_data[0], self.emg_data[1]
        else:
            # Simplified keyboard fallback - only WASD
            keys = pygame.key.get_pressed()
            left_right = -0.5 if keys[pygame.K_a] else (0.5 if keys[pygame.K_d] else 0.0)
            up_down = -0.5 if keys[pygame.K_s] else (0.5 if keys[pygame.K_w] else 0.0)
            return left_right, up_down
    
    def draw_background(self):
        """Draw sky and ground gradient background"""
        # Define colors if not already defined
        SKY_BLUE = (135, 206, 235)
        GROUND_GREEN = (34, 139, 34)
        
        # Draw sky (top half)
        for y in range(self.HEIGHT // 2):
            intensity = 1.0 - (y / (self.HEIGHT // 2)) * 0.3
            color = (
                int(SKY_BLUE[0] * intensity),
                int(SKY_BLUE[1] * intensity), 
                int(SKY_BLUE[2] * intensity)
            )
            pygame.draw.line(self.screen, color, (0, y), (self.WIDTH, y))
        
        # Draw ground (bottom half)
        for y in range(self.HEIGHT // 2, self.HEIGHT):
            progress = (y - self.HEIGHT // 2) / (self.HEIGHT // 2)
            intensity = 0.7 + (progress * 0.3)
            color = (
                int(GROUND_GREEN[0] * intensity),
                int(GROUND_GREEN[1] * intensity),
                int(GROUND_GREEN[2] * intensity)
            )
            pygame.draw.line(self.screen, color, (0, y), (self.WIDTH, y))

    def update_crosshair_position(self):
        """Update crosshair position - ENHANCED SENSITIVITY AND CLEAR MAPPING"""
        left_right, up_down = self.get_controls()
        
        # Store old position for movement tracking
        old_pos = (self.crosshair_x, self.crosshair_y)
        
        # MUCH HIGHER SENSITIVITY for small EMG signals
        sensitivity = 5.0  # Increased from 5.0 to 25.0
        
        # CLEAR MUSCLE MAPPING INSTRUCTIONS:
        # Channel 0 (A0 - Forearm flexors): Flex wrist DOWN = Move RIGHT, Relax = Move LEFT
        # Channel 1 (A1 - Forearm extensors): Extend wrist UP = Move UP, Relax = Move DOWN
        
        # Left/Right movement (Channel 0 - Wrist flexion)
        if abs(left_right) > 0.1:  # Lower threshold
            # Flex wrist (muscle tension) = move right, relax = center/left
            self.crosshair_x += left_right * sensitivity
            self.log_debug_info("MOVEMENT", f"Wrist flexion: {left_right:.3f} -> X movement")
        
        # Up/Down movement (Channel 1 - Wrist extension) 
        if abs(up_down) > 0.1:  # Lower threshold
            # Extend wrist (muscle tension) = move up, relax = center/down
            self.crosshair_y -= up_down * sensitivity  # Negative for intuitive up movement
            self.log_debug_info("MOVEMENT", f"Wrist extension: {up_down:.3f} -> Y movement")
        
        # Apply position constraints
        self.crosshair_x = max(self.crosshair_bounds['x_min'], 
                            min(self.crosshair_bounds['x_max'], self.crosshair_x))
        self.crosshair_y = max(self.crosshair_bounds['y_min'], 
                            min(self.crosshair_bounds['y_max'], self.crosshair_y))
        
        # Log significant movements
        new_pos = (self.crosshair_x, self.crosshair_y)
        movement_distance = ((new_pos[0] - old_pos[0])**2 + (new_pos[1] - old_pos[1])**2)**0.5
        
        if movement_distance > 2:  # Lower threshold to see more movement
            self.log_debug_info("MOVEMENT", f"Crosshair moved {movement_distance:.1f} pixels to {new_pos}")
        
    def draw_crosshair(self):
        """Draw EMG-controlled crosshair"""
        x, y = int(self.crosshair_x), int(self.crosshair_y)
        size = self.crosshair_size
        
        # Determine color based on control activity
        left_right, up_down = self.get_controls()
        activity_level = abs(left_right) + abs(up_down)
        
        if activity_level > 0.5:
            color = self.RED  # High activity
        elif activity_level > 0.2:
            color = self.YELLOW  # Medium activity
        else:
            color = self.GREEN  # Low/no activity
        
        # Draw simple crosshair
        pygame.draw.line(self.screen, color, 
                        (x - size, y), (x + size, y), 3)
        pygame.draw.line(self.screen, color,
                        (x, y - size), (x, y + size), 3)
        
        # Center dot
        pygame.draw.circle(self.screen, color, (x, y), 5)
        
        # Corner brackets for targeting assistance
        bracket_size = 8
        bracket_distance = size + 15
        
        corners = [
            (x - bracket_distance, y - bracket_distance),
            (x + bracket_distance, y - bracket_distance),
            (x - bracket_distance, y + bracket_distance),
            (x + bracket_distance, y + bracket_distance)
        ]
        
        for i, (corner_x, corner_y) in enumerate(corners):
            corner_x, corner_y = int(corner_x), int(corner_y)
            if i == 0:  # Top-left
                pygame.draw.line(self.screen, color, (corner_x, corner_y), (corner_x + bracket_size, corner_y), 2)
                pygame.draw.line(self.screen, color, (corner_x, corner_y), (corner_x, corner_y + bracket_size), 2)
            elif i == 1:  # Top-right
                pygame.draw.line(self.screen, color, (corner_x, corner_y), (corner_x - bracket_size, corner_y), 2)
                pygame.draw.line(self.screen, color, (corner_x, corner_y), (corner_x, corner_y + bracket_size), 2)
            elif i == 2:  # Bottom-left
                pygame.draw.line(self.screen, color, (corner_x, corner_y), (corner_x + bracket_size, corner_y), 2)
                pygame.draw.line(self.screen, color, (corner_x, corner_y), (corner_x, corner_y - bracket_size), 2)
            elif i == 3:  # Bottom-right
                pygame.draw.line(self.screen, color, (corner_x, corner_y), (corner_x - bracket_size, corner_y), 2)
                pygame.draw.line(self.screen, color, (corner_x, corner_y), (corner_x, corner_y - bracket_size), 2)
        
    def draw_control_display(self):
        """Draw real-time control input visualization"""
        left_right, up_down = self.get_controls()
        
        panel_x = 20
        panel_y = 50
        bar_width = 150
        bar_height = 20
        
        # Background panel (smaller for 2 channels)
        panel_rect = pygame.Rect(panel_x - 10, panel_y - 10, 200, 120)
        pygame.draw.rect(self.screen, (0, 0, 0, 180), panel_rect)
        pygame.draw.rect(self.screen, self.WHITE, panel_rect, 2)
        
        # Title
        title = self.font_medium.render("EMG Control Inputs", True, self.WHITE)
        self.screen.blit(title, (panel_x, panel_y - 30))
        
        controls = [
            ("Left/Right (↔)", left_right, self.GREEN),
            ("Up/Down (↕)", up_down, self.RED)
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
            if abs(value) > 0.02:
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
        status_y = 100
        
        # Status panel
        panel_rect = pygame.Rect(status_x - 10, status_y - 10, 240, 200)  # Make it taller
        pygame.draw.rect(self.screen, (0, 0, 0, 180), panel_rect)
        pygame.draw.rect(self.screen, self.WHITE, panel_rect, 2)
        
        # Title
        title = self.font_medium.render("Hardware Status", True, self.WHITE)
        self.screen.blit(title, (status_x, status_y - 30))
        
        # Connection status
        conn_color = self.GREEN if self.arduino_connected else self.RED
        conn_text = "Connected" if self.arduino_connected else "Disconnected"
        conn_display = self.font_small.render(f"Arduino: {conn_text}", True, conn_color)
        self.screen.blit(conn_display, (status_x, status_y))
        
        # EMG status - BYPASS CALIBRATION CHECK
        cal_color = self.GREEN if self.arduino_connected else self.YELLOW
        cal_text = "Active" if self.arduino_connected else "Inactive"
        cal_display = self.font_small.render(f"EMG: {cal_text}", True, cal_color)
        self.screen.blit(cal_display, (status_x, status_y + 25))
        
        # Signal quality
        quality_color = self.GREEN if self.signal_quality == "GOOD" else self.YELLOW
        quality_display = self.font_small.render(f"Quality: {self.signal_quality}", True, quality_color)
        self.screen.blit(quality_display, (status_x, status_y + 50))
        
        # Show raw EMG values for debugging
        raw_display = self.font_small.render(f"Raw EMG: [{self.raw_emg[0]:.2f}, {self.raw_emg[1]:.2f}]", True, self.WHITE)
        self.screen.blit(raw_display, (status_x, status_y + 75))
        
        # Acquisition rate
        rate_display = self.font_small.render(f"Rate: {self.acquisition_rate:.1f} Hz", True, self.WHITE)
        self.screen.blit(rate_display, (status_x, status_y + 100))
        
        # Crosshair position
        pos_display = self.font_small.render(f"Position: ({self.crosshair_x:.0f}, {self.crosshair_y:.0f})", True, self.WHITE)
        self.screen.blit(pos_display, (status_x, status_y + 125))
        
        # Session time
        session_time = time.time() - self.start_time
        time_display = self.font_small.render(f"Time: {session_time:.1f}s", True, self.WHITE)
        self.screen.blit(time_display, (status_x, status_y + 150))
        
    def draw_instructions(self):
        """Draw CLEAR muscle movement instructions - REPLACE EXISTING FUNCTION"""
        info_y = self.HEIGHT - 120
        
        # Main title
        title = self.font_large.render("EMG Crosshair Control - Enhanced Sensitivity", True, self.WHITE)
        title_rect = title.get_rect(center=(self.WIDTH // 2, 30))
        self.screen.blit(title, title_rect)
        
        # CLEAR MOVEMENT INSTRUCTIONS
        instructions = [
        "ACTUAL MUSCLE MAPPING: Channel A0 (flexors) = Constant RIGHT movement",
        "TROUBLESHOOTING: Reduce sensitivity if crosshair drifts constantly",
        "Current Issue: Only rightward movement detected - check EMG placement",
        "Controls: WASD=Keyboard | R=Reset | ESC=Exit"
     ]
   
        
        for i, instruction in enumerate(instructions):
            color = self.YELLOW if i == 0 else self.WHITE
            if "RIGHT" in instruction or "UP" in instruction:
                color = self.GREEN
            text = self.font_small.render(instruction, True, color)
            text_rect = text.get_rect(center=(self.WIDTH // 2, info_y + i * 20))
            self.screen.blit(text, text_rect)
    
    def log_data(self):
        """Log research data"""
        if hasattr(self, 'log_file'):
            timestamp = time.time() - self.start_time
            left_right, up_down = self.get_controls()
            
            writer = csv.writer(self.log_file)
            writer.writerow([
                timestamp, 
                self.raw_emg[0], self.raw_emg[1],
                left_right, up_down,
                self.crosshair_x, self.crosshair_y,
                self.signal_quality, self.acquisition_rate
            ])
            self.log_file.flush()
    
    def run(self):
        """Main demo loop"""
        clock = pygame.time.Clock()
        running = True
        
        print("=== EMG Crosshair Control Research Platform ===")
        print("Hardware: BioAmp EXG Pill + Arduino Uno R4")
        print("Research: HardwareX Proof of Concept")
        print("Session ID:", self.session_id)
        print("=" * 50)
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.log_debug_info("USER", "User requested exit via ESC key")
                        running = False
                    elif event.key == pygame.K_r:
                        self.log_debug_info("USER", "User reset crosshair position")
                        # Reset crosshair position
                        self.crosshair_x = self.WIDTH // 2
                        self.crosshair_y = self.HEIGHT // 2

            # Update crosshair position
            self.update_crosshair_position()
            
            # Render everything
            self.draw_background()  # Draw gradient background instead of solid black
            self.draw_crosshair()
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
        """Cleanup resources with debug logging"""
        self.log_debug_info("CLEANUP", "Starting cleanup process")
        
        if hasattr(self, 'log_file'):
            self.log_file.close()
            self.log_debug_info("CLEANUP", f"Data logged to: emg_crosshair_{self.session_id}.csv")
            
        if self.arduino_connected and self.ser:
            self.ser.close()
            self.log_debug_info("CLEANUP", "Arduino connection closed")
            
        if hasattr(self, 'debug_file'):
            self.log_debug_info("CLEANUP", "Debug logging session completed")
            self.debug_file.close()
            
        pygame.quit()
        print(f"Debug log saved to: debug_log_{self.session_id}.txt")

if __name__ == "__main__":
    demo = SimplifiedEMGDemo()
    demo.run()