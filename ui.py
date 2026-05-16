#ui py citymind
import pygame
import sys
import math
import os
from city_graph import CityGraph

BASE_DIR = os.path.dirname(__file__)
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

#constants
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 800
SIDEBAR_WIDTH = 300
#colors
#backgrounds
COL_BG              = (8,   10,  14)
COL_SIDEBAR         = (11,  14,  18)
COL_SIDEBAR_DEEP    = (8,   10,  12)
COL_TOPBAR          = (9,   11,  16)
COL_CARD            = (14,  18,  24)
COL_CARD_HOVER      = (20,  26,  34)
#borders
COL_BORDER          = (38,  48,  62)
COL_BORDER_GOLD     = (90,  68,  28)
COL_BORDER_BRIGHT   = (120, 95,  40)
#gold palette
COL_GOLD_DIM        = (120, 90,  35)
COL_GOLD            = (180, 138, 55)
COL_GOLD_BRIGHT     = (218, 170, 75)
COL_GOLD_SHINE      = (240, 200, 110)
COL_TEXT_PRIMARY    = (200, 185, 155)
COL_TEXT_DIM        = (100, 88,  65)
COL_TEXT_GHOST      = (50,  44,  32)
#status colors
COL_SUCCESS         = (60,  130, 70)
COL_SUCCESS_TEXT    = (100, 180, 110)
COL_WARNING         = (160, 100, 30)
COL_WARNING_TEXT    = (220, 155, 60)
COL_DANGER          = (130, 35,  35)
COL_DANGER_TEXT     = (200, 80,  80)
#map area
COL_MAP_BG          = (16,  20,  14)
#original colors
COLOR_ROAD          = (80, 85, 95)
COLOR_ROAD_MST      = (140, 200, 130)
COLOR_ROAD_BLOCKED  = (220, 50, 60)
COLOR_ACCENT        = (0, 255, 200)
SIDEBAR_W  = 270
TOPBAR_H   = 60
MAP_X      = SIDEBAR_W
MAP_Y      = TOPBAR_H
MAP_W      = SCREEN_WIDTH  - SIDEBAR_W
MAP_H      = SCREEN_HEIGHT - TOPBAR_H
TYPE_COLORS = {
    "Residential":   (75,  180,  90),
    "Hospital":      (230,  50,  80),
    "School":        (60,  130, 220),
    "Industrial":    (170, 140, 110),
    "PowerPlant":    (255, 190,   0),
    "AmbulanceDepot": (240, 140, 50),
}
BTN_CSP      = (40,  200, 120)
BTN_MST      = (60,  130, 220)
BTN_GA       = (160, 100, 240)
BTN_ROUTING  = (230, 140, 60)
BTN_RANDOM_ROUTING = (255, 165, 0)
BTN_AMBULANCE_SIM = (0, 200, 100)
BTN_ML       = (220,  80, 160)#challenge 5 crime
BTN_FLOOD    = (200,  40,  60)
BTN_RESET    = (120, 120, 140)
#overlay modes
OVERLAY_ROAD      = "road"#road view
OVERLAY_AMBULANCE = "ambulance"#ambulance view
OVERLAY_CRIME     = "crime"#crime view
COLOR_AMBULANCE_HALO = (160, 100, 240, 60)#purple halo
import os

def _load_font(name, size, bold=False):
    path = os.path.join(ASSETS_DIR, name)
    try:
        return pygame.font.Font(path, size)
    except:
        fallbacks = ["Segoe UI", "Georgia", "Arial"]
        for fb in fallbacks:
            try:
                return pygame.font.SysFont(fb, size, bold=bold)
            except:
                pass
        return pygame.font.SysFont(None, size, bold=bold)

class Camera:

    def __init__(self):
        self.x = 0
        self.y = 0
        self.zoom = 1.0
        self.min_zoom = 0.3
        self.max_zoom = 3.0

    def world_to_screen(self, wx, wy):
        cx = SIDEBAR_W + MAP_W // 2
        cy = TOPBAR_H + MAP_H // 2
        sx = (wx - self.x) * self.zoom + cx
        sy = (wy - self.y) * self.zoom + cy
        return sx, sy

    def screen_to_world(self, sx, sy):
        cx = SIDEBAR_W + MAP_W // 2
        cy = TOPBAR_H + MAP_H // 2
        wx = (sx - cx) / self.zoom + self.x
        wy = (sy - cy) / self.zoom + self.y
        return wx, wy

