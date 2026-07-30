import pygame
import math
import random

# --- AYARLAR ---
WIDTH = 400
HEIGHT = 700
FPS = 60

# Renkler
BLACK = (15, 15, 20)
WHITE = (255, 255, 255)
GREEN = (46, 204, 113)
RED = (231, 76, 60)
BLUE = (52, 152, 219)
YELLOW = (241, 196, 15)
CYAN = (0, 255, 255)
GRAY = (127, 140, 141)
DARK_GRAY = (50, 50, 60)
PURPLE = (155, 89, 182)
STAMINA_BLUE = (0, 120, 255)

class Game:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Saklambaç Kaçış - Backrooms")
        self.clock = pygame.time.Clock()

        self.font_gameover = pygame.font.Font("Another Danger - Demo.otf", 35)
        self.font_note = pygame.font.Font("Trash Secret DEMO.ttf", 22)

        self.font_ui = pygame.font.Font("Bad Signal.otf", 20)
        self.font_ui_small = pygame.font.Font("Bad Signal.otf", 14)
        self.font_timer = pygame.font.Font("Bad Signal.otf", 12)

        # --- GÜVENLİ TEXTURE YÜKLEME ---
        self.floor_tile = None
        self.wall_img_raw = None
        self.camera_img = None

        try:
            raw_floor = pygame.image.load("rough-cement-wall.jpg").convert()
            self.floor_tile = pygame.transform.scale(raw_floor, (100, 100))
        except Exception: pass

        try:
            raw_wall = pygame.image.load("The Backrooms Texture Wallpaper 3k in 2022 _ Textured wallpaper, Texture, Wallpaper.jpg").convert()
            self.wall_img_raw = raw_wall
        except Exception: pass

        try:
            raw_cam = pygame.image.load("78742693481413487.jpg").convert_alpha()
            self.camera_img = pygame.transform.scale(raw_cam, (30, 30))
        except Exception: pass

        # --- SESLERİN YÜKLENMESİ ---
        self.sounds_loaded = True
        try:
            self.snd_oyundayken = pygame.mixer.Sound("oyundayken.mp3")
            self.snd_canavar = pygame.mixer.Sound("canavar_gelirken.mp3")
            self.snd_kaybedince = pygame.mixer.Sound("kaybedince.mp3")
            self.snd_yurume = pygame.mixer.Sound("oyuncu_yürüme.mp3")
            self.snd_kamera = pygame.mixer.Sound("kamera.mp3")
        except Exception as e:
            print(f"Ses dosyaları yüklenirken hata oluştu: {e}")
            self.sounds_loaded = False

        self.monster_sound_playing = False
        self.walk_sound_playing = False
        self.camera_sound_playing = False

        # Oyun Durumu
        self.state = "menu"
        self.difficulty = "normal"
        self.camera_static_timer = 0
        self.game_over = False
        self.game_won = False

        # Menü Butonları
        self.btn_menu_kolay = pygame.Rect(80, HEIGHT // 2 - 60, 240, 50)
        self.btn_menu_normal = pygame.Rect(80, HEIGHT // 2 + 10, 240, 50)
        self.btn_menu_kabus = pygame.Rect(80, HEIGHT // 2 + 80, 240, 50)

        # Kontrol Tuşları (Sanal Butonlar)
        self.btn_up = pygame.Rect(160, HEIGHT - 125, 80, 55)
        self.btn_down = pygame.Rect(160, HEIGHT - 60, 80, 55)
        self.btn_left = pygame.Rect(75, HEIGHT - 92, 80, 55)
        self.btn_right = pygame.Rect(245, HEIGHT - 92, 80, 55)
        self.btn_sprint = pygame.Rect(320, HEIGHT - 140, 60, 60)

        self.btn_open_note = pygame.Rect(WIDTH // 2 - 100, HEIGHT - 200, 200, 45)

        self.moving_up = False
        self.moving_down = False
        self.moving_left = False
        self.moving_right = False
        self.is_sprinting = False

    def setup_game(self, diff):
        self.difficulty = diff
        self.player_x = 0
        self.player_y = 0
        self.player_radius = 13
        self.player_angle = 0

        # Dengeli Hızlar
        self.walk_speed = 3.6
        self.run_speed = 6.5
        self.player_speed = self.walk_speed
        
        # Stamina
        self.stamina = 100.0
        self.max_stamina = 100.0
        self.stamina_drain_rate = 0.85
        self.stamina_regen_rate = 0.65
        self.stamina_depleted = False

        self.speed_boost_timer = 0
        self.shield_timer = 0

        # --- HARİTA VE DUVARLAR ---
        self.walls = []
        self.map_size = 1400
        wall_thick = 30
        self.walls.extend([
            pygame.Rect(-self.map_size, -self.map_size, self.map_size * 2, wall_thick),
            pygame.Rect(-self.map_size, self.map_size - wall_thick, self.map_size * 2, wall_thick),
            pygame.Rect(-self.map_size, -self.map_size, wall_thick, self.map_size * 2),
            pygame.Rect(self.map_size - wall_thick, -self.map_size, wall_thick, self.map_size * 2)
        ])

        self.walls.extend([
            pygame.Rect(-250, -250, 180, 25), pygame.Rect(70, -250, 180, 25),
            pygame.Rect(-250, 225, 180, 25), pygame.Rect(70, 225, 180, 25),
            pygame.Rect(-250, -250, 25, 180), pygame.Rect(-250, 70, 25, 180),
            pygame.Rect(225, -250, 25, 180), pygame.Rect(225, 70, 25, 180),
        ])

        random.seed(42)
        for _ in range(85):
            w = random.choice([120, 200, 300, 380])
            h = 25
            rx = random.randint(-self.map_size + 50, self.map_size - 50)
            ry = random.randint(-self.map_size + 50, self.map_size - 50)
            if abs(rx) < 350 and abs(ry) < 350: continue
            if random.choice([True, False]): self.walls.append(pygame.Rect(rx, ry, w, h))
            else: self.walls.append(pygame.Rect(rx, ry, h, w))

        if diff == "kolay":
            self.base_enemy_speed = 2.0
            normal_enemy_count = 3
            ghost_enemy_count = 1
        elif diff == "normal":
            self.base_enemy_speed = 2.6
            normal_enemy_count = 5
            ghost_enemy_count = 2
        else:
            self.base_enemy_speed = 3.5
            normal_enemy_count = 7
            ghost_enemy_count = 4

        self.enemies = []
        spawn_positions = [
            (900, -900), (-900, 900), (900, 900), (-900, -900),
            (0, -1100), (1100, 0), (-1100, 0), (500, 500), (-500, -500), (0, 1100), (-700, -700)
        ]
        
        idx = 0
        for _ in range(normal_enemy_count):
            pos = spawn_positions[idx % len(spawn_positions)]
            self.enemies.append({
                "x": pos[0], "y": pos[1], 
                "speed": self.base_enemy_speed + random.uniform(-0.2, 0.2), 
                "radius": 15, "type": "normal",
                "angle": random.uniform(0, math.pi * 2), "timer": 0
            })
            idx += 1

        for _ in range(ghost_enemy_count):
            pos = spawn_positions[idx % len(spawn_positions)]
            self.enemies.append({
                "x": pos[0], "y": pos[1], 
                "speed": self.base_enemy_speed * 0.75, 
                "radius": 14, "type": "ghost",
                "angle": random.uniform(0, math.pi * 2), "timer": 0
            })
            idx += 1

        self.powerups = []
        for _ in range(5):
            while True:
                px = random.randint(-1200, 1200)
                py = random.randint(-1200, 1200)
                if not self.check_collision(px, py, 20) and math.hypot(px, py) > 200:
                    ptype = random.choice(["speed", "shield"])
                    self.powerups.append({"x": px, "y": py, "type": ptype, "radius": 12})
                    break

        self.notes = [
            {"x": 400, "y": 400, "text": "Note #1: 'Running depletes stamina. Blue speed and yellow shield power-ups save your life.'"},
            {"x": -500, "y": 600, "text": "Note #2: 'When enemies approach, the screen starts glitching - be careful!'"},
            {"x": 700, "y": -600, "text": "Note #3: 'The exit door... if you can last 2 minutes, it might appear.'"}
        ]
        self.active_note = None

        self.exit_door = None
        self.exit_spawned = False

        self.cameras = []
        if diff == "nightmare":
            for _ in range(12):
                cx = random.randint(-1000, 1000)
                cy = random.randint(-1000, 1000)
                if abs(cx) > 300 or abs(cy) > 300:
                    self.cameras.append({"x": cx, "y": cy, "range": 220})

        self.score = 0
        self.game_over = False
        self.game_won = False
        self.start_ticks = pygame.time.get_ticks()
        self.state = "game"

        # Oyundayken müziğini başlat (sonsuz döngü)
        if self.sounds_loaded:
            pygame.mixer.stop()
            self.snd_oyundayken.play(-1)

    def check_collision(self, x, y, radius):
        rect = pygame.Rect(x - radius, y - radius, radius * 2, radius * 2)
        for wall in self.walls:
            if rect.colliderect(wall): return True
        return False

    def has_line_of_sight(self, x1, y1, x2, y2):
        dist = math.hypot(x2 - x1, y2 - y1)
        if dist == 0: return True
        steps = int(dist / 12)
        if steps == 0: return True
        dx = (x2 - x1) / steps
        dy = (y2 - y1) / steps
        cx, cy = x1, y1
        for _ in range(steps):
            cx += dx
            cy += dy
            for wall in self.walls:
                if wall.collidepoint(cx, cy): return False
        return True

    def create_vignette(self, dark_level=180):
        vignette = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        max_dist = math.hypot(WIDTH // 2, HEIGHT // 2)
        for r in range(int(max_dist), int(max_dist * 0.4), -8):
            alpha = int(dark_level * ((r - max_dist * 0.4) / (max_dist * 0.6)))
            alpha = max(0, min(dark_level, alpha))
            pygame.draw.circle(vignette, (0, 0, 0, alpha), (WIDTH // 2, HEIGHT // 2), r)
        return vignette

    def draw_capcut_shaky_glitch(self, surface, intensity_factor):
        num_slices = int(2 + intensity_factor * 8)
        for _ in range(num_slices):
            strip_y = random.randint(0, HEIGHT - 15)
            strip_h = random.randint(2, 10)
            shift_x = random.randint(int(-12 * intensity_factor), int(12 * intensity_factor))
            strip_rect = pygame.Rect(0, strip_y, WIDTH, strip_h)
            try:
                sub = surface.subsurface(strip_rect).copy()
                surface.blit(sub, (shift_x, strip_y))
            except Exception:
                pass

        shift_val = int(2 + intensity_factor * 4)
        red_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        red_surf.fill((255, 0, 0, int(22 * intensity_factor)))
        surface.blit(red_surf, (shift_val, 0))
        
        blue_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        blue_surf.fill((0, 0, 255, int(22 * intensity_factor)))
        surface.blit(blue_surf, (-shift_val, 0))

        scanline_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        for y in range(0, HEIGHT, 6):
            pygame.draw.line(scanline_surf, (0, 0, 0, 35), (0, y), (WIDTH, y))
        surface.blit(scanline_scanline_surf if 'scanline_scanline_surf' in locals() else scanline_surf, (0, 0))

    def run(self):
        running = True
        vignette_nightmare = self.create_vignette(200)
        vignette_normal = self.create_vignette(110)

        while running:
            current_time = pygame.time.get_ticks()
            is_camera_alert = current_time < self.camera_static_timer

            # Kamera alarm sesi yönetimi
            if self.sounds_loaded and not self.game_over and not self.game_won:
                if is_camera_alert:
                    if not self.camera_sound_playing:
                        self.snd_kamera.play(-1)
                        self.camera_sound_playing = True
                else:
                    if self.camera_sound_playing:
                        self.snd_kamera.stop()
                        self.camera_sound_playing = False

            draw_surface = pygame.Surface((WIDTH, HEIGHT))
            draw_surface.fill(BLACK)

            # --- 1. ANA MENÜ EKRANI ---
            if self.state == "menu":
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                    elif event.type == pygame.MOUSEBUTTONDOWN:
                        pos = event.pos
                        if self.btn_menu_kolay.collidepoint(pos): self.setup_game("kolay")
                        elif self.btn_menu_normal.collidepoint(pos): self.setup_game("normal")
                        elif self.btn_menu_kabus.collidepoint(pos): self.setup_game("nightmare")

                title_font = self.font_ui
                btn_font = pygame.font.SysFont("Arial", 22, bold=True)
                title_text = title_font.render("THE BACKROOMS", True, WHITE)
                sub_text = pygame.font.SysFont("Arial", 16).render("Select Difficulty Level", True, GRAY)

                self.screen.fill(BLACK)
                self.screen.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, 120))
                self.screen.blit(sub_text, (WIDTH // 2 - sub_text.get_width() // 2, 170))

                pygame.draw.rect(self.screen, (39, 174, 96), self.btn_menu_kolay, border_radius=10)
                t_kolay = btn_font.render("EASY", True, WHITE)
                self.screen.blit(t_kolay, (self.btn_menu_kolay.centerx - t_kolay.get_width()//2, self.btn_menu_kolay.centery - t_kolay.get_height()//2))

                pygame.draw.rect(self.screen, (41, 128, 185), self.btn_menu_normal, border_radius=10)
                t_normal = btn_font.render("NORMAL", True, WHITE)
                self.screen.blit(t_normal, (self.btn_menu_normal.centerx - t_normal.get_width()//2, self.btn_menu_normal.centery - t_normal.get_height()//2))

                pygame.draw.rect(self.screen, (192, 57, 43), self.btn_menu_kabus, border_radius=10)
                t_kabus = btn_font.render("NIGHTMARE (HARD)", True, WHITE)
                self.screen.blit(t_kabus, (self.btn_menu_kabus.centerx - t_kabus.get_width()//2, self.btn_menu_kabus.centery - t_kabus.get_height()//2))

                pygame.display.flip()
                self.clock.tick(FPS)
                continue

            near_note = False
            current_nearby_note_text = None
            for note in self.notes:
                if math.hypot(self.player_x - note["x"], self.player_y - note["y"]) < 45:
                    near_note = True
                    current_nearby_note_text = note["text"]
                    break

            # --- 2. OYUN EKRANI ---
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    pos = event.pos
                    if self.game_over or self.game_won:
                        # Menüye dönerken tüm sesleri tamamen durdur
                        if self.sounds_loaded:
                            pygame.mixer.stop()
                        self.state = "menu"
                    elif self.active_note:
                        self.active_note = None
                    else:
                        if near_note and self.btn_open_note.collidepoint(pos):
                            self.active_note = current_nearby_note_text
                        elif self.btn_sprint.collidepoint(pos):
                            self.is_sprinting = True
                        else:
                            if self.btn_up.collidepoint(pos): self.moving_up = True
                            if self.btn_down.collidepoint(pos): self.moving_down = True
                            if self.btn_left.collidepoint(pos): self.moving_left = True
                            if self.btn_right.collidepoint(pos): self.moving_right = True

                elif event.type == pygame.MOUSEBUTTONUP:
                    self.is_sprinting = False
                    self.moving_up = False
                    self.moving_down = False
                    self.moving_left = False
                    self.moving_right = False

                elif event.type == pygame.KEYDOWN:
                    if (self.game_over or self.game_won) and event.key == pygame.K_r:
                        if self.sounds_loaded:
                            pygame.mixer.stop()
                        self.state = "menu"
                    if event.key == pygame.K_e:
                        if self.active_note: self.active_note = None
                        elif near_note: self.active_note = current_nearby_note_text
                    if event.key in (pygame.K_LSHIFT, pygame.K_RSHIFT):
                        self.is_sprinting = True

                elif event.type == pygame.KEYUP:
                    if event.key in (pygame.K_LSHIFT, pygame.K_RSHIFT):
                        self.is_sprinting = False

            keys = pygame.key.get_pressed()
            if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]:
                self.is_sprinting = True

            dx, dy = 0, 0
            if not self.active_note:
                if keys[pygame.K_LEFT] or self.moving_left: dx = -1
                if keys[pygame.K_RIGHT] or self.moving_right: dx = 1
                if keys[pygame.K_UP] or self.moving_up: dy = -1
                if keys[pygame.K_DOWN] or self.moving_down: dy = 1

            if dx != 0 or dy != 0:
                self.player_angle = math.atan2(dy, dx)
                
                current_base_speed = self.run_speed if (self.is_sprinting and self.stamina > 0 and not self.stamina_depleted) else self.walk_speed
                if current_time < self.speed_boost_timer:
                    current_base_speed *= 1.45

                if self.is_sprinting and not self.stamina_depleted:
                    self.stamina -= self.stamina_drain_rate
                    if self.stamina <= 0:
                        self.stamina_depleted = True
                
                mag = math.hypot(dx, dy)
                dx = (dx / mag) * current_base_speed
                dy = (dy / mag) * current_base_speed

                # Oyuncu yürüme sesi yönetimi
                if self.sounds_loaded and not self.walk_sound_playing and not self.game_over and not self.game_won:
                    self.snd_yurume.play(-1)
                    self.walk_sound_playing = True
            else:
                if self.stamina < self.max_stamina:
                    self.stamina += self.stamina_regen_rate
                    if self.stamina >= 30:
                        self.stamina_depleted = False
                
                if self.walk_sound_playing:
                    self.snd_yurume.stop()
                    self.walk_sound_playing = False

            if not self.is_sprinting and self.stamina < self.max_stamina:
                self.stamina = min(self.max_stamina, self.stamina + self.stamina_regen_rate)

            # En yakın düşmanın mesafesini bul
            min_enemy_dist = 9999
            for enemy in self.enemies:
                d = math.hypot(self.player_x - enemy["x"], self.player_y - enemy["y"])
                if d < min_enemy_dist:
                    min_enemy_dist = d

            # --- CANAVAR YAKLAŞMA SESİ YÖNETİMİ ---
            if self.sounds_loaded and not self.game_over and not self.game_won:
                if min_enemy_dist < 400:
                    vol = max(0.0, min(1.0, 1.0 - (min_enemy_dist / 400)))
                    self.snd_canavar.set_volume(vol)
                    if not self.monster_sound_playing:
                        self.snd_canavar.play(-1)
                        self.monster_sound_playing = True
                else:
                    if self.monster_sound_playing:
                        self.snd_canavar.stop()
                        self.monster_sound_playing = False

            if not self.game_over and not self.game_won:
                self.score = (current_time - self.start_ticks) // 1000

                if self.score >= 120 and not self.exit_spawned:
                    while True:
                        ex = random.randint(-1100, 1100)
                        ey = random.randint(-1100, 1100)
                        if not self.check_collision(ex, ey, 30) and math.hypot(ex, ey) > 400:
                            self.exit_door = {"x": ex, "y": ey, "radius": 25}
                            self.exit_spawned = True
                            break

                if self.exit_spawned and self.exit_door:
                    if math.hypot(self.player_x - self.exit_door["x"], self.player_y - self.exit_door["y"]) < self.player_radius + self.exit_door["radius"]:
                        self.game_won = True
                        if self.sounds_loaded:
                            pygame.mixer.stop()
                            self.snd_kaybedince.play()

                if not self.check_collision(self.player_x + dx, self.player_y, self.player_radius):
                    self.player_x += dx
                if not self.check_collision(self.player_x, self.player_y + dy, self.player_radius):
                    self.player_y += dy

                for pw in self.powerups[:]:
                    if math.hypot(self.player_x - pw["x"], self.player_y - pw["y"]) < self.player_radius + pw["radius"]:
                        if pw["type"] == "speed":
                            self.speed_boost_timer = current_time + 7000
                        elif pw["type"] == "shield":
                            self.shield_timer = current_time + 8000
                        self.powerups.remove(pw)

                if self.difficulty == "nightmare":
                    for cam in self.cameras:
                        if math.hypot(self.player_x - cam["x"], self.player_y - cam["y"]) < cam["range"]:
                            if self.has_line_of_sight(cam["x"], cam["y"], self.player_x, self.player_y):
                                self.camera_static_timer = current_time + 1200

                for enemy in self.enemies:
                    e_x, e_y = enemy["x"], enemy["y"]
                    dist_to_player = math.hypot(self.player_x - e_x, self.player_y - e_y)
                    
                    can_see = False
                    vision_limit = 500 if self.difficulty != "nightmare" else 650
                    if dist_to_player < vision_limit:
                        if self.has_line_of_sight(e_x, e_y, self.player_x, self.player_y):
                            can_see = True

                    if can_see:
                        angle_to_player = math.atan2(self.player_y - e_y, self.player_x - e_x)
                        current_speed = self.base_enemy_speed * 1.4 if (self.difficulty == "nightmare" and is_camera_alert) else self.base_enemy_speed
                        
                        if enemy["type"] == "ghost":
                            enemy["x"] += math.cos(angle_to_player) * (current_speed * 0.75)
                            enemy["y"] += math.sin(angle_to_player) * (current_speed * 0.75)
                        else:
                            nx = e_x + math.cos(angle_to_player) * current_speed
                            ny = e_y + math.sin(angle_to_player) * current_speed
                            if not self.check_collision(nx, e_y, enemy["radius"]): enemy["x"] = nx
                            if not self.check_collision(enemy["x"], ny, enemy["radius"]): enemy["y"] = ny
                    else:
                        enemy["timer"] += 1
                        if enemy["timer"] > random.randint(90, 180):
                            enemy["angle"] = random.uniform(0, math.pi * 2)
                            enemy["timer"] = 0

                        wander_speed = self.base_enemy_speed * 0.4
                        nx = e_x + math.cos(enemy["angle"]) * wander_speed
                        ny = e_y + math.sin(enemy["angle"]) * wander_speed

                        if enemy["type"] == "ghost":
                            enemy["x"] = nx
                            enemy["y"] = ny
                        else:
                            if not self.check_collision(nx, e_y, enemy["radius"]): enemy["x"] = nx
                            else: enemy["angle"] = random.uniform(0, math.pi * 2)
                            if not self.check_collision(enemy["x"], ny, enemy["radius"]): enemy["y"] = ny
                            else: enemy["angle"] = random.uniform(0, math.pi * 2)

                    if dist_to_player < self.player_radius + enemy["radius"]:
                        if current_time < self.shield_timer:
                            enemy["x"] += random.choice([-80, 80])
                            enemy["y"] += random.choice([-80, 80])
                        else:
                            if not self.game_over:
                                self.game_over = True
                                if self.sounds_loaded:
                                    pygame.mixer.stop()
                                    self.snd_kaybedince.play()

            cam_x = WIDTH // 2 - self.player_x
            cam_y = HEIGHT // 2 - self.player_y

            # --- ZEMİN ---
            if self.floor_tile:
                start_x = int((cam_x % 100) - 100)
                start_y = int((cam_y % 100) - 100)
                for x in range(start_x, WIDTH + 100, 100):
                    for y in range(start_y, HEIGHT + 100, 100):
                        draw_surface.blit(self.floor_tile, (x, y))
            else:
                draw_surface.fill(BLACK)

            # --- DUVARLAR ---
            for wall in self.walls:
                sw = wall.copy()
                sw.x += cam_x
                sw.y += cam_y
                if -300 < sw.x < WIDTH + 300 and -300 < sw.y < HEIGHT + 300:
                    if self.wall_img_raw:
                        wall_texture = pygame.transform.scale(self.wall_img_raw, (max(1, sw.width), max(1, sw.height)))
                        draw_surface.blit(wall_texture, (sw.x, sw.y))
                    else:
                        pygame.draw.rect(draw_surface, DARK_GRAY, sw)
                    pygame.draw.rect(draw_surface, (100, 90, 40), sw, 2)

            # --- GÜÇLENDİRMELER ---
            for pw in self.powerups:
                pw_sx = pw["x"] + cam_x
                pw_sy = pw["y"] + cam_y
                if -50 < pw_sx < WIDTH + 50 and -50 < pw_sy < HEIGHT + 50:
                    p_color = BLUE if pw["type"] == "speed" else YELLOW
                    pygame.draw.circle(draw_surface, p_color, (int(pw_sx), int(pw_sy)), pw["radius"])

            # --- NOTLAR ---
            for note in self.notes:
                n_sx = note["x"] + cam_x
                n_sy = note["y"] + cam_y
                if -100 < n_sx < WIDTH + 100 and -100 < n_sy < HEIGHT + 100:
                    pygame.draw.rect(draw_surface, WHITE, (int(n_sx)-8, int(n_sy)-10, 16, 20))

            # --- ÇIKIŞ ---
            if self.exit_spawned and self.exit_door:
                ex_sx = self.exit_door["x"] + cam_x
                ex_sy = self.exit_door["y"] + cam_y
                if -100 < ex_sx < WIDTH + 100 and -100 < ex_sy < HEIGHT + 100:
                    pygame.draw.rect(draw_surface, GREEN, (int(ex_sx)-15, int(ex_sy)-25, 30, 50))
                    pygame.draw.circle(draw_surface, YELLOW, (int(ex_sx)+8, int(ex_sy)), 3)

            # --- KAMERALAR ---
            if self.difficulty == "nightmare":
                for cam in self.cameras:
                    c_sx = cam["x"] + cam_x
                    c_sy = cam["y"] + cam_y
                    if -100 < c_sx < WIDTH + 100 and -100 < c_sy < HEIGHT + 100:
                        if self.camera_img:
                            draw_surface.blit(self.camera_img, (int(c_sx) - 15, int(c_sy) - 15))
                        else:
                            pygame.draw.circle(draw_surface, (100, 100, 100), (int(c_sx), int(c_sy)), 8)
                            pygame.draw.circle(draw_surface, RED, (int(c_sx), int(c_sy)), 3)

            # --- DÜŞMANLAR ---
            for enemy in self.enemies:
                e_screen_x = enemy["x"] + cam_x
                e_screen_y = enemy["y"] + cam_y
                if -100 < e_screen_x < WIDTH + 100 and -100 < e_screen_y < HEIGHT + 100:
                    if enemy["type"] == "ghost":
                        ghost_surf = pygame.Surface((30, 30), pygame.SRCALPHA)
                        pygame.draw.circle(ghost_surf, (155, 89, 182, 180), (15, 15), enemy["radius"])
                        draw_surface.blit(ghost_surf, (int(e_screen_x) - 15, int(e_screen_y) - 15))
                    else:
                        pygame.draw.circle(draw_surface, RED, (int(e_screen_x), int(e_screen_y)), enemy["radius"])

            # Oyuncu ve Kalkan
            p_draw_x = self.player_x + cam_x
            p_draw_y = self.player_y + cam_y
            pygame.draw.circle(draw_surface, BLUE, (int(p_draw_x), int(p_draw_y)), self.player_radius)
            if current_time < self.shield_timer:
                pygame.draw.circle(draw_surface, YELLOW, (int(p_draw_x), int(p_draw_y)), self.player_radius + 6, 2)

            # --- VİNYET VE DİJİTAL GLİTCH EFEKTİ ---
            if self.difficulty == "nightmare":
                draw_surface.blit(vignette_nightmare, (0, 0))
            else:
                draw_surface.blit(vignette_normal, (0, 0))

            if min_enemy_dist < 350:
                glitch_intensity = max(0.3, 1.0 - (min_enemy_dist / 350))
            else:
                glitch_intensity = 0.3

            self.draw_capcut_shaky_glitch(draw_surface, glitch_intensity)

            shake_power = int(1 + 3 * max(0.0, (1.0 - (min_enemy_dist / 300))))
            shake_x = random.randint(-shake_power, shake_power)
            shake_y = random.randint(-shake_power, shake_power)

            self.screen.fill(BLACK)
            self.screen.blit(draw_surface, (shake_x, shake_y))

            # --- MİNİ HARİTA (SAĞ ÜST) ---
            minimap_w, minimap_h = 100, 100
            minimap_surf = pygame.Surface((minimap_w, minimap_h))
            minimap_surf.fill((20, 20, 25))
            m_scale = minimap_w / (self.map_size * 2)
            
            for wall in self.walls:
                mx = int((wall.x + self.map_size) * m_scale)
                my = int((wall.y + self.map_size) * m_scale)
                mw = int(wall.width * m_scale)
                mh = int(wall.height * m_scale)
                pygame.draw.rect(minimap_surf, (80, 80, 90), (mx, my, max(1, mw), max(1, mh)))
            
            mp_x = int((self.player_x + self.map_size) * m_scale)
            mp_y = int((self.player_y + self.map_size) * m_scale)
            pygame.draw.circle(minimap_surf, CYAN, (mp_x, mp_y), 3)
            
            minimap_rect = minimap_surf.get_rect(topright=(WIDTH - 15, 15))
            self.screen.blit(minimap_surf, minimap_rect)
            pygame.draw.rect(self.screen, WHITE, minimap_rect, 2)

            if is_camera_alert:
                static_surface = pygame.Surface((WIDTH, HEIGHT))
                for _ in range(800):
                    rx = random.randint(0, WIDTH)
                    ry = random.randint(0, HEIGHT)
                    rc = random.choice([WHITE, (100, 100, 100), RED])
                    pygame.draw.rect(static_surface, rc, (rx, ry, random.randint(1, 4), random.randint(1, 3)))
                static_surface.set_alpha(170)
                self.screen.blit(static_surface, (0, 0))
                warn_font = pygame.font.SysFont("Arial", 24, bold=True)
                w_text = warn_font.render("[REC] CAMERA DETECTED YOU!", True, RED)
                self.screen.blit(w_text, (WIDTH // 2 - w_text.get_width() // 2, 80))

            # Kontrol Butonları
            pygame.draw.rect(self.screen, GRAY, self.btn_up, border_radius=8)
            pygame.draw.rect(self.screen, GRAY, self.btn_down, border_radius=8)
            pygame.draw.rect(self.screen, GRAY, self.btn_left, border_radius=8)
            pygame.draw.rect(self.screen, GRAY, self.btn_right, border_radius=8)
            
            sprint_color = (200, 50, 50) if self.stamina_depleted else (41, 128, 185)
            pygame.draw.rect(self.screen, sprint_color, self.btn_sprint, border_radius=12)
            
            font = self.font_ui
            self.screen.blit(font.render("^", True, WHITE), (self.btn_up.x + 32, self.btn_up.y + 12))
            self.screen.blit(font.render("v", True, WHITE), (self.btn_down.x + 34, self.btn_down.y + 12))
            self.screen.blit(font.render("<", True, WHITE), (self.btn_left.x + 32, self.btn_left.y + 14))
            self.screen.blit(font.render(">", True, WHITE), (self.btn_right.x + 32, self.btn_right.y + 14))
            
            sprint_txt = self.font_ui_small.render("RUN", True, WHITE)
            self.screen.blit(sprint_txt, (self.btn_sprint.centerx - sprint_txt.get_width()//2, self.btn_sprint.centery - sprint_txt.get_height()//2))

            # Stamina Barı
            pygame.draw.rect(self.screen, DARK_GRAY, (20, HEIGHT - 25, 150, 12), border_radius=5)
            current_stamina_w = int(150 * (self.stamina / self.max_stamina))
            pygame.draw.rect(self.screen, STAMINA_BLUE, (20, HEIGHT - 25, current_stamina_w, 12), border_radius=5)
            st_text = self.font_timer.render("STAMINA", True, WHITE)
            self.screen.blit(st_text, (25, HEIGHT - 42))

            score_text = font.render(f"Time: {self.score}s", True, WHITE)
            self.screen.blit(score_text, (20, 20))

            if not self.exit_spawned:
                left_time = max(0, 120 - self.score)
                exit_timer_text = font.render(f"Time till exit: {left_time}s", True, CYAN)
                self.screen.blit(exit_timer_text, (20, 50))
            else:
                exit_ready_text = font.render("EXIT DOOR LOCATED!", True, GREEN)
                self.screen.blit(exit_ready_text, (20, 50))

            if near_note and not self.active_note:
                pygame.draw.rect(self.screen, (241, 196, 15), self.btn_open_note, border_radius=8)
                btn_txt = font.render("OPEN NOTE", True, BLACK)
                self.screen.blit(btn_txt, (self.btn_open_note.centerx - btn_txt.get_width() // 2, self.btn_open_note.centery - btn_txt.get_height() // 2))

            if self.active_note:
                note_box = pygame.Surface((WIDTH - 60, 180), pygame.SRCALPHA)
                note_box.fill((30, 30, 40, 230))
                self.screen.blit(note_box, (30, HEIGHT // 2 - 90))
                
                n_font = self.font_note
                words = self.active_note.split(' ')
                line = ""
                lines = []
                for word in words:
                    test_line = line + word + " "
                    if n_font.size(test_line)[0] < WIDTH - 100:
                        line = test_line
                    else:
                        lines.append(line)
                        line = word + " "
                lines.append(line)

                for i, l in enumerate(lines):
                    rendered_line = n_font.render(l, True, WHITE)
                    self.screen.blit(rendered_line, (50, HEIGHT // 2 - 60 + (i * 25)))
                
                close_msg = n_font.render("[Tap screen to close]", True, YELLOW)
                self.screen.blit(close_msg, (WIDTH // 2 - close_msg.get_width() // 2, HEIGHT // 2 + 40))

            if self.game_over:
                overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 200))
                self.screen.blit(overlay, (0, 0))
                big_font = self.font_gameover
                go_text = big_font.render("GAME OVER!", True, RED)
                sub_text = font.render("Click to return to main menu", True, WHITE)
                self.screen.blit(go_text, (WIDTH//2 - go_text.get_width()//2, HEIGHT//2 - 50))
                self.screen.blit(sub_text, (WIDTH//2 - sub_text.get_width()//2, HEIGHT//2 + 10))

            if self.game_won:
                overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 200))
                self.screen.blit(overlay, (0, 0))
                big_font = self.font_gameover
                win_text = big_font.render("YOU WIN!", True, GREEN)
                sub_text = font.render("Click to return to main menu", True, WHITE)
                self.screen.blit(win_text, (WIDTH//2 - win_text.get_width()//2, HEIGHT//2 - 50))
                self.screen.blit(sub_text, (WIDTH//2 - sub_text.get_width()//2, HEIGHT//2 + 10))

            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()

if __name__ == "__main__":
    Game().run()