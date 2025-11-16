# main_vertical.py - Single-channel vertical control for research
# Optimized for 1-channel EMG with up/down movement only

import pygame
import time
import csv
import os
import serial
import threading
from collections import deque

class ResearchLogger:
    """Research logger for single-channel vertical control"""
    
    def __init__(self, session_id):
        self.session_id = session_id
        self.start_time = time.time()
        
        os.makedirs("research_data", exist_ok=True)
        
        self.emg_file = open(f"research_data/emg_vertical_{session_id}.csv", 'w', newline='')
        self.emg_writer = csv.writer(self.emg_file)
        self.emg_writer.writerow(['timestamp_ms', 'raw_vertical', 'proc_vertical', 'quality'])
        
        self.movement_file = open(f"research_data/movements_vertical_{session_id}.csv", 'w', newline='')
        self.movement_writer = csv.writer(self.movement_file)
        self.movement_writer.writerow(['timestamp_ms', 'start_y', 'end_y', 'distance', 'duration_ms'])
        
        self.movement_start_y = None
        self.movement_start_time = None
        self.movement_count = 0
        
    def log_emg(self, raw_vertical, processed_vertical, quality):
        timestamp_ms = int((time.time() - self.start_time) * 1000)
        self.emg_writer.writerow([timestamp_ms, raw_vertical, processed_vertical, quality])
        
    def start_movement(self, y_pos):
        if self.movement_start_y is None:
            self.movement_start_y = y_pos
            self.movement_start_time = time.time()
    
    def end_movement(self, y_pos):
        if self.movement_start_y is not None:
            distance = abs(y_pos - self.movement_start_y)
            if distance > 15:
                duration_ms = int((time.time() - self.movement_start_time) * 1000)
                timestamp_ms = int((time.time() - self.start_time) * 1000)
                
                self.movement_writer.writerow([
                    timestamp_ms, self.movement_start_y, y_pos, distance, duration_ms
                ])
                self.movement_count += 1
                
            self.movement_start_y = None
            
    def close(self):
        session_duration = time.time() - self.start_time
        self.emg_file.close()
        self.movement_file.close()
        
        print(f"\n=== RESEARCH SESSION SUMMARY ===")
        print(f"Duration: {session_duration:.1f}s")
        print(f"Vertical Movements: {self.movement_count}")
        print(f"Data saved: research_data/emg_vertical_{self.session_id}.csv")
        print(f"           research_data/movements_vertical_{self.session_id}.csv")