class CityMapUI:

    def __init__(self, city_graph):
        pygame.init()
        try:
            pygame.mixer.init()
            self.audio_enabled = True
        except Exception:
            self.audio_enabled = False
        self.city = city_graph
        self.display = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
        self.screen = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("CityMind | Interactive Urban Map")
        self.camera = Camera()
        #center camera
        self.camera.x = city_graph.GRID_SIZE * 60 / 2
        self.camera.y = city_graph.GRID_SIZE * 60 / 2
        #fonts
        self.font_title   = _load_font("Cinzel-Regular.ttf", 22)
        self.font_heading = _load_font("Cinzel-Regular.ttf", 15)
        self.font_body    = _load_font("IMFellEnglish-Regular.ttf", 17)
        self.font_value   = _load_font("IMFellEnglish-Regular.ttf", 23)
        self.font_small   = _load_font("IMFellEnglish-Regular.ttf", 15)
        self.font_tiny    = _load_font("IMFellEnglish-Regular.ttf", 13)
        self.clock = pygame.time.Clock()
        self.panning       = False
        self.last_mouse_pos = (0, 0)
        self.flooded       = False
        self.hovered_node  = None
        self.hovered_btn   = None
        self.btn_running   = None
        self.csp_done = False
        self.mst_done = False
        self.ga_done  = False
        self.routing_done = False
        self.ml_done  = False#challenge 5
        #overlay modes
        self.overlay_mode = OVERLAY_ROAD#road view
        #animation state
        self.ambulance_animating = False
        self.anim_route_index = 0#current segment
        self.anim_progress = 0.0#progress 0 to
        self.anim_speed = 0.02#speed per frame
        self.anim_current_pos = None#current position
        self.rescued_civilians = set()#civilians reached
        self.event_log = ["CityMind initialized."]
        self.node_spacing = 90#world units
        #load assets
        self.assets = {}
        import os

        for b_type in ["Hospital", "Residential", "School", "Industrial", "PowerPlant", "Tree", "AmbulanceDepot"]:
            img_path = os.path.join(ASSETS_DIR, f"{b_type.lower()}.png")
            try:
                img = pygame.image.load(img_path).convert_alpha()
                self.assets[b_type] = pygame.transform.scale(img, (64, 64))
            except Exception:
                self.assets[b_type] = None
        self.ambulance_sprite = None
        amb_path = os.path.join(ASSETS_DIR, "ambulance.png")
        try:
            img = pygame.image.load(amb_path).convert_alpha()
            self.ambulance_sprite = pygame.transform.scale(img, (48, 48))
        except Exception:
            pass
        self.citizen_sprite = None
        cit_path = os.path.join(ASSETS_DIR, "citizen.png")
        try:
            img = pygame.image.load(cit_path).convert_alpha()
            self.citizen_sprite = pygame.transform.scale(img, (48, 48))
        except Exception:
            pass
        self.ambulance_music = None
        self.flood_music = None
        self.ambulance_music_ch = None
        self.flood_music_ch = None
        if self.audio_enabled:
            try:
                amb_sound_path = os.path.join(ASSETS_DIR, "ambulance.mp3")
                self.ambulance_music = pygame.mixer.Sound(amb_sound_path)
            except Exception:
                self.ambulance_music = None
            try:
                flood_sound_path = os.path.join(ASSETS_DIR, "Paani.wav")
                self.flood_music = pygame.mixer.Sound(flood_sound_path)
            except Exception:
                self.flood_music = None
        #button rects
        self.btn_csp   = pygame.Rect(0, 0, 0, 0)
        self.btn_mst   = pygame.Rect(0, 0, 0, 0)
        self.btn_ga    = pygame.Rect(0, 0, 0, 0)
        self.btn_routing = pygame.Rect(0, 0, 0, 0)
        self.btn_random_routing = pygame.Rect(0, 0, 0, 0)
        self.btn_ambulance_sim = pygame.Rect(0, 0, 0, 0)
        self.btn_ml    = pygame.Rect(0, 0, 0, 0)#challenge 5
        self.btn_flood = pygame.Rect(0, 0, 0, 0)
        self.btn_reset = pygame.Rect(0, 0, 0, 0)
        #overlay toggle
        self.btn_overlay_road = pygame.Rect(0, 0, 0, 0)
        self.btn_overlay_amb  = pygame.Rect(0, 0, 0, 0)
        self.btn_overlay_crime = pygame.Rect(0, 0, 0, 0)
        #border trees
        import random

        random.seed(42)
        self.border_trees = []
        #top strip
        for _ in range(9):
            x = random.randint(MAP_X + 20, SCREEN_WIDTH - 20)
            y = random.randint(MAP_Y - 22, MAP_Y - 6)
            s = random.randint(7, 12)
            self.border_trees.append((x, y, s))
        #bottom strip
        for _ in range(9):
            x = random.randint(MAP_X + 20, SCREEN_WIDTH - 20)
            y = random.randint(MAP_Y + MAP_H + 4, MAP_Y + MAP_H + 20)
            s = random.randint(7, 12)
            self.border_trees.append((x, y, s))
        #right strip
        for _ in range(10):
            x = random.randint(SCREEN_WIDTH - 22, SCREEN_WIDTH - 4)
            y = random.randint(MAP_Y + 10, MAP_Y + MAP_H - 10)
            s = random.randint(7, 12)
            self.border_trees.append((x, y, s))

    def _log(self, msg):
        self.event_log.append(msg)
        if len(self.event_log) > 50:
            self.event_log = self.event_log[-50:]
        print(f"{msg}")
    #sidebar
    #divider

    def _draw_section_divider(self, y):
        pygame.draw.line(self.screen, COL_BORDER, (14, y), (SIDEBAR_W - 14, y), 1)
        #gold dot
        cx = SIDEBAR_W // 2
        cy = y - 1
        pygame.draw.polygon(self.screen, COL_GOLD_DIM, [
            (cx, cy - 3), (cx + 3, cy), (cx, cy + 3), (cx - 3, cy)
        ])
        return y + 14

    def _draw_topbar(self):
        pygame.draw.rect(self.screen, COL_TOPBAR, (0, 0, SCREEN_WIDTH, TOPBAR_H))
        pygame.draw.line(self.screen, COL_BORDER_GOLD, (0, TOPBAR_H-1), (SCREEN_WIDTH, TOPBAR_H-1), 2)
        pygame.draw.line(self.screen, COL_BORDER, (0, TOPBAR_H-2), (SCREEN_WIDTH, TOPBAR_H-2), 1)
        title = self.font_title.render("LAHORE City Explorer", True, COL_GOLD_SHINE)
        self.screen.blit(title, (14, TOPBAR_H//2 - title.get_height()//2))
        subtitle = self.font_tiny.render("Urban Intelligence System", True, COL_GOLD_DIM)
        self.screen.blit(subtitle, (14 + title.get_width() + 10, TOPBAR_H//2 - subtitle.get_height()//2))
        #stats strip
        buildings_count = sum(1 for n in self.city.nodes.values() if n.location_type)
        blocked_count   = sum(1 for e in self.city.edges if e.blocked)
        mst_count       = sum(1 for e in self.city.edges if e.in_mst)
        amb_count       = len(self.city.ambulance_positions)
        stat_pairs = [
            ("BUILDINGS",  f"{buildings_count}", COL_GOLD_SHINE),
            ("AMBULANCES", f"{amb_count}" if self.ga_done else "—", COL_GOLD_SHINE),
            ("RIVER",      "Flooded" if self.flooded else "Normal", COL_DANGER_TEXT if self.flooded else COL_SUCCESS_TEXT),
            ("ROADS",      f"{len(self.city.edges)}", COL_GOLD_SHINE),
            ("MST ROADS",  f"{mst_count}" if self.mst_done else "—", COL_GOLD_SHINE),
            ("BLOCKED",    f"{blocked_count}", COL_GOLD_SHINE),
        ]
        stat_w = (SCREEN_WIDTH - 320) // max(1, len(stat_pairs))
        for i, (lbl, val, val_col) in enumerate(stat_pairs):
            x = 320 + i * stat_w
            #draw line
            if i > 0:
                pygame.draw.line(self.screen, COL_BORDER, (x - 10, 0), (x - 10, TOPBAR_H), 1)
            lbl_surf = self.font_tiny.render(lbl, True, COL_GOLD_DIM)
            val_surf = self.font_heading.render(val, True, val_col)
            #stack vertically
            self.screen.blit(lbl_surf, (x, 12))
            self.screen.blit(val_surf, (x, 28))

    def draw_sidebar(self):
        #fill sidebar panel
        pygame.draw.rect(self.screen, COL_SIDEBAR, (0, TOPBAR_H, SIDEBAR_W, SCREEN_HEIGHT - TOPBAR_H))
        #border double line
        pygame.draw.line(self.screen, COL_BORDER_GOLD, (SIDEBAR_W-2, TOPBAR_H), (SIDEBAR_W-2, SCREEN_HEIGHT), 2)
        pygame.draw.line(self.screen, COL_BORDER, (SIDEBAR_W-4, TOPBAR_H), (SIDEBAR_W-4, SCREEN_HEIGHT), 1)
        y = TOPBAR_H + 10
        #title block
        title_str = "LAHORE City Explorer"
        title = self.font_title.render(title_str, True, COL_GOLD_BRIGHT)
        cx = SIDEBAR_W // 2
        cy = y + title.get_height() // 2
        #left diamond
        pygame.draw.polygon(self.screen, COL_GOLD_DIM, [
            (cx - title.get_width()//2 - 20, cy),
            (cx - title.get_width()//2 - 15, cy - 4),
            (cx - title.get_width()//2 - 10, cy),
            (cx - title.get_width()//2 - 15, cy + 4)
        ])
        #right diamond
        pygame.draw.polygon(self.screen, COL_GOLD_DIM, [
            (cx + title.get_width()//2 + 10, cy),
            (cx + title.get_width()//2 + 15, cy - 4),
            (cx + title.get_width()//2 + 20, cy),
            (cx + title.get_width()//2 + 15, cy + 4)
        ])
        self.screen.blit(title, (cx - title.get_width()//2, y))
        y += 32
        y = self._draw_section_divider(y)
        #view toggles
        self.screen.blit(self.font_heading.render("VIEW MODE", True, COL_GOLD_DIM), (14, y))
        y += 18
        ov_w = (SIDEBAR_W - 28) // 2
        ov_h = 26
        pygame.draw.rect(self.screen, COL_BORDER_GOLD, (14, y, ov_w*2, ov_h), 1, border_radius=4)
        for btn_attr, mode, label, idx in [
            ("btn_overlay_road",  OVERLAY_ROAD,      "Roads",    0),
            ("btn_overlay_crime", OVERLAY_CRIME,     "Heatmap",  1),
        ]:
            bx = 14 + idx * ov_w
            rect = pygame.Rect(bx, y, ov_w, ov_h)
            setattr(self, btn_attr, rect)
            active = self.overlay_mode == mode
            hover = self.hovered_btn == btn_attr and not active
            bg_col = COL_BORDER_GOLD if active else (COL_CARD_HOVER if hover else COL_SIDEBAR_DEEP)
            txt_col = COL_GOLD_SHINE if active else (COL_GOLD if hover else COL_TEXT_DIM)
            pygame.draw.rect(self.screen, bg_col, (bx+1, y+1, ov_w-1, ov_h-2))
            lbl = self.font_heading.render(label, True, txt_col)
            self.screen.blit(lbl, (rect.centerx - lbl.get_width()//2, rect.centery - lbl.get_height()//2))
            if idx > 0:
                pygame.draw.line(self.screen, COL_BORDER, (bx, y), (bx, y+ov_h), 1)
        y += ov_h + 14
        y = self._draw_section_divider(y)
        self.screen.blit(self.font_heading.render("LEGEND", True, COL_GOLD_DIM), (14, y))
        y += 20

        def _legend_row(icon_col, label, is_x=False):
            nonlocal y
            if is_x:
                pygame.draw.line(self.screen, (255, 50, 50), (14, y+3), (24, y+11), 2)
                pygame.draw.line(self.screen, (255, 50, 50), (14, y+11), (24, y+3), 2)
            elif isinstance(icon_col, tuple) and len(icon_col) > 3:#hack to identify
                pygame.draw.line(self.screen, icon_col[:3], (14, y+7), (26, y+7), icon_col[3])
            else:
                pygame.draw.rect(self.screen, icon_col, (14, y+2, 12, 10))
            self.screen.blit(self.font_tiny.render(label, True, COL_TEXT_PRIMARY), (34, y))
            y += 18
        _legend_row(COL_BORDER + (2,), "Road")
        _legend_row(COL_BORDER_GOLD + (2,), "MST Road")
        _legend_row((220, 50, 60, 2), "Blocked Road")
        _legend_row(None, "Not Accessible", is_x=True)
        if self.overlay_mode == OVERLAY_CRIME and self.ml_done:
            _legend_row(COL_DANGER_TEXT, "High Risk")
            _legend_row(COL_WARNING_TEXT, "Med Risk")
            _legend_row(COL_SUCCESS_TEXT, "Low Risk")
        if self.routing_done:
            _legend_row((200, 170, 0, 3), "A* Route")
        y += 4
        y = self._draw_section_divider(y)
        y += 4
        #action buttons
        btn_w, btn_h = SIDEBAR_W - 28, 30
        buttons = [
            ("btn_csp",    (40, 160, 100),  self.csp_done,
             "CSP Layout",         "Layout Done"),
            ("btn_mst",    (60, 120, 200),  self.mst_done,
             "Road Network",       "Network Built"),
            ("btn_ga",     (140, 80, 200),  self.ga_done,
             "Ambulance Placement","Ambulances Placed"),
            ("btn_ml",     (200, 70, 130),  self.ml_done,
             "Crime Risk ML",      "Risk Predicted"),
            ("btn_routing",(200, 130, 50),  self.routing_done,
             "Emergency Routing",  "Routing Complete"),
            ("btn_random_routing", (180, 150, 40), False,
             "Random Routing",     ""),
            ("btn_ambulance_sim",  (40,  180, 90),  False,
             "Ambulance Sim",      ""),
            ("btn_flood",  (180, 40,  40),  False,
             "Simulate Flood",     ""),
            ("btn_reset",  (80,  80,  100), False,
             "Reset Flood",        ""),
        ]
        ticks = pygame.time.get_ticks()
        for btn_attr, accent, done_flag, label, done_label in buttons:
            rect = pygame.Rect(14, y, btn_w, btn_h)
            setattr(self, btn_attr, rect)
            is_running = self.btn_running == btn_attr
            is_hover = self.hovered_btn == btn_attr
            if done_flag:
                bg = (accent[0]//4, accent[1]//4, accent[2]//4)
                border = COL_SUCCESS
                txt_col = COL_SUCCESS_TEXT
                txt_str = "[OK] " + done_label
            elif is_running:
                bg = COL_SIDEBAR_DEEP
                border = COL_BORDER_GOLD
                txt_col = COL_GOLD_DIM
                dots = "." * (ticks // 400 % 4)
                txt_str = "Running" + dots
            elif is_hover:
                bg = COL_CARD_HOVER
                border = COL_BORDER_BRIGHT
                txt_col = COL_GOLD
                txt_str = label
            else:
                bg = COL_CARD
                border = COL_BORDER_GOLD
                txt_col = COL_TEXT_PRIMARY
                txt_str = label
            pygame.draw.rect(self.screen, bg, rect, border_radius=4)
            pygame.draw.rect(self.screen, border, rect, 1, border_radius=4)
            txt = self.font_heading.render(txt_str, True, txt_col)
            self.screen.blit(txt, (26, y + btn_h//2 - txt.get_height()//2))
            if is_hover and not done_flag and not is_running:
                pygame.draw.polygon(self.screen, COL_GOLD_DIM, [
                    (rect.right - 18, rect.centery - 4),
                    (rect.right - 12, rect.centery),
                    (rect.right - 18, rect.centery + 4)
                ])
            y += btn_h + 5
    #map

    def _draw_map_frame(self):
        blen = 18#bracket arm length
        bw   = 2#line width
        col  = COL_BORDER_GOLD
        mx, my = MAP_X, MAP_Y
        mw, mh = MAP_W, MAP_H
        pad  = 4
        corners = [
            #top left
            [(mx+pad, my+pad+blen), (mx+pad, my+pad), (mx+pad+blen, my+pad)],
            #top right
            [(mx+mw-pad-blen, my+pad), (mx+mw-pad, my+pad), (mx+mw-pad, my+pad+blen)],
            #bottom left
            [(mx+pad, my+mh-pad-blen), (mx+pad, my+mh-pad), (mx+pad+blen, my+mh-pad)],
            #bottom right
            [(mx+mw-pad-blen, my+mh-pad), (mx+mw-pad, my+mh-pad), (mx+mw-pad, my+mh-pad-blen)],
        ]
        for pts in corners:
            pygame.draw.lines(self.screen, col, False, pts, bw)

    def _draw_border_trees(self):
        for (x, y, size) in self.border_trees:
            #trunk
            pygame.draw.rect(self.screen, (60, 38, 18), (x - 1, y + size//2, 3, size//2 + 2))
            #canopy outer
            pygame.draw.circle(self.screen, (28, 72, 32), (x, y + size//4), size//2 + 2)
            #canopy inner
            pygame.draw.circle(self.screen, (40, 98, 44), (x - 1, y), size//2)

    def draw_map(self):
        self._draw_topbar()
        map_rect = pygame.Rect(MAP_X, MAP_Y, MAP_W, MAP_H)
        pygame.draw.rect(self.screen, COL_MAP_BG, map_rect)
        self.screen.set_clip(map_rect)
        #river bed always
        for node_coord in self.city.river_nodes:
            sp = self.camera.world_to_screen(node_coord[0] * self.node_spacing, node_coord[1] * self.node_spacing)
            pygame.draw.circle(self.screen, (30, 65, 130), (int(sp[0]), int(sp[1])), 3)
        #flood water draws
        if self.flooded:
            for node_coord in self.city.river_nodes:
                sp = self.camera.world_to_screen(node_coord[0] * self.node_spacing, node_coord[1] * self.node_spacing)
                pygame.draw.circle(self.screen, (55, 130, 220), (int(sp[0]), int(sp[1])), 7)
            for edge in self.city.edges:
                if edge.blocked:
                    p1 = self.camera.world_to_screen(edge.u.x * self.node_spacing, edge.u.y * self.node_spacing)
                    p2 = self.camera.world_to_screen(edge.v.x * self.node_spacing, edge.v.y * self.node_spacing)
                    #draw blue flood
                    width = max(6, int(15 * self.camera.zoom))
                    pygame.draw.line(self.screen, (30, 80, 150), (int(p1[0]), int(p1[1])), (int(p2[0]), int(p2[1])), width)
                    #draw blue flood
                    for node_coord in [(edge.u.x, edge.u.y), (edge.v.x, edge.v.y)]:
                        sp = self.camera.world_to_screen(node_coord[0] * self.node_spacing, node_coord[1] * self.node_spacing)
                        #draw a semi
                        flood_surf = pygame.Surface((20, 20), pygame.SRCALPHA)
                        pygame.draw.circle(flood_surf, (55, 130, 220, 130), (10, 10), 10)
                        self.screen.blit(flood_surf, (int(sp[0]) - 10, int(sp[1]) - 10))
        #roads
        for edge in self.city.edges:
            p1 = self.camera.world_to_screen(edge.u.x * self.node_spacing,
                                              edge.u.y * self.node_spacing)
            p2 = self.camera.world_to_screen(edge.v.x * self.node_spacing,
                                              edge.v.y * self.node_spacing)
            if edge.blocked:
                color, width = COLOR_ROAD_BLOCKED, max(2, int(3 * self.camera.zoom))
                pygame.draw.line(self.screen, color,
                                 (int(p1[0]), int(p1[1])),
                                 (int(p2[0]), int(p2[1])), width)
            elif edge.in_mst:
                color, width = COLOR_ROAD_MST, max(2, int(3 * self.camera.zoom))
                pygame.draw.line(self.screen, color,
                                 (int(p1[0]), int(p1[1])),
                                 (int(p2[0]), int(p2[1])), width)
            else:
                color, width = COLOR_ROAD, max(1, int(1.5 * self.camera.zoom))
                pygame.draw.line(self.screen, color,
                                 (int(p1[0]), int(p1[1])),
                                 (int(p2[0]), int(p2[1])), width)
        #emergency route visualization
        if hasattr(self.city, 'routing_result') and self.city.routing_result:
            routes = self.city.routing_result.get('routes', [])
            route_colors = [
                (200, 170, 0),#dark yellow challenge
                (200, 170, 0),
                (200, 170, 0),
                (200, 170, 0),
                (200, 170, 0),#dark yellow
            ]
            for route_idx, route in enumerate(routes):
                if not route:
                    continue
                color = route_colors[route_idx % len(route_colors)]
                width = max(3, int(3.5 * self.camera.zoom))
                #draw path line
                for i in range(len(route) - 1):
                    x1, y1 = route[i]
                    x2, y2 = route[i + 1]
                    p1 = self.camera.world_to_screen(x1 * self.node_spacing, y1 * self.node_spacing)
                    p2 = self.camera.world_to_screen(x2 * self.node_spacing, y2 * self.node_spacing)
                    pygame.draw.line(self.screen, color,
                                    (int(p1[0]), int(p1[1])),
                                    (int(p2[0]), int(p2[1])), width)
                #draw route number
                if route:
                    sx, sy = self.camera.world_to_screen(
                        route[0][0] * self.node_spacing,
                        route[0][1] * self.node_spacing
                    )
                    route_label = self.font_small.render(
                        f"R{route_idx + 1}",
                        True, color
                    )
                    self.screen.blit(route_label, (int(sx) + 5, int(sy) - 15))
        #crime heatmap overlay
        if self.overlay_mode == OVERLAY_CRIME and self.ml_done:
            for node in self.city.get_all_nodes():
                wx = node.x * self.node_spacing
                wy = node.y * self.node_spacing
                sx, sy = self.camera.world_to_screen(wx, wy)
                sx, sy = int(sx), int(sy)
                r = node.risk_index#0 0 1
                #interpolate low green
                if r >= 0.7:
                    heat_col = (200, 40, 40, 120)#red high
                elif r >= 0.3:
                    t = (r - 0.3) / 0.4#0 1 as
                    heat_col = (
                        int(50  + t * 180),
                        int(180 - t * 140),
                        40, 100
                    )
                else:
                    heat_col = (50, 180, 40, 80)#green low
                cell_size = max(10, int(self.node_spacing * self.camera.zoom * 0.9))
                surf = pygame.Surface((cell_size, cell_size), pygame.SRCALPHA)
                surf.fill(heat_col[:3] + (heat_col[3],))
                self.screen.blit(surf, (sx - cell_size // 2, sy - cell_size // 2))
        #nodes
        mouse_world = self.camera.screen_to_world(*pygame.mouse.get_pos())
        self.hovered_node = None
        for node in self.city.get_all_nodes():
            wx = node.x * self.node_spacing
            wy = node.y * self.node_spacing
            sx, sy = self.camera.world_to_screen(wx, wy)
            sx, sy = int(sx), int(sy)
            dist = math.sqrt((mouse_world[0]-wx)**2 + (mouse_world[1]-wy)**2)
            if dist < 20 / self.camera.zoom:
                self.hovered_node = node
            base_r = max(3, int(6 * self.camera.zoom))
            if node.location_type:
                color = TYPE_COLORS.get(node.location_type, (200, 200, 200))
                m = max(8, int(16 * self.camera.zoom))
                #check if asset
                img = self.assets.get(node.location_type)
                if img:
                    #dynamically scale image
                    scaled_w = max(16, int(img.get_width() * self.camera.zoom))
                    scaled_h = max(16, int(img.get_height() * self.camera.zoom))
                    scaled_img = pygame.transform.scale(img, (scaled_w, scaled_h))
                    self.screen.blit(scaled_img, (sx - scaled_w // 2, sy - scaled_h // 2))
                else:
                    pygame.draw.rect(self.screen, color,
                                     (sx - m//2, sy - m//2, m, m), border_radius=3)
                if node.is_primary_hospital:
                    pygame.draw.circle(self.screen, (255, 255, 255), (sx, sy), m//3)
                if not node.accessible:
                    c = max(m // 2, 8)
                    pygame.draw.line(self.screen, (200, 40, 40),
                                     (sx-c, sy-c), (sx+c, sy+c), 3)
                    pygame.draw.line(self.screen, (200, 40, 40),
                                     (sx+c, sy-c), (sx-c, sy+c), 3)
            else:
                dot = (50, 40, 40) if not node.accessible else (60, 65, 75)
                pygame.draw.circle(self.screen, dot, (sx, sy), base_r)
            if self.hovered_node == node:
                pygame.draw.circle(self.screen, COLOR_ACCENT,
                                   (sx, sy), base_r + max(5, int(10*self.camera.zoom)), 2)
        #ambulance markers challenge
        for amb_coord in self.city.ambulance_positions:
            #hide the ambulance
            if self.ambulance_animating and hasattr(self, 'anim_full_path') and self.anim_full_path:
                if amb_coord == self.anim_full_path[0]:
                    continue
            ax = amb_coord[0] * self.node_spacing
            ay = amb_coord[1] * self.node_spacing
            asx, asy = self.camera.world_to_screen(ax, ay)
            asx, asy = int(asx), int(asy)
            #coverage halo shows
            halo_r = max(20, int(60 * self.camera.zoom))
            halo_surface = pygame.Surface((halo_r * 2, halo_r * 2), pygame.SRCALPHA)
            pygame.draw.circle(halo_surface, (160, 100, 240, 40),
                               (halo_r, halo_r), halo_r)
            pygame.draw.circle(halo_surface, (160, 100, 240, 80),
                               (halo_r, halo_r), halo_r, 2)
            self.screen.blit(halo_surface, (asx - halo_r, asy - halo_r))
            #ambulance sprite or
            if self.ambulance_sprite:
                s = max(24, int(48 * self.camera.zoom))
                scaled = pygame.transform.scale(self.ambulance_sprite, (s, s))
                self.screen.blit(scaled, (asx - s // 2, asy - s // 2))
            else:
                #fallback white cross
                r = max(8, int(14 * self.camera.zoom))
                pygame.draw.circle(self.screen, (160, 100, 240), (asx, asy), r)
                pygame.draw.line(self.screen, (255, 255, 255),
                                 (asx - r//2, asy), (asx + r//2, asy), 2)
                pygame.draw.line(self.screen, (255, 255, 255),
                                 (asx, asy - r//2), (asx, asy + r//2), 2)
        #animated moving ambulance
        if self.ambulance_animating and self.anim_current_pos:
            ax = self.anim_current_pos[0] * self.node_spacing
            ay = self.anim_current_pos[1] * self.node_spacing
            asx, asy = self.camera.world_to_screen(ax, ay)
            asx, asy = int(asx), int(asy)
            if self.ambulance_sprite:
                s = max(32, int(64 * self.camera.zoom))#slightly larger
                scaled = pygame.transform.scale(self.ambulance_sprite, (s, s))
                self.screen.blit(scaled, (asx - s // 2, asy - s // 2))
                #highlight ring
                pygame.draw.circle(self.screen, (0, 255, 200), (asx, asy), s//2 + 4, 3)
            else:
                r = max(10, int(18 * self.camera.zoom))
                pygame.draw.circle(self.screen, (0, 255, 100), (asx, asy), r)
                pygame.draw.line(self.screen, (255, 255, 255), (asx - r//2, asy), (asx + r//2, asy), 3)
                pygame.draw.line(self.screen, (255, 255, 255), (asx, asy - r//2), (asx, asy + r//2), 3)
        #trapped civilians challenge
        for civ_coord in self.city.trapped_civilians:
            if civ_coord in getattr(self, 'rescued_civilians', set()):
                continue
            cx = civ_coord[0] * self.node_spacing
            cy = civ_coord[1] * self.node_spacing
            csx, csy = self.camera.world_to_screen(cx, cy)
            csx, csy = int(csx), int(csy)
            if self.citizen_sprite:
                s = max(24, int(48 * self.camera.zoom))
                scaled = pygame.transform.scale(self.citizen_sprite, (s, s))
                #render directly on
                self.screen.blit(scaled, (csx - s // 2, csy - s // 2))
            else:
                #fallback small orange
                r = max(4, int(8 * self.camera.zoom))
                pygame.draw.circle(self.screen, (255, 160, 40), (csx + 8, csy - 8), r)
        self.screen.set_clip(None)

        # ── Node Hover Tooltip ──
        if self.hovered_node:
            node = self.hovered_node
            wx = node.x * self.node_spacing
            wy = node.y * self.node_spacing
            tsx, tsy = self.camera.world_to_screen(wx, wy)
            tsx, tsy = int(tsx), int(tsy)

            n_type = node.location_type or "Empty"
            risk_val = node.risk_index
            if risk_val >= 0.7:
                risk_label = "High"
            elif risk_val >= 0.3:
                risk_label = "Medium"
            else:
                risk_label = "Low"

            lines = [
                f"Type: {n_type}",
                f"Grid: ({node.x}, {node.y})",
                f"Pop Density: {node.population_density:.0f}",
                f"Risk: {risk_label} ({risk_val:.2f})",
            ]

            line_surfs = [self.font_tiny.render(l, True, COL_TEXT_PRIMARY) for l in lines]
            pad = 8
            line_h = max(s.get_height() for s in line_surfs) + 3
            tw = max(s.get_width() for s in line_surfs) + pad * 2
            th = line_h * len(line_surfs) + pad * 2 - 3

            # Position tooltip to the right of the node; flip if near screen edge
            tx = tsx + 18
            ty = tsy - th // 2
            if tx + tw > SCREEN_WIDTH:
                tx = tsx - tw - 18
            if ty < TOPBAR_H:
                ty = TOPBAR_H + 4
            if ty + th > SCREEN_HEIGHT:
                ty = SCREEN_HEIGHT - th - 4

            # Background card
            tip_rect = pygame.Rect(tx, ty, tw, th)
            pygame.draw.rect(self.screen, COL_CARD, tip_rect, border_radius=6)
            pygame.draw.rect(self.screen, COL_BORDER_GOLD, tip_rect, 1, border_radius=6)

            for i, surf in enumerate(line_surfs):
                self.screen.blit(surf, (tx + pad, ty + pad + i * line_h))
    #button handlers

    def _handle_csp(self):
        from challenge1_layout import solve_layout, identify_primary_hospital

        self._log("Running CSP layout...")
        placement = solve_layout(self.city)
        if placement:
            identify_primary_hospital(self.city)
            self.csp_done = True
            self.mst_done = False#mst needs to
            self._log(f"CSP done: {len(placement)} buildings placed.")
        else:
            self._log("CSP failed — check building counts.")

    def _handle_mst(self):
        from challenge2_network import optimize_network

        if not self.csp_done:
            self._log("Run CSP first!")
            return
        self._log("Building road network (Kruskal MST)...")
        result = optimize_network(self.city)
        if result:
            self.mst_done = True
            self._log(f"MST: {result['mst_edge_count']} edges, "
                       f"cost {result['total_cost']:.1f}")
            if result['redundancy_added']:
                self._log("Redundancy path added.")
        else:
            self._log("MST failed.")

    def _handle_ga(self):
        from challenge3_ga import evaluate_depots

        if not self.mst_done:
            self._log("Build road network first!")
            return
        self._log("Running GA ambulance placement...")
        result = evaluate_depots(self.city)
        if result:
            self.ga_done = True
            self._log(f"GA: {len(result['best_positions'])} ambulances, "
                       f"worst-case: {result['best_fitness']} hops")
        else:
            self._log("GA failed.")

    def _handle_ml(self):
        #challenge 5 run
        from challenge5_ml import run_crime_risk_pipeline

        if not self.csp_done:
            self._log("Run CSP Layout first (need buildings placed)!")
            return
        self._log("Running Challenge 5 ML pipeline...")
        try:
            result = run_crime_risk_pipeline(self.city)
            if result:
                self.ml_done = True
                counts = result['risk_counts']
                self._log(
                    f"ML done (k={result['best_k']}, inertia={result['kmeans_inertia']:.0f}): "
                    f"H={counts['High']} M={counts['Medium']} L={counts['Low']}"
                )
                self._log(
                    f"Decision Tree acc: {result['tree_accuracy']:.0%}. "
                    f"Edge costs updated."
                )
                #switch to crime
                self.overlay_mode = OVERLAY_CRIME
        except Exception as e:
            self._log(f"ML pipeline error: {e}")
            import traceback; traceback.print_exc()

    def _handle_routing(self):
        from challenge4_routing import add_trapped_civilians, evaluate_routing

        if not self.ga_done:
            self._log("Place ambulances first!")
            return
        #clear rescued civilians
        if hasattr(self, 'rescued_civilians'):
            self.rescued_civilians.clear()
        #set up sample
        #in a real
        trapped = [
        (2, 2),
        (12, 2),
        (12, 12),#civilian 3
        (2, 12),#civilian 4
        (7, 7),#civilian 5 center
        ]
        add_trapped_civilians(self.city, trapped)
        self._log(f"Added {len(trapped)} trapped civilians...")
        self._log("Running emergency routing (A*)...")
        result = evaluate_routing(self.city)
        if result and result['success']:
            self.routing_done = True
            self._log(f"[OK] Routing complete. Returned to base.")
        elif result:
            self._log(f"[!] Partial routing: {result['waypoints_reached']} stops reached")
        else:
            self._log("Routing failed.")

    def _handle_random_routing(self):
        from challenge4_routing import random_place_civilians, evaluate_routing

        if not self.ga_done:
            self._log("Place ambulances first!")
            return
        #clear rescued civilians
        if hasattr(self, 'rescued_civilians'):
            self.rescued_civilians.clear()
        self._log("Randomly placing trapped civilians...")
        trapped = random_place_civilians(self.city, num_civilians=5)
        self._log("Running emergency routing (A*)...")
        result = evaluate_routing(self.city)
        if result and result['success']:
            self.routing_done = True
            self._log(f"✓ Routing complete. Returned to base.")
        elif result:
            self._log(f"⚠ Partial routing: {result['waypoints_reached']} stops reached")
        else:
            self._log("Routing failed.")

    def _handle_ambulance_sim(self):
        if not hasattr(self.city, 'routing_result') or not self.city.routing_result:
            self._log("Run routing first!")
            return
        routes = self.city.routing_result.get('routes', [])
        if not routes:
            self._log("No valid route found!")
            return
        #flatten routes into
        self.anim_full_path = []
        for route in routes:
            for node in route:
                if not self.anim_full_path or self.anim_full_path[-1] != node:
                    self.anim_full_path.append(node)
        if len(self.anim_full_path) < 2:
            self._log("Path too short to animate.")
            return
        self.ambulance_animating = True
        self.anim_route_index = 0
        self.anim_progress = 0.0
        self.anim_current_pos = self.anim_full_path[0]
        if hasattr(self, 'rescued_civilians'):
            self.rescued_civilians.clear()
            if self.anim_current_pos in getattr(self.city, 'trapped_civilians', []):
                self.rescued_civilians.add(self.anim_current_pos)
        self._play_music(self.ambulance_music, 'ambulance_music_ch', loops=-1)
        self._log("Ambulance simulation started...")

    def _handle_flood(self):
        from flood_simulation import trigger_flood
        from challenge4_routing import handle_flood_event

        self._play_music(self.flood_music, 'flood_music_ch', loops=0)
        self._log("Simulating flood...")
        result = trigger_flood(self.city, spread_steps=2, block_chance=0.7)
        self.flooded = True
        self._log(f"Flood: {result['flooded_tiles']} tiles, "
                   f"{result['blocked_edges']} roads blocked.")
        if getattr(self.city, 'routing_result', None) and getattr(self.city, 'trapped_civilians', None):
            reroute = handle_flood_event(self.city, result.get('blocked_edge_pairs', []))
            if reroute.get('rerouted'):
                self._log("Emergency routing updated after flood.")
                if reroute['routing_result'] and reroute['routing_result']['success']:
                    self.routing_done = True
                    self._log(f"[OK] Routing still reaches all targets")
                elif reroute['routing_result']:
                    self._log(f"[!] Routing partial after flood: {reroute['routing_result']['waypoints_reached']} stops reached")
                #update animation path
                if self.ambulance_animating and self.city.routing_result:
                    routes = self.city.routing_result.get('routes', [])
                    new_path = []
                    for route in routes:
                        for node in route:
                            if not new_path or new_path[-1] != node:
                                new_path.append(node)
                    if new_path:
                        #try to find
                        target_node = None
                        if hasattr(self, 'anim_full_path') and self.anim_route_index + 1 < len(self.anim_full_path):
                            target_node = self.anim_full_path[self.anim_route_index + 1]
                        self.anim_full_path = new_path
                        if target_node in new_path:
                            idx = new_path.index(target_node)
                            if idx > 0:
                                self.anim_route_index = idx - 1
                                self.anim_progress = 0.0
                                self.anim_current_pos = new_path[self.anim_route_index]
                            else:
                                self.anim_route_index = 0
                                self.anim_progress = 0.0
                                self.anim_current_pos = new_path[0]
                        else:
                            self.anim_route_index = 0
                            self.anim_progress = 0.0
                            self.anim_current_pos = new_path[0]

    def _handle_reset_flood(self):
        from flood_simulation import reset_flood

        reset_flood(self.city)
        self.flooded = False
        self._stop_music('flood_music_ch')
        #re apply mst
        if self.mst_done:
            from challenge2_network import optimize_network

            optimize_network(self.city)
        self._log("Flood reset. New river generated.")

    def _stop_music(self, channel_attr):
        ch = getattr(self, channel_attr, None)
        if ch:
            try:
                ch.stop()
            except Exception:
                pass
            setattr(self, channel_attr, None)

    def _play_music(self, sound, channel_attr, loops=0):
        if not self.audio_enabled or sound is None:
            return
        self._stop_music(channel_attr)
        try:
            channel = sound.play(loops=loops)
            setattr(self, channel_attr, channel)
        except Exception:
            setattr(self, channel_attr, None)

    #main loop

    def run(self):
        running = True
        while running:
            real_mx, real_my = pygame.mouse.get_pos()
            dw, dh = self.display.get_size()
            mx = int(real_mx * (SCREEN_WIDTH / dw))
            my = int(real_my * (SCREEN_HEIGHT / dh))
            self.hovered_btn = None
            for btn_attr in ["btn_csp","btn_mst","btn_ga","btn_ml","btn_routing",
                             "btn_random_routing","btn_ambulance_sim","btn_flood","btn_reset",
                             "btn_overlay_road","btn_overlay_crime"]:
                rect = getattr(self, btn_attr, None)
                if rect and rect.collidepoint((mx, my)):
                    self.hovered_btn = btn_attr
                    break
            if self.hovered_btn:
                pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
            else:
                pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.MOUSEWHEEL:
                    self.camera.zoom = max(
                        self.camera.min_zoom,
                        min(self.camera.max_zoom,
                            self.camera.zoom + event.y * 0.1))
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    #map panning bounds
                    if mx > SIDEBAR_W and my > TOPBAR_H:
                        self.panning = True
                        self.last_mouse_pos = (mx, my)
                    #action buttons
                    clicked_btn = None
                    for btn_attr in ["btn_csp","btn_mst","btn_ga","btn_ml","btn_routing",
                                     "btn_random_routing","btn_ambulance_sim","btn_flood","btn_reset"]:
                        rect = getattr(self, btn_attr, None)
                        if rect and rect.collidepoint((mx, my)):
                            clicked_btn = btn_attr
                            break
                    if clicked_btn:
                        self.btn_running = clicked_btn
                        self.draw_sidebar()
                        pygame.display.flip()
                        if clicked_btn == "btn_csp": self._handle_csp()
                        elif clicked_btn == "btn_mst": self._handle_mst()
                        elif clicked_btn == "btn_ga": self._handle_ga()
                        elif clicked_btn == "btn_ml": self._handle_ml()
                        elif clicked_btn == "btn_routing": self._handle_routing()
                        elif clicked_btn == "btn_random_routing": self._handle_random_routing()
                        elif clicked_btn == "btn_ambulance_sim": self._handle_ambulance_sim()
                        elif clicked_btn == "btn_flood": self._handle_flood()
                        elif clicked_btn == "btn_reset": self._handle_reset_flood()
                        self.btn_running = None
                    else:
                        #overlay toggle buttons
                        if getattr(self, "btn_overlay_road", pygame.Rect(0,0,0,0)).collidepoint(mx, my):
                            self.overlay_mode = OVERLAY_ROAD
                            self._log("View: Road Network")
                        elif getattr(self, "btn_overlay_crime", pygame.Rect(0,0,0,0)).collidepoint(mx, my):
                            self.overlay_mode = OVERLAY_CRIME
                            self._log("View: Crime Heatmap")
                if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    self.panning = False
                if event.type == pygame.MOUSEMOTION and self.panning:
                    dx = mx - self.last_mouse_pos[0]
                    dy = my - self.last_mouse_pos[1]
                    self.camera.x -= dx / self.camera.zoom
                    self.camera.y -= dy / self.camera.zoom
                    self.last_mouse_pos = (mx, my)
            #update ambulance animation
            if self.ambulance_animating and hasattr(self, 'anim_full_path'):
                if self.anim_route_index < len(self.anim_full_path) - 1:
                    self.anim_progress += self.anim_speed
                    if self.anim_progress >= 1.0:
                        self.anim_progress -= 1.0
                        self.anim_route_index += 1
                        #check if we
                        current_node = self.anim_full_path[self.anim_route_index]
                        if current_node in getattr(self.city, 'trapped_civilians', []):
                            self.rescued_civilians.add(current_node)
                    if self.anim_route_index < len(self.anim_full_path) - 1:
                        p1 = self.anim_full_path[self.anim_route_index]
                        p2 = self.anim_full_path[self.anim_route_index + 1]
                        cx = p1[0] + (p2[0] - p1[0]) * self.anim_progress
                        cy = p1[1] + (p2[1] - p1[1]) * self.anim_progress
                        self.anim_current_pos = (cx, cy)
                    else:
                        self.anim_current_pos = self.anim_full_path[-1]
                else:
                    self.ambulance_animating = False
                    self._stop_music('ambulance_music_ch')
                    self._log("Ambulance simulation completed.")
            self.screen.fill(COL_BG)
            self._draw_border_trees()
            self.draw_map()
            self.screen.set_clip(None)
            self._draw_map_frame()
            self.draw_sidebar()
            #scale internal screen
            scaled_screen = pygame.transform.smoothscale(self.screen, self.display.get_size())
            self.display.blit(scaled_screen, (0, 0))
            pygame.display.flip()
            self.clock.tick(60)
        pygame.quit()
