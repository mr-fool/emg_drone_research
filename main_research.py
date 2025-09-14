# main_research.py - Research version with clean logging
# Based on your existing main.py with research logging integration

import pygame
import math
import time
import csv
import os
import serial
import threading
from collections import deque
import statistics

class ResearchLogger:
    """Lightweight research logger for HardwareX"""
    
    def __init__(self, session_id):
        self.session_id = session_id
        self.start_time = time.time()
        
        # Create research data directory
        os.makedirs("research_data", exist_ok=True)
        
        # Simple structured logging
        self.emg_file = open(f"research_data/emg_{session_id}.csv", 'w', newline='')
        self.emg_writer = csv.writer(self.emg_file)
        self.emg_writer.writerow(['timestamp_ms', 'raw_lr', 'raw_ud', 'proc_lr', 'proc_ud', 'quality'])
        
        self.movement_file = open(f"research_data/movements_{session_id}.csv", 'w', newline='')
        self.movement_writer = csv.writer(self.movement_file)
        self.movement_writer.writerow(['timestamp_ms', 'start_x', 'start_y', 'end_x', 'end_y', 'distance', 'duration_ms'])
        
        # Movement tracking
        self.movement_start_pos = None
        self.movement_start_time = None
        self.movement_count = 0
        
    def log_emg(self, raw_emg, processed_emg, quality):
        """Log EMG data every 0.5 seconds"""
        timestamp_ms = int((time.time() - self.start_time) * 1000)
        self.emg_writer.writerow([timestamp_ms, raw_emg[0], raw_emg[1], processed_emg[0], processed_emg[1], quality])
        
    def start_movement(self, pos):
        """Track movement start"""
        if self.movement_start_pos is None:
            self.movement_start_pos = pos
            self.movement_start_time = time.time()
    
    def end_movement(self, pos):
        """Track movement end and log if significant"""
        if self.movement_start_pos is not None:
            distance = ((pos[0] - self.movement_start_pos[0])**2 + (pos[1] - self.movement_start_pos[1])**2)**0.5
            if distance > 15:  # Only log significant movements
                duration_ms = int((time.time() - self.movement_start_time) * 1000)
                timestamp_ms = int((time.time() - self.start_time) * 1000)
                
                self.movement_writer.writerow([
                    timestamp_ms, self.movement_start_pos[0], self.movement_start_pos[1],
                    pos[0], pos[1], distance, duration_ms
                ])
                self.movement_count += 1
                
            self.movement_start_pos = None
            
    def close(self):
        """Close files and print summary"""
        session_duration = time.time() - self.start_time
        self.emg_file.close()
        self.movement_file.close()
        
        print(f"\n=== RESEARCH SESSION SUMMARY ===")
        print(f"Duration: {session_duration:.1f}s")
        print(f"Movements: {self.movement_count}")
        print(f"Data saved: research_data/emg_{self.session_id}.csv")
        print(f"           research_data/movements_{self.session_id}.csv")

