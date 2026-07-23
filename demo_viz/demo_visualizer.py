import pygame
import numpy as np
import os
import sys
import math
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from demo_viz.demo_config import *

class Visualizer:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Genesis V5: Structure-Function Decoupling Demo")
        
        # Typography
        try:
            self.font_title = pygame.font.SysFont("Inter, Roboto, Arial", 36, bold=True)
            self.font_nodes = pygame.font.SysFont("Consolas, Courier New, monospace", 32, bold=True)
            self.font_gen = pygame.font.SysFont("Inter, Roboto, Arial", 24)
            self.font_alert = pygame.font.SysFont("Inter, Roboto, Arial", 32, bold=True)
            self.font_subtext = pygame.font.SysFont("Inter, Roboto, Arial", 20)
            self.font_overlay_story = pygame.font.SysFont("Inter, Roboto, Arial", 28, italic=True)
            self.font_action = pygame.font.SysFont("Segoe UI Symbol, Arial", 16)
        except:
            self.font_title = pygame.font.Font(None, 42)
            self.font_nodes = pygame.font.Font(None, 36)
            self.font_gen = pygame.font.Font(None, 28)
            self.font_alert = pygame.font.Font(None, 36)
            self.font_subtext = pygame.font.Font(None, 24)
            self.font_overlay_story = pygame.font.Font(None, 32)
            self.font_action = pygame.font.Font(None, 20)
            
        self.sub_width = SCREEN_WIDTH // 2
        self.sub_height = SCREEN_HEIGHT
        self.left_surface = pygame.Surface((self.sub_width, self.sub_height))
        self.right_surface = pygame.Surface((self.sub_width, self.sub_height))
        
        # Colormaps
        self.cmap_left = self._build_colormap((10, 10, 30), (40, 85, 140), (180, 220, 255))
        self.cmap_right = self._build_colormap((25, 5, 25), (140, 50, 15), (255, 190, 40))
        
        self.c_left_agent = (0, 255, 255)
        self.c_right_agent = (255, 165, 0)
        
    def _build_colormap(self, c_low, c_mid, c_high):
        lut = np.zeros((256, 3), dtype=np.uint8)
        for i in range(256):
            t = i / 255.0
            if t < 0.5:
                t2 = t * 2
                lut[i] = [
                    int(c_low[0] + (c_mid[0] - c_low[0]) * t2),
                    int(c_low[1] + (c_mid[1] - c_low[1]) * t2),
                    int(c_low[2] + (c_mid[2] - c_low[2]) * t2)
                ]
            else:
                t2 = (t - 0.5) * 2
                lut[i] = [
                    int(c_mid[0] + (c_high[0] - c_mid[0]) * t2),
                    int(c_mid[1] + (c_high[1] - c_mid[1]) * t2),
                    int(c_mid[2] + (c_high[2] - c_mid[2]) * t2)
                ]
        return lut

    def _render_text_with_shadow(self, surface, text, font, color, pos, bg_bar=False, center=False):
        text_surf = font.render(text, True, color)
        shadow_surf = font.render(text, True, (0, 0, 0))
        
        if center:
            rect = text_surf.get_rect(center=pos)
        else:
            rect = text_surf.get_rect(topleft=pos)
            
        if bg_bar:
            bg_rect = rect.copy()
            bg_rect.inflate_ip(40, 20)
            s = pygame.Surface((bg_rect.w, bg_rect.h), pygame.SRCALPHA)
            s.fill((0, 0, 0, 180))
            surface.blit(s, bg_rect.topleft)
            
        surface.blit(shadow_surf, (rect.x + 2, rect.y + 2))
        surface.blit(text_surf, rect)
        return rect

    def _render_agent_brain(self, surface, cx, cy, network_json, agent_color):
        # Draw tracked agent as a large circle (radius 24px)
        radius = 24
        
        # Draw soft glow
        glow = pygame.Surface((radius * 4, radius * 4), pygame.SRCALPHA)
        for r in range(radius * 2, radius, -1):
            alpha = int(120 * ((radius * 2 - r) / radius)**2)
            pygame.draw.circle(glow, (*agent_color, alpha), (radius*2, radius*2), r)
        surface.blit(glow, (cx - radius*2, cy - radius*2))
        
        # Base agent body
        pygame.draw.circle(surface, (20, 20, 20, 230), (cx, cy), radius)
        pygame.draw.circle(surface, (255, 255, 255), (cx, cy), radius, 2)
        
        # Parse network
        try:
            net = json.loads(network_json)
            nodes = net.get("nodes", [])
            conns = net.get("connections", [])
        except Exception:
            nodes, conns = [], []
            
        num_nodes = len(nodes)
        
        # Position nodes deterministically inside agent using Fermat's spiral
        node_coords = {}
        for i, n in enumerate(nodes):
            if num_nodes == 0: continue
            angle = i * 137.5 * (math.pi / 180.0)
            # Distance from center scales with node index
            dist = (radius - 5) * math.sqrt(i / num_nodes)
            nx = int(cx + dist * math.cos(angle))
            ny = int(cy + dist * math.sin(angle))
            node_coords[n["id"]] = (nx, ny)
            
        # Draw connections
        # Limit to first 100 connections to avoid turning V5 into a solid block
        for c in conns[:100]:
            f_id, t_id = c["from"], c["to"]
            if f_id in node_coords and t_id in node_coords:
                pygame.draw.line(surface, (*agent_color, 80), node_coords[f_id], node_coords[t_id], 1)
                
        # Draw nodes
        for n_id, (nx, ny) in node_coords.items():
            pygame.draw.circle(surface, (255, 255, 255), (nx, ny), 2)
            
    def _render_action_display(self, surface, cx, cy, action_char):
        action_map = {
            'M': ("→", "moving", (100, 255, 100)),
            'S': ("💧", "secreting", (100, 200, 255)),
            'I': ("⏸", "waiting", (200, 200, 200))
        }
        icon, label, color = action_map.get(action_char, ("⏸", "waiting", (200, 200, 200)))
        
        # Render bubble below agent
        text = f"{icon} {label}"
        text_surf = self.font_action.render(text, True, color)
        
        # Background bar
        rect = text_surf.get_rect(center=(cx, cy + 42))
        bg_rect = rect.inflate(16, 6)
        
        bg = pygame.Surface((bg_rect.w, bg_rect.h), pygame.SRCALPHA)
        pygame.draw.rect(bg, (0, 0, 0, 180), (0, 0, bg_rect.w, bg_rect.h), border_radius=6)
        
        surface.blit(bg, bg_rect.topleft)
        surface.blit(text_surf, rect)

    def _render_node_counter(self, surface, nodes, pos, pulse_val):
        # Base milestone colors
        if nodes < 100: color = (200, 200, 200)
        elif nodes < 200: color = (100, 255, 100)
        elif nodes < 300: color = (255, 255, 100)
        elif nodes < 400: color = (255, 165, 0)
        else: color = (255, 80, 80)
        
        # Apply visual pulse
        c_r = min(255, color[0] + pulse_val)
        c_g = min(255, color[1] + pulse_val)
        c_b = min(255, color[2] + pulse_val)
        
        text = f"Nodes: {int(nodes)}"
        rect = self._render_text_with_shadow(surface, text, self.font_nodes, (c_r, c_g, c_b), pos)
        
        # Progress Bar (140x8px)
        bar_x = rect.x
        bar_y = rect.bottom + 8
        bar_w = 140
        bar_h = 8
        pygame.draw.rect(surface, (40, 40, 40), (bar_x, bar_y, bar_w, bar_h))
        
        fill_w = min(bar_w, int((nodes / 500.0) * bar_w))
        if fill_w > 0:
            pygame.draw.rect(surface, (c_r, c_g, c_b), (bar_x, bar_y, fill_w, bar_h))
            
    def render_world(self, surface, substrate_U, cmap, tint, oldest_x, oldest_y, network_json, oldest_color, action_char, avg_nodes, label, generation):
        # 1. Render colormap substrate
        if substrate_U is not None:
            U = np.clip(substrate_U, 0, 1)
            U_idx = (U * 255).astype(np.uint8)
            rgb = cmap[U_idx]
            
            # Smooth scale blur
            surf = pygame.surfarray.make_surface(np.swapaxes(rgb, 0, 1))
            small_surf = pygame.transform.smoothscale(surf, (12, 12))
            scaled_sub = pygame.transform.smoothscale(small_surf, (self.sub_width, self.sub_height))
            surface.blit(scaled_sub, (0, 0))
        else:
            surface.fill((0, 0, 0))
            
        # Subtle tint
        tint_surf = pygame.Surface((self.sub_width, self.sub_height), pygame.SRCALPHA)
        tint_surf.fill((*tint, int(255 * 0.15)))
        surface.blit(tint_surf, (0, 0))
        
        # 2. Grid overlay
        grid_surf = pygame.Surface((self.sub_width, self.sub_height), pygame.SRCALPHA)
        grid_color = (255, 255, 255, 8)
        for x in range(0, self.sub_width, 32):
            pygame.draw.line(grid_surf, grid_color, (x, 0), (x, self.sub_height))
        for y in range(0, self.sub_height, 32):
            pygame.draw.line(grid_surf, grid_color, (0, y), (self.sub_width, y))
        surface.blit(grid_surf, (0, 0))
        
        scale_x = self.sub_width / SUBSTRATE_SIZE
        scale_y = self.sub_height / SUBSTRATE_SIZE
        cx, cy = int(oldest_x * scale_x), int(oldest_y * scale_y)
        
        # 3. Render brain inside tracked agent
        self._render_agent_brain(surface, cx, cy, network_json, oldest_color)
        
        # 4. Action bubble below agent
        self._render_action_display(surface, cx, cy, action_char)
        
        # 5. Milestone node pulse math
        pulse_val = 0
        if avg_nodes > 100 and int(avg_nodes) % 100 < 5:
            pulse_val = int(abs(math.sin(generation * 0.2)) * 60)
            
        # 6. Overlays
        self._render_text_with_shadow(surface, label, self.font_title, (255, 255, 255), (30, 30), bg_bar=True)
        self._render_node_counter(surface, avg_nodes, (40, 110), pulse_val)
        
    def render_frame(self, frame_idx, row_data, left_sub_U, right_sub_U, history_similarity, is_split_screen, show_left_only):
        self.screen.fill((0, 0, 0))
        
        gen = int(row_data['generation'])
        
        # Render left V4
        self.render_world(
            self.left_surface, left_sub_U, self.cmap_left, COLOR_V4_TINT,
            float(row_data['left_x']), float(row_data['left_y']),
            row_data['left_network'], self.c_left_agent, row_data['left_action'],
            float(row_data['left_avg_nodes']), "🔒 FIXED PHYSICS (V4)", gen
        )
        
        # Render right V5
        self.render_world(
            self.right_surface, right_sub_U, self.cmap_right, COLOR_V5_TINT,
            float(row_data['right_x']), float(row_data['right_y']),
            row_data['right_network'], self.c_right_agent, row_data['right_action'],
            float(row_data['right_avg_nodes']), "🌿 CO-EVOLVING PHYSICS (V5)", gen
        )
        
        # Story phase drawing
        if show_left_only:
            # V4 takes full screen or V5 is blacked out
            self.screen.blit(self.left_surface, (0, 0))
            black_cover = pygame.Surface((self.sub_width, self.sub_height))
            black_cover.fill((0, 0, 0))
            self.screen.blit(black_cover, (self.sub_width, 0))
        else:
            if is_split_screen:
                self.screen.blit(self.left_surface, (0, 0))
                self.screen.blit(self.right_surface, (self.sub_width, 0))
            else:
                # Transition fade-in for V5
                self.screen.blit(self.left_surface, (0, 0))
                # Compute fade transparency
                self.screen.blit(self.right_surface, (self.sub_width, 0))
                
        # Draw central divider line
        if not show_left_only:
            pygame.draw.line(self.screen, (100, 100, 100), (self.sub_width, 0), (self.sub_width, self.sub_height), 2)
            
        # Story overlay narrative text
        narrative = ""
        if 120 <= frame_idx < 300:
            narrative = "Fixed physics (V4) constraints lead to quick structural stagnation."
        elif 300 <= frame_idx < 480:
            narrative = "Co-evolving environments (V5) drive open-ended complexity."
        elif 480 <= frame_idx < 800:
            narrative = "Neural complexity scales to adapt to shifting environmental niches."
        elif 800 <= frame_idx < 1350:
            narrative = "Decoupling begins: internal wiring expands while external behavior remains stable."
            
        if narrative:
            self._render_text_with_shadow(self.screen, narrative, self.font_overlay_story, (255, 255, 255), (SCREEN_WIDTH // 2, 70), bg_bar=True, center=True)
            
        # ~15s (frame 450) specific annotation
        if 450 <= frame_idx < 600:
            fade = 255
            if frame_idx < 470: fade = int(((frame_idx - 450) / 20.0) * 255)
            elif frame_idx > 580: fade = int(((600 - frame_idx) / 20.0) * 255)
            
            if fade > 0:
                ann2_surf = pygame.Surface((500, 60), pygame.SRCALPHA)
                pygame.draw.rect(ann2_surf, (0, 0, 0, int(180 * (fade/255))), (0, 0, 500, 60), border_radius=15)
                self._render_text_with_shadow(ann2_surf, "🔄 Trail = same movement pattern repeated", self.font_subtext, (255, 255, 255), (250, 30), center=True)
                
                ann2_surf.set_alpha(fade)
                # Show near V4 and V5 agents
                self.screen.blit(ann2_surf, (self.sub_width // 2 - 250, self.sub_height - 180))
                self.screen.blit(ann2_surf, (self.sub_width + self.sub_width // 2 - 250, self.sub_height - 180))
                
        # Decoupling annotation triggered around gen 1350
        # Check from CSV metrics if decoupling triggered
        if (float(row_data['right_avg_nodes']) > 350 or gen >= 1350) and history_similarity > 0.90:
            ann_w, ann_h = 800, 150
            ann_surf = pygame.Surface((ann_w, ann_h), pygame.SRCALPHA)
            
            pygame.draw.rect(ann_surf, (0, 0, 0, 220), (0, 0, ann_w, ann_h), border_radius=40)
            pygame.draw.rect(ann_surf, (255, 165, 0, 255), (0, 0, ann_w, ann_h), 3, border_radius=40)
            
            self._render_text_with_shadow(ann_surf, "STRUCTURE-FUNCTION DECOUPLING DETECTED", self.font_alert, (255, 255, 255), (ann_w//2, 45), center=True)
            self._render_text_with_shadow(ann_surf, "Internal complexity grows while behaviour remains stable.", self.font_subtext, (255, 200, 200), (ann_w//2, 95), center=True)
            
            cx = self.sub_width + (self.sub_width // 2)
            cy = self.sub_height // 2
            
            rect = ann_surf.get_rect(center=(cx, cy))
            self.screen.blit(ann_surf, rect)
            
        # Bottom Gen Counter
        gen_text = f"Gen: {gen} / 2000"
        self._render_text_with_shadow(self.screen, gen_text, self.font_gen, (200, 200, 200), (SCREEN_WIDTH//2, SCREEN_HEIGHT - 35), bg_bar=True, center=True)
        
        pygame.display.flip()
        
    def render_opening_titles(self, frame_idx):
        self.screen.fill((0, 0, 0))
        
        texts = [
            "Can an evolutionary process stay productive without any fixed point?",
            "No goal. No fixed environment. No fixed rules.",
            "Just physical constraints interacting."
        ]
        
        # 120 frames total. 40 frames per text segment.
        txt_idx = min(2, frame_idx // 40)
        text = texts[txt_idx]
        
        # Compute fade alpha
        sub_frame = frame_idx % 40
        if sub_frame < 10:
            alpha = int((sub_frame / 10.0) * 255)
        elif sub_frame > 30:
            alpha = int(((40 - sub_frame) / 10.0) * 255)
        else:
            alpha = 255
            
        surf = self.font_title.render(text, True, (255, 255, 255))
        surf.set_alpha(alpha)
        rect = surf.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
        
        self.screen.blit(surf, rect)
        pygame.display.flip()
        
    def render_end_card(self, frame_idx):
        self.screen.fill((0, 0, 0))
        
        text1 = "Can artificial systems evolve open-ended complexity"
        text2 = "without predefined objectives?"
        text3 = "Genesis V5: Open-Ended Evolutionary Dynamics."
        
        self._render_text_with_shadow(self.screen, text1, self.font_title, (255, 255, 255), (SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 60), center=True)
        self._render_text_with_shadow(self.screen, text2, self.font_title, (255, 255, 255), (SCREEN_WIDTH//2, SCREEN_HEIGHT//2), center=True)
        self._render_text_with_shadow(self.screen, text3, self.font_subtext, (200, 200, 200), (SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 80), center=True)
        
        pygame.display.flip()