class VerticalEMGControl:
    """Single-channel EMG for vertical crosshair control"""
    
    def __init__(self):
        pygame.init()
        self.WIDTH, self.HEIGHT = 1000, 700
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        pygame.display.set_caption("EMG Vertical Control - Single Channel Research")
        
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
        self.emg_vertical = 0.0
        self.raw_vertical = 0.0
        self.baseline = 0.0
        self.calibrated = False
        
        # Crosshair position - CENTERED HORIZONTALLY, moves vertically only
        self.crosshair_x = self.WIDTH // 2  # Fixed horizontal position
        self.crosshair_y = self.HEIGHT // 2
        self.crosshair_size = 20
        
        # Movement constraints
        self.crosshair_bounds = {
            'y_min': 50, 
            'y_max': self.HEIGHT - 50
        }
        
        # Research tracking
        self.signal_quality = "Unknown"
        self.start_time = time.time()
        self.last_emg_time = time.time()
        self.frame_count = 0
        
        # Setup
        self.session_id = time.strftime("%Y%m%d_%H%M%S")
        self.research_logger = ResearchLogger(self.session_id)
        self.setup_arduino()
        
    def setup_arduino(self):
        arduino_ports = ['COM3', 'COM4', 'COM5', '/dev/ttyUSB0', '/dev/ttyACM0']
        
        print("Starting Arduino connection...")
        
        for port in arduino_ports:
            try:
                print(f"Trying {port}...")
                self.ser = serial.Serial(port, 115200, timeout=0.1)
                time.sleep(2)
                self.arduino_connected = True
                print(f"Connected to Arduino on {port}")
                
                self.emg_thread = threading.Thread(target=self.read_emg_data, daemon=True)
                self.emg_thread.start()
                break
                
            except (serial.SerialException, FileNotFoundError):
                continue
                
        if not self.arduino_connected:
            print("No Arduino detected - keyboard mode (W/S for up/down)")
            
    def read_emg_data(self):
        while self.arduino_connected:
            try:
                if self.ser.in_waiting > 0:
                    line = self.ser.readline().decode('utf-8').strip()
                    
                    if line.startswith('EMG,'):
                        parts = line.split(',')
                        if len(parts) >= 4:
                            self.raw_vertical = float(parts[2])
                            self.baseline = float(parts[3])
                            self.last_emg_time = time.time()
                            self.process_emg_signal()
                            
                    elif line.startswith('QUALITY,'):
                        parts = line.split(',')
                        if len(parts) >= 3:
                            self.signal_quality = parts[2]
                            
                    elif line.startswith('CALIBRATION_COMPLETE'):
                        self.calibrated = True
                        print("EMG calibrated - ready for vertical control")
                        
            except Exception as e:
                print(f"EMG Error: {e}")
                time.sleep(0.1)
                
    def process_emg_signal(self):
        """Process vertical EMG signal"""
        if self.raw_vertical > 0.08:
            normalized = (self.raw_vertical - 0.08) / 0.42
            self.emg_vertical = min(1.0, normalized) * 3.0
        else:
            self.emg_vertical = 0.0
            
    def get_vertical_control(self):
        """Get vertical control value"""
        if self.arduino_connected:
            return self.emg_vertical
        else:
            # Keyboard fallback
            keys = pygame.key.get_pressed()
            return -0.5 if keys[pygame.K_s] else (0.5 if keys[pygame.K_w] else 0.0)
    
    def draw_background(self):
        """Draw sky and ground"""
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
        """Update vertical crosshair position only"""
        vertical = self.get_vertical_control()
        
        old_y = self.crosshair_y
        sensitivity = 6.0
        
        # Track movement
        if abs(vertical) > 0.01:
            self.research_logger.start_movement(old_y)
        else:
            self.research_logger.end_movement(old_y)
        
        # Update vertical position only
        if abs(vertical) > 0.1:
            self.crosshair_y -= vertical * sensitivity  # Negative because screen Y increases downward
        
        # Apply vertical constraints
        self.crosshair_y = max(self.crosshair_bounds['y_min'], 
                              min(self.crosshair_bounds['y_max'], self.crosshair_y))
        
    def draw_crosshair(self):
        """Draw vertical crosshair with activity indication"""
        x, y = int(self.crosshair_x), int(self.crosshair_y)
        size = self.crosshair_size
        
        vertical = self.get_vertical_control()
        activity_level = abs(vertical)
        
        if activity_level > 0.5:
            color = self.RED
        elif activity_level > 0.2:
            color = self.YELLOW
        else:
            color = self.GREEN
        
        # Vertical line emphasis
        pygame.draw.line(self.screen, color, (x, y - size*2), (x, y + size*2), 4)
        pygame.draw.line(self.screen, color, (x - size, y), (x + size, y), 3)
        pygame.draw.circle(self.screen, color, (x, y), 6)
        
    def draw_control_display(self):
        """Display vertical control bar"""
        panel_x, panel_y = 20, 50
        bar_width, bar_height = 30, 200
        
        panel_rect = pygame.Rect(panel_x - 10, panel_y - 10, 80, 240)
        pygame.draw.rect(self.screen, (0, 0, 0, 180), panel_rect)
        pygame.draw.rect(self.screen, self.WHITE, panel_rect, 2)
        
        title = self.font_medium.render("Vertical", True, self.WHITE)
        self.screen.blit(title, (panel_x - 5, panel_y - 30))
        
        # Vertical bar
        bar_rect = pygame.Rect(panel_x, panel_y, bar_width, bar_height)
        pygame.draw.rect(self.screen, self.GRAY, bar_rect)
        
        vertical = self.get_vertical_control()
        if abs(vertical) > 0.02:
            fill_height = int(abs(vertical) * bar_height / 2)
            fill_y = panel_y + bar_height // 2
            if vertical > 0:  # Up movement
                fill_y = panel_y + bar_height // 2 - fill_height
            fill_rect = pygame.Rect(panel_x, fill_y, bar_width, fill_height)
            pygame.draw.rect(self.screen, self.BLUE, fill_rect)
        
        # Value text
        value_text = self.font_small.render(f"{vertical:.2f}", True, self.WHITE)
        self.screen.blit(value_text, (panel_x - 5, panel_y + bar_height + 10))
        
        # Direction indicator
        if vertical > 0.1:
            dir_text = self.font_small.render("UP", True, self.GREEN)
            self.screen.blit(dir_text, (panel_x + 5, panel_y - 50))
        elif vertical < -0.1:
            dir_text = self.font_small.render("DOWN", True, self.RED)
            self.screen.blit(dir_text, (panel_x, panel_y - 50))
        
    def draw_hardware_status(self):
        """Display system status"""
        status_x = self.WIDTH - 250
        status_y = 100
        
        panel_rect = pygame.Rect(status_x - 10, status_y - 10, 240, 150)
        pygame.draw.rect(self.screen, (0, 0, 0, 180), panel_rect)
        pygame.draw.rect(self.screen, self.WHITE, panel_rect, 2)
        
        title = self.font_medium.render("System Status", True, self.WHITE)
        self.screen.blit(title, (status_x, status_y - 30))
        
        # Connection
        conn_color = self.GREEN if self.arduino_connected else self.RED
        conn_text = "Connected" if self.arduino_connected else "Keyboard Mode"
        conn_display = self.font_small.render(f"Arduino: {conn_text}", True, conn_color)
        self.screen.blit(conn_display, (status_x, status_y))
        
        # Signal quality
        quality_color = self.GREEN if self.signal_quality == "GOOD" else self.YELLOW
        quality_display = self.font_small.render(f"Quality: {self.signal_quality}", True, quality_color)
        self.screen.blit(quality_display, (status_x, status_y + 25))
        
        # Movements
        movements = self.research_logger.movement_count
        move_display = self.font_small.render(f"Movements: {movements}", True, self.WHITE)
        self.screen.blit(move_display, (status_x, status_y + 50))
        
        # Session time
        session_time = time.time() - self.start_time
        time_display = self.font_small.render(f"Time: {session_time:.1f}s", True, self.WHITE)
        self.screen.blit(time_display, (status_x, status_y + 75))
        
        # Channel config
        config_display = self.font_small.render("Mode: 1-Channel", True, self.BLUE)
        self.screen.blit(config_display, (status_x, status_y + 100))
        
    def draw_instructions(self):
        """Display instructions"""
        info_y = self.HEIGHT - 100
        
        title = self.font_large.render("Single-Channel Vertical EMG Control", True, self.WHITE)
        title_rect = title.get_rect(center=(self.WIDTH // 2, 30))
        self.screen.blit(title, title_rect)
        
        instructions = [
            "Contract forearm muscle to move crosshair UP",
            "Relax muscle to return to CENTER",
            "1-Channel Configuration | W/S=Keyboard | R=Reset | ESC=Exit"
        ]
        
        for i, instruction in enumerate(instructions):
            text = self.font_small.render(instruction, True, self.WHITE)
            text_rect = text.get_rect(center=(self.WIDTH // 2, info_y + i * 20))
            self.screen.blit(text, text_rect)
    
    def log_research_data(self):
        """Log research data"""
        if self.frame_count % 30 == 0:
            vertical = self.get_vertical_control()
            self.research_logger.log_emg(self.raw_vertical, vertical, self.signal_quality)
    
    def run(self):
        """Main loop"""
        clock = pygame.time.Clock()
        running = True
        
        print("=== Single-Channel Vertical EMG Control Started ===")
        print(f"Session ID: {self.session_id}")
        print("Crosshair moves UP/DOWN only")
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_r:
                        self.crosshair_y = self.HEIGHT // 2

            self.update_crosshair_position()
            
            self.draw_background()
            self.draw_crosshair()
            self.draw_control_display()
            self.draw_hardware_status()
            self.draw_instructions()
            
            self.frame_count += 1
            self.log_research_data()
            
            pygame.display.flip()
            clock.tick(60)
        
        self.cleanup()
        
    def cleanup(self):
        """Cleanup"""
        self.research_logger.close()
        
        if self.arduino_connected and self.ser:
            self.ser.close()
            
        pygame.quit()

if __name__ == "__main__":
    demo = VerticalEMGControl()
    demo.run()