class SimplifiedEMGDemo:
    """Your existing EMG demo class with minimal research logging added"""
    
    def setup_debug_logging(self):
        """Replace verbose debug with research logging"""
        self.research_logger = ResearchLogger(self.session_id)
        
    def log_debug_info(self, event_type, message):
        """Simplified logging - only critical events"""
        if event_type in ["ARDUINO", "CALIBRATION", "USER"]:
            print(f"[{event_type}] {message}")

    def __init__(self):
        pygame.init()
        self.WIDTH, self.HEIGHT = 1000, 700
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        pygame.display.set_caption("EMG Crosshair Control - Research Version")
        
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
        
        # Arduino/EMG setup
        self.arduino_connected = False
        self.ser = None
        self.emg_data = [0.0, 0.0]
        self.raw_emg = [0.0, 0.0]
        self.baseline = [0.0, 0.0]
        self.calibrated = False
        
        # Crosshair position
        self.crosshair_x = self.WIDTH // 2
        self.crosshair_y = self.HEIGHT // 2
        self.crosshair_size = 20
        
        # Movement constraints
        self.crosshair_bounds = {
            'x_min': 50, 'x_max': self.WIDTH - 50,
            'y_min': 50, 'y_max': self.HEIGHT - 50
        }
        
        # Research tracking
        self.signal_quality = "Unknown"
        self.start_time = time.time()
        self.last_emg_time = time.time()
        self.acquisition_rate = 0.0
        self.frame_count = 0
        self.control_history = deque(maxlen=300)
        
        # Setup
        self.session_id = time.strftime("%Y%m%d_%H%M%S")
        self.setup_debug_logging()  # Creates research logger
        self.setup_arduino()
        
    def setup_arduino(self):
        """Setup Arduino - same as your original"""
        arduino_ports = ['COM3', 'COM4', 'COM5', '/dev/ttyUSB0', '/dev/ttyACM0']
        
        self.log_debug_info("INIT", "Starting Arduino connection")
        
        for port in arduino_ports:
            try:
                self.log_debug_info("ARDUINO", f"Connecting to {port}")
                self.ser = serial.Serial(port, 115200, timeout=0.1)
                time.sleep(2)
                self.arduino_connected = True
                self.log_debug_info("ARDUINO", f"Connected on {port}")
                
                self.emg_thread = threading.Thread(target=self.read_emg_data, daemon=True)
                self.emg_thread.start()
                break
                
            except (serial.SerialException, FileNotFoundError):
                continue
                
        if not self.arduino_connected:
            self.log_debug_info("ARDUINO", "No Arduino - keyboard mode")
            
    def read_emg_data(self):
        """Read EMG data - same as your original"""
        emg_packet_count = 0
        
        while self.arduino_connected:
            try:
                if self.ser.in_waiting > 0:
                    line = self.ser.readline().decode('utf-8').strip()
                    
                    if line.startswith('EMG,'):
                        emg_packet_count += 1
                        parts = line.split(',')
                        if len(parts) >= 6:
                            self.raw_emg = [float(parts[2]), float(parts[3])]
                            self.baseline = [float(parts[4]), float(parts[5])]
                            self.last_emg_time = time.time()
                            self.process_emg_signals()
                            
                    elif line.startswith('QUALITY,'):
                        parts = line.split(',')
                        if len(parts) >= 4:
                            self.signal_quality = parts[3]
                            
                    elif line.startswith('CALIBRATION_COMPLETE'):
                        self.calibrated = True
                        self.log_debug_info("CALIBRATION", "EMG calibrated")
                        
            except Exception as e:
                print(f"EMG Error: {e}")
                time.sleep(0.1)
                
    def process_emg_signals(self):
        """Process EMG - enhanced version from your updated code"""
        processed = [0.0, 0.0]
        
        for i in range(2):
            if self.raw_emg[i] > 0.08:
                normalized = (self.raw_emg[i] - 0.08) / 0.42
                processed[i] = min(1.0, normalized) * 3.0
            else:
                processed[i] = 0.0
        
        self.emg_data = processed
        self.calculate_acquisition_rate()
            
    def calculate_acquisition_rate(self):
        """Calculate acquisition rate"""
        current_time = time.time()
        self.control_history.append(current_time)
            
        if len(self.control_history) > 10:
            time_span = current_time - self.control_history[0]
            self.acquisition_rate = len(self.control_history) / time_span
            
    def get_controls(self):
        """Get controls - same as your original"""
        if self.arduino_connected:
            return self.emg_data[0], self.emg_data[1]
        else:
            keys = pygame.key.get_pressed()
            left_right = -0.5 if keys[pygame.K_a] else (0.5 if keys[pygame.K_d] else 0.0)
            up_down = -0.5 if keys[pygame.K_s] else (0.5 if keys[pygame.K_w] else 0.0)
            return left_right, up_down
    
    def draw_background(self):
        """Same as your original"""
        SKY_BLUE = (135, 206, 235)
        GROUND_GREEN = (34, 139, 34)
        
        for y in range(self.HEIGHT // 2):
            intensity = 1.0 - (y / (self.HEIGHT // 2)) * 0.3
            color = (int(SKY_BLUE[0] * intensity), int(SKY_BLUE[1] * intensity), int(SKY_BLUE[2] * intensity))
            pygame.draw.line(self.screen, color, (0, y), (self.WIDTH, y))
        
        for y in range(self.HEIGHT // 2, self.HEIGHT):
            progress = (y - self.HEIGHT // 2) / (self.HEIGHT // 2)
            intensity = 0.7 + (progress * 0.3)
            color = (int(GROUND_GREEN[0] * intensity), int(GROUND_GREEN[1] * intensity), int(GROUND_GREEN[2] * intensity))
            pygame.draw.line(self.screen, color, (0, y), (self.WIDTH, y))

    def update_crosshair_position(self):
        """Enhanced crosshair update with movement tracking"""
        left_right, up_down = self.get_controls()
        
        old_pos = (self.crosshair_x, self.crosshair_y)
        sensitivity = 5.0  # Enhanced sensitivity
        
        # Track movement for research
        if abs(left_right) > 0.01 or abs(up_down) > 0.01:
            self.research_logger.start_movement(old_pos)
        else:
            self.research_logger.end_movement(old_pos)
        
        # Update position
        if abs(left_right) > 0.1:
            self.crosshair_x += left_right * sensitivity
        
        if abs(up_down) > 0.1:
            self.crosshair_y -= up_down * sensitivity
        
        # Apply constraints
        self.crosshair_x = max(self.crosshair_bounds['x_min'], min(self.crosshair_bounds['x_max'], self.crosshair_x))
        self.crosshair_y = max(self.crosshair_bounds['y_min'], min(self.crosshair_bounds['y_max'], self.crosshair_y))
        
    def draw_crosshair(self):
        """Same as your original"""
        x, y = int(self.crosshair_x), int(self.crosshair_y)
        size = self.crosshair_size
        
        left_right, up_down = self.get_controls()
        activity_level = abs(left_right) + abs(up_down)
        
        if activity_level > 0.5:
            color = self.RED
        elif activity_level > 0.2:
            color = self.YELLOW
        else:
            color = self.GREEN
        
        pygame.draw.line(self.screen, color, (x - size, y), (x + size, y), 3)
        pygame.draw.line(self.screen, color, (x, y - size), (x, y + size), 3)
        pygame.draw.circle(self.screen, color, (x, y), 5)
        
    def draw_control_display(self):
        """Same as your original"""
        left_right, up_down = self.get_controls()
        
        panel_x, panel_y = 20, 50
        bar_width, bar_height = 150, 20
        
        panel_rect = pygame.Rect(panel_x - 10, panel_y - 10, 200, 120)
        pygame.draw.rect(self.screen, (0, 0, 0, 180), panel_rect)
        pygame.draw.rect(self.screen, self.WHITE, panel_rect, 2)
        
        title = self.font_medium.render("EMG Control Inputs", True, self.WHITE)
        self.screen.blit(title, (panel_x, panel_y - 30))
        
        controls = [("Left/Right", left_right, self.GREEN), ("Up/Down", up_down, self.RED)]
        
        for i, (name, value, color) in enumerate(controls):
            y_pos = panel_y + i * 40
            
            label = self.font_small.render(name, True, self.WHITE)
            self.screen.blit(label, (panel_x, y_pos))
            
            bar_rect = pygame.Rect(panel_x, y_pos + 15, bar_width, bar_height)
            pygame.draw.rect(self.screen, self.GRAY, bar_rect)
            
            if abs(value) > 0.02:
                fill_width = int(abs(value) * bar_width)
                fill_x = panel_x + bar_width // 2
                if value < 0:
                    fill_x = panel_x + bar_width // 2 - fill_width
                fill_rect = pygame.Rect(fill_x, y_pos + 15, fill_width, bar_height)
                pygame.draw.rect(self.screen, color, fill_rect)
            
            value_text = self.font_small.render(f"{value:.2f}", True, self.WHITE)
            self.screen.blit(value_text, (panel_x + bar_width + 10, y_pos + 15))
        
    def draw_hardware_status(self):
        """Simplified status display"""
        status_x = self.WIDTH - 250
        status_y = 100
        
        panel_rect = pygame.Rect(status_x - 10, status_y - 10, 240, 150)
        pygame.draw.rect(self.screen, (0, 0, 0, 180), panel_rect)
        pygame.draw.rect(self.screen, self.WHITE, panel_rect, 2)
        
        title = self.font_medium.render("System Status", True, self.WHITE)
        self.screen.blit(title, (status_x, status_y - 30))
        
        # Connection status
        conn_color = self.GREEN if self.arduino_connected else self.RED
        conn_text = "Connected" if self.arduino_connected else "Disconnected"
        conn_display = self.font_small.render(f"Arduino: {conn_text}", True, conn_color)
        self.screen.blit(conn_display, (status_x, status_y))
        
        # Signal quality
        quality_color = self.GREEN if self.signal_quality == "GOOD" else self.YELLOW
        quality_display = self.font_small.render(f"Quality: {self.signal_quality}", True, quality_color)
        self.screen.blit(quality_display, (status_x, status_y + 25))
        
        # Movements tracked
        movements = self.research_logger.movement_count
        move_display = self.font_small.render(f"Movements: {movements}", True, self.WHITE)
        self.screen.blit(move_display, (status_x, status_y + 50))
        
        # Session time
        session_time = time.time() - self.start_time
        time_display = self.font_small.render(f"Time: {session_time:.1f}s", True, self.WHITE)
        self.screen.blit(time_display, (status_x, status_y + 75))
        
    def draw_instructions(self):
        """Research version instructions"""
        info_y = self.HEIGHT - 120
        
        title = self.font_large.render("EMG Research - HardwareX Study", True, self.WHITE)
        title_rect = title.get_rect(center=(self.WIDTH // 2, 30))
        self.screen.blit(title, title_rect)
        
        instructions = [
            "ACTUAL MUSCLE MAPPING: Channel A0 (flexors) = Constant RIGHT movement",
            "TROUBLESHOOTING: Reduce sensitivity if crosshair drifts constantly",
            "Current Issue: Only rightward movement detected - check EMG placement",
            "Controls: WASD=Keyboard | R=Reset | ESC=Exit"
        ]
        
        for i, instruction in enumerate(instructions):
            color = self.YELLOW if "Research" in instruction else self.WHITE
            text = self.font_small.render(instruction, True, color)
            text_rect = text.get_rect(center=(self.WIDTH // 2, info_y + i * 20))
            self.screen.blit(text, text_rect)
    
    def log_research_data(self):
        """Log research data every 0.5 seconds"""
        if self.frame_count % 30 == 0:  # Every 0.5s at 60fps
            left_right, up_down = self.get_controls()
            self.research_logger.log_emg(self.raw_emg, [left_right, up_down], self.signal_quality)
    
    def run(self):
        """Main loop - same structure as your original"""
        clock = pygame.time.Clock()
        running = True
        
        print("=== EMG Research Session Started ===")
        print(f"Session ID: {self.session_id}")
        print("Data will be saved to research_data/ folder")
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.log_debug_info("USER", "Exit requested")
                        running = False
                    elif event.key == pygame.K_r:
                        self.crosshair_x = self.WIDTH // 2
                        self.crosshair_y = self.HEIGHT // 2

            self.update_crosshair_position()
            
            self.draw_background()
            self.draw_crosshair()
            self.draw_control_display()
            self.draw_hardware_status()
            self.draw_instructions()
            
            # Research logging
            self.frame_count += 1
            self.log_research_data()
            
            pygame.display.flip()
            clock.tick(60)
        
        self.cleanup()
        
    def cleanup(self):
        """Enhanced cleanup with research summary"""
        self.research_logger.close()
        
        if self.arduino_connected and self.ser:
            self.ser.close()
            
        pygame.quit()

if __name__ == "__main__":
    demo = SimplifiedEMGDemo()
    demo.run()