import pygame
import numpy as np
import pyaudiowpatch as pyaudio
import sys

# --- تنظیمات گرافیکی ---
WIDTH, HEIGHT = 1200, 600
FPS = 60
BG_COLOR = (10, 10, 12)
BAR_SPACING = 4
BAR_WIDTH = 1
# محاسبه تعداد بارها بر اساس عرض صفحه
NUM_BARS = (WIDTH - 40) // (BAR_WIDTH + BAR_SPACING) 

# --- تنظیمات آنالیز صدا ---
MIN_FREQ = 40      # کمی بم‌تر کردم تا بیس عمیق‌تر دیده شود
MAX_FREQ = 16000

# --- فیزیک حرکت ---
DECAY_SPEED = 12.0      
SMOOTHING = 0.4        

class ProfessionalVisualizer:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Ultimate Audio Visualizer")
        self.clock = pygame.time.Clock()
        
        # فونت‌ها
        self.font_small = pygame.font.SysFont("Arial", 10)
        self.font_bold = pygame.font.SysFont("Verdana", 12, bold=True)
        self.font_ui = pygame.font.SysFont("Consolas", 14)
        self.font_big_zones = pygame.font.SysFont("Impact", 30) # فونت برای LOW MID HIGH

        self.p = pyaudio.PyAudio()
        self.chunk_size = 2048
        self.stream = None
        
        self.current_mode = "MIC"
        self.device_index = None
        self.device_rate = 44100
        self.device_channels = 1
        self.sensitivity = 1.0 
        
        self.prev_levels = np.zeros(NUM_BARS)
        self.bar_frequencies = []
        self.fft_indices = []
        
        # منحنی وزنی متعادل
        self.weighting = np.logspace(0, 1.0, NUM_BARS) 

        self.setup_mic()

    def calculate_mapping(self):
        self.bar_frequencies = []
        self.fft_indices = []
        
        log_freqs = np.logspace(np.log10(MIN_FREQ), np.log10(MAX_FREQ), NUM_BARS + 1)
        freq_res = self.device_rate / self.chunk_size
        
        for i in range(NUM_BARS):
            start_freq = log_freqs[i]
            end_freq = log_freqs[i+1]
            center_freq = (start_freq + end_freq) / 2
            self.bar_frequencies.append(center_freq)
            
            start_idx = int(start_freq / freq_res)
            end_idx = int(end_freq / freq_res)
            if end_idx == start_idx: end_idx += 1
            self.fft_indices.append((start_idx, end_idx))

    def get_loopback_device(self):
        wasapi_info = None
        try:
            for i in range(self.p.get_host_api_count()):
                api = self.p.get_host_api_info_by_index(i)
                if "WASAPI" in api["name"]:
                    wasapi_info = api
                    break
        except: return None
        if not wasapi_info: return None
        for i in range(self.p.get_device_count()):
            dev = self.p.get_device_info_by_index(i)
            if dev["hostApi"] == wasapi_info["index"] and dev.get("isLoopbackDevice"):
                return dev
        return None

    def setup_mic(self):
        self.stop_stream()
        try:
            default_mic = self.p.get_default_input_device_info()
            self.device_index = default_mic['index']
            self.device_rate = int(default_mic['defaultSampleRate'])
            self.device_channels = 1
            self.current_mode = "MIC"
            self.sensitivity = 2.0
            self.calculate_mapping()
            self.start_stream()
        except: pass

    def setup_system(self):
        self.stop_stream()
        dev = self.get_loopback_device()
        if dev:
            self.device_index = dev['index']
            self.device_rate = int(dev['defaultSampleRate'])
            self.device_channels = dev['maxInputChannels']
            self.current_mode = "SYSTEM"
            self.sensitivity = 0.4 # پیش فرض سیستم کمتر است
            self.calculate_mapping()
            self.start_stream()
        else:
            self.current_mode = "MIC (Sys Failed)"

    def start_stream(self):
        try:
            self.stream = self.p.open(
                format=pyaudio.paInt16,
                channels=self.device_channels,
                rate=self.device_rate,
                input=True,
                input_device_index=self.device_index,
                frames_per_buffer=self.chunk_size
            )
        except: pass

    def stop_stream(self):
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None

    def toggle_mode(self):
        if "MIC" in self.current_mode: self.setup_system()
        else: self.setup_mic()

    def process_audio(self):
        if self.stream is None: return np.zeros(NUM_BARS)
        try:
            raw_data = self.stream.read(self.chunk_size, exception_on_overflow=False)
            data_int = np.frombuffer(raw_data, dtype=np.int16)
            if self.device_channels > 1: data_int = data_int[::self.device_channels]
            data_float = data_int / 32768.0
            window = np.hanning(len(data_float))
            fft_data = np.abs(np.fft.rfft(data_float * window))
            
            new_levels = np.zeros(NUM_BARS)
            for i in range(NUM_BARS):
                start, end = self.fft_indices[i]
                if start >= len(fft_data): break
                real_end = min(end, len(fft_data))
                val = np.mean(fft_data[start:real_end]) if real_end > start else fft_data[start]
                new_levels[i] = val * self.weighting[i]
            return new_levels
        except: return np.zeros(NUM_BARS)

    def get_x_for_freq(self, freq):
        """یافتن موقعیت X برای یک فرکانس خاص"""
        freq_arr = np.array(self.bar_frequencies)
        idx = (np.abs(freq_arr - freq)).argmin()
        return 20 + idx * (BAR_WIDTH + BAR_SPACING)

    def draw_grid_and_labels(self):
        line_y = HEIGHT - 50
        
        # --- 1. کشیدن خط کش و اعداد ریز ---
        pygame.draw.line(self.screen, (50, 50, 60), (20, line_y), (WIDTH-20, line_y), 1)
        target_freqs = [60, 200, 500, 1000, 2500, 5000, 10000]
        labels_str = ["60", "200", "500", "1k", "2.5k", "5k", "10k"]
        
        for tf, label in zip(target_freqs, labels_str):
            x = self.get_x_for_freq(tf) + BAR_WIDTH//2
            pygame.draw.line(self.screen, (80, 80, 80), (x, line_y), (x, line_y+8))
            text = self.font_small.render(label, True, (150, 150, 150))
            rect = text.get_rect(center=(x, line_y + 18))
            self.screen.blit(text, rect)

        # --- 2. اضافه کردن دوباره LOW / MID / HIGH ---
        # محدوده ها
        x_start = 20
        x_250 = self.get_x_for_freq(250)
        x_4k = self.get_x_for_freq(4000)
        x_end = WIDTH - 20

        # موقعیت Y برای متون بزرگ
        zone_y = HEIGHT - 25

        # LOW (Bass)
        text_low = self.font_big_zones.render("LOW", True, (40, 40, 50))
        center_low = (x_start + x_250) // 2
        self.screen.blit(text_low, text_low.get_rect(center=(center_low, zone_y)))

        # MID
        text_mid = self.font_big_zones.render("MID", True, (40, 40, 50))
        center_mid = (x_250 + x_4k) // 2
        self.screen.blit(text_mid, text_mid.get_rect(center=(center_mid, zone_y)))

        # HIGH
        text_high = self.font_big_zones.render("HIGH", True, (40, 40, 50))
        center_high = (x_4k + x_end) // 2
        self.screen.blit(text_high, text_high.get_rect(center=(center_high, zone_y)))

        # خط جداکننده نواحی (اختیاری، کمرنگ)
        pygame.draw.line(self.screen, (30, 30, 30), (x_250, line_y+10), (x_250, HEIGHT), 1)
        pygame.draw.line(self.screen, (30, 30, 30), (x_4k, line_y+10), (x_4k, HEIGHT), 1)


    def draw_ui(self):
        # دکمه
        btn_rect = pygame.Rect(10, 10, 240, 30)
        pygame.draw.rect(self.screen, (0, 100, 180), btn_rect, border_radius=5)
        
        # نمایش اطلاعات
        info = f"SOURCE: {self.current_mode} | SENS: {self.sensitivity:.2f}"
        text = self.font_ui.render(info, True, (255, 255, 255))
        self.screen.blit(text, (20, 17))
        return btn_rect

    def run(self):
        running = True
        while running:
            btn_rect = self.draw_ui()
            for event in pygame.event.get():
                if event.type == pygame.QUIT: running = False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1 and btn_rect.collidepoint(event.pos):
                        self.toggle_mode()
                if event.type == pygame.KEYDOWN:
                    # تغییر حساسیت با دقت بیشتر (0.05)
                    if event.key == pygame.K_UP: 
                        self.sensitivity += 0.05
                    elif event.key == pygame.K_DOWN: 
                        self.sensitivity = max(0.05, self.sensitivity - 0.05)

            raw_levels = self.process_audio()

            self.screen.fill(BG_COLOR)
            self.draw_grid_and_labels() # رسم گرید و لیبل‌ها قبل از بارها
            self.draw_ui()
            
            for i in range(NUM_BARS):
                # ضریب کلی را از 500 به 300 کاهش دادم
                target = raw_levels[i] * 300 * self.sensitivity
                target = np.clip(target, 0, HEIGHT - 140)
                
                if target > self.prev_levels[i]:
                    self.prev_levels[i] = (self.prev_levels[i] * SMOOTHING) + (target * (1 - SMOOTHING))
                else:
                    self.prev_levels[i] -= DECAY_SPEED
                    if self.prev_levels[i] < 0: self.prev_levels[i] = 0
                
                h = self.prev_levels[i]
                
                if h > 2:
                    x = 20 + i * (BAR_WIDTH + BAR_SPACING)
                    y = (HEIGHT - 50) - h # تنظیم موقعیت نسبت به خط کف جدید
                    
                    # رنگ‌آمیزی گرادینت
                    hue_norm = i / NUM_BARS
                    if hue_norm < 0.5:
                        r = 255
                        g = int(255 * (hue_norm * 2))
                        b = 50
                    else:
                        r = int(255 * (1 - (hue_norm - 0.5) * 2))
                        g = 255
                        b = 255
                    
                    pygame.draw.rect(self.screen, (r, min(255, g+50), b), (x, y, BAR_WIDTH, h), border_radius=2)

            pygame.display.flip()
            self.clock.tick(FPS)

        self.stop_stream()
        self.p.terminate()
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    app = ProfessionalVisualizer()
    app.run()
