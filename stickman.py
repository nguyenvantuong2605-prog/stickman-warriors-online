import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
import random
import json
import os

# --- 1. CẤU HÌNH ---
THEME = {
    'bg': "#050010",
    'grid': "#1A0033",
    'p1': "#00F7FF",
    'p2': "#FF0055",
    'btn_bg': "#101030",
    'btn_fg': "#00FFFF",
    'disabled': "#555555",
    'text': "#FFFFFF",
    'reward': "#FFD700",
    'beam_core': "#FFFFFF",
    'beam_mid': "#FFFF00",
    'beam_out': "#FF4500"
}

DATA_FILE = "stickman_data.json"
MEMORY_FILE = "ai_memory.json"

GAME_CONFIG = {
    'block_cost': 50,
    'exp_base': 1000,
    'rewards': {
        2: {'type': 'gold', 'val': 2000, 'desc': "2000 Vàng"},
        3: {'type': 'hp', 'val': 200, 'desc': "+200 Máu"},
        5: {'type': 'skin', 'val': 'frieza', 'desc': "Skin Frieza Vàng"},
        10: {'type': 'hp', 'val': 1000, 'desc': "+1000 Máu (Bất Tử)"}
    },
    'skills': {
        'dam_nhe': {'name': "Đấm Thường", 'dmg': (25, 40), 'acc': 95, 'limit': 999, 'type': 'melee', 'price': 0},
        'kame': {'name': "KAMEHAMEHA", 'dmg': (70, 100), 'acc': 80, 'limit': 3, 'type': 'beam', 'price': 200},
        'genki': {'name': "Quả Cầu Kênh Khi", 'dmg': (150, 200), 'acc': 70, 'limit': 1, 'type': 'bomb', 'price': 500},
        'teleport': {'name': "Dịch Chuyển", 'dmg': (50, 70), 'acc': 90, 'limit': 5, 'type': 'teleport', 'price': 300}
    },
    'skins': {
        'default': {'name': "Neon Xanh", 'price': 0, 'color': '#00F7FF'},
        'goku': {'name': "Goku Cam", 'price': 500, 'color': '#FF6600'},
        'vegeta': {'name': "Vegeta Xanh", 'price': 1000, 'color': '#0000FF'},
        'black': {'name': "Goku Black", 'price': 3000, 'color': '#FF69B4'},
        'frieza': {'name': "Frieza Vàng", 'price': 5000, 'color': '#FFD700'}
    },
    'giftcodes': {'MHJKIOPGH': 10000, 'THUYTRWS': 99999,'MHTHTTNT':3000, 'CARD50K': 50000}
}

# --- 2. QUẢN LÝ DỮ LIỆU ---
class DataManager:
    def __init__(self):
        self.data = self.load()

    def load(self):
        if not os.path.exists(DATA_FILE):
            return {}
        try:
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}

    def save(self):
        with open(DATA_FILE, 'w') as f:
            json.dump(self.data, f, indent=4)

    def register(self, u, p):
        if u in self.data:
            return False, "Tài khoản đã tồn tại!"
        self.data[u] = {
            'password': p, 'level': 1, 'exp': 100, 'gold': 500,
            'hp_max': 500, 'skills': ['dam_nhe'], 'skins': ['default'],
            'current_skin': '#00F7FF', 'used_codes': []
        }
        self.save()
        return True, "Đăng ký thành công!"

    def login(self, u, p):
        if u not in self.data:
            return False, "Tài khoản không tồn tại!", None
        if self.data[u]['password'] != p:
            return False, "Sai mật khẩu!", None
        user = self.data[u]
        if 'skills' not in user: user['skills'] = ['dam_nhe']
        if 'hp_max' not in user: user['hp_max'] = 500
        return True, "OK", user

    def update(self, u, d):
        self.data[u] = d
        self.save()

# --- 3. AI ---
class SmartBrain:
    def __init__(self):
        self.q_table = self.load_memory()
        self.last_state = None
        self.last_action = None
        self.epsilon = 0.2
        self.alpha = 0.1
        self.gamma = 0.9

    def load_memory(self):
        if not os.path.exists(MEMORY_FILE):
            return {}
        try:
            with open(MEMORY_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}

    def save_memory(self):
        with open(MEMORY_FILE, 'w') as f:
            json.dump(self.q_table, f, indent=4)

    def get_state(self, ai_hp, p_hp, max_hp):
        s1 = 0 if ai_hp < max_hp * 0.3 else (2 if ai_hp > max_hp * 0.7 else 1)
        s2 = 0 if p_hp < max_hp * 0.3 else (2 if p_hp > max_hp * 0.7 else 1)
        return f"{s1}-{s2}"

    def choose_action(self, ai_hp, p_hp, max_hp, available_skills):
        for k in available_skills:
            s = GAME_CONFIG['skills'][k]
            if s['dmg'][0] >= p_hp and s['acc'] >= 90:
                return k

        state = self.get_state(ai_hp, p_hp, max_hp)
        self.last_state = state
        
        if state not in self.q_table:
            self.q_table[state] = {}

        if random.random() < self.epsilon:
            action = random.choice(available_skills)
        else:
            known = {k: v for k, v in self.q_table[state].items() if k in available_skills}
            if known:
                action = max(known, key=known.get)
            else:
                action = random.choice(available_skills)
        
        self.last_action = action
        return action

    def learn(self, c_ai, c_p, max_h, r):
        if not self.last_state or not self.last_action:
            return
        ns = self.get_state(c_ai, c_p, max_h)
        if ns not in self.q_table:
            self.q_table[ns] = {}
        if self.last_action not in self.q_table[self.last_state]:
            self.q_table[self.last_state][self.last_action] = 0

        old = self.q_table[self.last_state][self.last_action]
        nm = max(self.q_table[ns].values()) if self.q_table[ns] else 0
        new_val = (1 - self.alpha) * old + self.alpha * (r + self.gamma * nm)
        self.q_table[self.last_state][self.last_action] = new_val

# --- 4. GIAO DIỆN ---
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("STICKMAN Warriors Game")
        self.geometry("1100x750")
        self.configure(bg=THEME['bg'])
        self.resizable(False, False)
        
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TNotebook", background=THEME['bg'], borderwidth=0)
        style.configure("TNotebook.Tab", background="#333", foreground="white", font=("Consolas", 10, "bold"))
        style.map("TNotebook.Tab", background=[("selected", THEME['p1'])], foreground=[("selected", "black")])

        self.db = DataManager()
        self.ai = SmartBrain()
        self.current_user = None
        self.user_data = None
        self.particles = []
        self.stars = []
        for _ in range(40): 
            self.stars.append((random.randint(0, 1100), random.randint(0, 500), random.randint(1, 3)))
            
        self.is_animating = False
        self.current_def_pose = "idle"
        self.show_login_screen()

    def clear_screen(self):
        for w in self.winfo_children():
            widget = w
            widget.destroy()

    def create_neon_btn(self, parent, text, cmd, bg=THEME['btn_bg'], fg=THEME['btn_fg'], w=20, state="normal"):
        b_bg = bg if state == "normal" else THEME['disabled']
        f_col = fg if state == "normal" else "#AAAAAA"
        cursor_type = "hand2" if state == "normal" else "arrow"
        command_fn = cmd if state == "normal" else None
        return tk.Button(parent, text=text, font=("Consolas", 11, "bold"), bg=b_bg, fg=f_col, 
                         activebackground=fg, activeforeground=bg, relief="raised", bd=2, width=w, 
                         cursor=cursor_type, command=command_fn)

    # --- LOGIN & MENU ---
    def show_login_screen(self):
        self.clear_screen()
        f = tk.Frame(self, bg=THEME['bg'])
        f.pack(expand=True)
        tk.Label(f, text="STICKMAN WARRIORS", font=("Impact", 60), bg=THEME['bg'], fg=THEME['p1']).pack(pady=30)
        tk.Label(f, text="USER:", bg=THEME['bg'], fg="white").pack()
        eu = tk.Entry(f, font=("Arial", 14)); eu.pack(pady=5)
        tk.Label(f, text="PASS:", bg=THEME['bg'], fg="white").pack()
        ep = tk.Entry(f, show="*", font=("Arial", 14)); ep.pack(pady=5)
        
        def log():
            s, m, d = self.db.login(eu.get(), ep.get())
            if s:
                self.current_user = eu.get(); self.user_data = d; self.show_menu_screen()
            else: messagebox.showerror("Lỗi", m)
        def reg():
            s, m = self.db.register(eu.get(), ep.get())
            messagebox.showinfo("Thông báo", m)
            
        self.create_neon_btn(f, "ĐĂNG NHẬP", log, bg=THEME['p1'], fg="black").pack(pady=10)
        self.create_neon_btn(f, "ĐĂNG KÝ", reg, bg="#333", fg=THEME['p2']).pack(pady=5)

    def show_menu_screen(self):
        self.clear_screen()
        tk.Label(self, text=f"PLAYER: {self.current_user}", font=("Impact", 35), bg=THEME['bg'], fg="white").pack(pady=20)
        nx = self.user_data['level'] * GAME_CONFIG['exp_base']
        tk.Label(self, text=f"LV: {self.user_data['level']} | EXP: {self.user_data['exp']}/{nx}", font=("Consolas", 14), bg=THEME['bg'], fg="#FFD700").pack()
        f = tk.Frame(self, bg=THEME['bg']); f.pack(pady=30)
        self.create_neon_btn(f, "CHIẾN ĐẤU", self.diff_screen, fg=THEME['p1']).pack(pady=10)
        self.create_neon_btn(f, "CỬA HÀNG", self.shop_screen, fg="#FFFF00").pack(pady=10)
        self.create_neon_btn(f, "QUÀ LEVEL", self.rewards_info, bg="#550055", fg="#FFD700").pack(pady=10)
        self.create_neon_btn(f, "THOÁT", self.show_login_screen, bg="#FF0000", fg="white").pack(pady=10)

    # --- SHOP ---
    def rewards_info(self):
        t = tk.Toplevel(self); t.geometry("400x400"); t.configure(bg="#222")
        tk.Label(t, text="PHẦN THƯỞNG", font=("Impact", 20), bg="#222", fg="yellow").pack(pady=10)
        for lv, r in GAME_CONFIG['rewards'].items():
            st = " [ĐÃ NHẬN]" if self.user_data['level'] >= lv else " [KHÓA]"
            c = "green" if self.user_data['level'] >= lv else "gray"
            tk.Label(t, text=f"Lv {lv}: {r['desc']}{st}", font=("Arial", 12), bg="#222", fg=c).pack(anchor="w", padx=20)

    def shop_screen(self):
        self.clear_screen()
        h = tk.Frame(self, bg=THEME['bg']); h.pack(fill='x', pady=10)
        self.create_neon_btn(h, "< MENU", self.show_menu_screen, w=10).pack(side='left', padx=20)
        tk.Label(h, text=f"SHOP ({self.user_data['gold']}G)", font=("Impact", 25), bg=THEME['bg'], fg="#FFFF00").pack(side='left', padx=50)
        self.create_neon_btn(h, "NẠP", self.deposit, bg="green", fg="white", w=15).pack(side='right', padx=20)
        nb = ttk.Notebook(self); nb.pack(pady=10, expand=True, fill="both", padx=20)
        t1 = tk.Frame(nb, bg=THEME['bg']); nb.add(t1, text=' KỸ NĂNG '); self.render_items(t1, GAME_CONFIG['skills'], 'skills', THEME['p1'])
        t2 = tk.Frame(nb, bg=THEME['bg']); nb.add(t2, text=' SKIN '); self.render_items(t2, GAME_CONFIG['skins'], 'skins', THEME['p2'])

    def render_items(self, p, items, tk_type, col):
        r, c = 0, 0
        for k, v in items.items():
            if tk_type == 'skins' and k == 'default': continue
            f = tk.LabelFrame(p, text=v['name'], bg="#202040", fg=col, font=("Arial", 10, "bold"))
            f.grid(row=r, column=c, padx=10, pady=10, sticky="nsew")
            d = f"Giá: {v['price']}" + (f"\nDMG: {v['dmg']}" if tk_type == 'skills' else "")
            tk.Label(f, text=d, bg="#202040", fg="white").pack(pady=5)
            owned = k in self.user_data[tk_type]
            if owned:
                if tk_type == 'skins':
                    if self.user_data['current_skin'] == v['color']: tk.Label(f, text="[ĐANG DÙNG]", bg="#202040", fg="#00FF00").pack()
                    else: self.create_neon_btn(f, "DÙNG", lambda k=k: self.equip(k), w=10).pack()
                else: tk.Label(f, text="[ĐÃ CÓ]", bg="#202040", fg="gray").pack()
            else: self.create_neon_btn(f, "MUA", lambda k=k: self.buy(tk_type, k), w=10).pack()
            c += 1 
            if c > 2: c = 0; r += 1

    def buy(self, tk_type, k):
        item = GAME_CONFIG[tk_type][k]
        if self.user_data['gold'] >= item['price']:
            self.user_data['gold'] -= item['price']; self.user_data[tk_type].append(k)
            self.db.update(self.current_user, self.user_data); self.shop_screen()
            messagebox.showinfo("OK", f"Mua {item['name']}")
        else: messagebox.showerror("Lỗi", "Thiếu tiền!")
    def equip(self, k):
        self.user_data['current_skin'] = GAME_CONFIG['skins'][k]['color']
        self.db.update(self.current_user, self.user_data); self.shop_screen()
    def deposit(self):
        c = simpledialog.askstring("Nạp", "Code:")
        if c and c in GAME_CONFIG['giftcodes'] and c not in self.user_data['used_codes']:
            self.user_data['gold'] += GAME_CONFIG['giftcodes'][c]
            self.user_data['used_codes'].append(c)
            self.db.update(self.current_user, self.user_data); self.shop_screen(); messagebox.showinfo("OK", "Nạp xong!")
        else: messagebox.showerror("Lỗi", "Sai mã!")

    # --- GAMEPLAY ---
    def diff_screen(self):
        self.clear_screen()
        tk.Label(self, text="ĐỘ KHÓ", font=("Impact", 40), bg=THEME['bg'], fg="white").pack(pady=50)
        f = tk.Frame(self, bg=THEME['bg']); f.pack()
        # Hiển thị số lượt Skill mỗi cấp
        lbl = tk.Label(self, text="Skill +1 mỗi cấp", fg="gray", bg=THEME['bg']); lbl.pack()
        self.create_neon_btn(f, "DỄ", lambda: self.start(1), fg="#00FF00").pack(pady=10)
        self.create_neon_btn(f, "THƯỜNG", lambda: self.start(2), fg="#FFFF00").pack(pady=10)
        self.create_neon_btn(f, "KHÓ", lambda: self.start(3), fg="#FF0000").pack(pady=10)
        self.create_neon_btn(f, "QUAY LẠI", self.show_menu_screen, bg="#333", fg="white").pack(pady=20)

    def start(self, diff):
        # 1. Tính toán HP (Player & Boss)
        lv = self.user_data['level']
        # HP Player: 500 + 150/lv
        self.p_hp = 500 + (lv - 1) * 150
        
        # HP Boss: Base 350 + 50/lv + Diff Bonus
        boss_base = 350 + (lv - 1) * 50
        self.e_hp = boss_base + (diff - 1) * 150
        self.e_max = self.e_hp
        
        self.diff = diff
        self.turn = "player"
        self.particles = []
        
        # 2. Tính toán Skill Limit
        # Limit = Base + (Diff - 1)
        bonus_limit = diff - 1 
        self.p_lim = {}
        for k in self.user_data['skills']:
            base_l = GAME_CONFIG['skills'][k]['limit']
            if base_l < 999:
                self.p_lim[k] = base_l + bonus_limit
            else:
                self.p_lim[k] = 999
                
        self.ai_lim = {}
        for k in GAME_CONFIG['skills']:
            base_l = GAME_CONFIG['skills'][k]['limit']
            if base_l < 999:
                self.ai_lim[k] = base_l + bonus_limit
            else:
                self.ai_lim[k] = 999
        
        self.is_animating = False
        self.current_def_pose = "idle"
        self.game_ui()

    def game_ui(self):
        self.clear_screen()
        self.cv = tk.Canvas(self, width=1100, height=500, bg="black", highlightthickness=0); self.cv.pack(pady=10)
        
        # Thanh Info
        inf = tk.Frame(self, bg=THEME['bg']); inf.pack(fill="x")
        self.lb_p = tk.Label(inf, text=f"HP: {self.p_hp}", font=("Impact", 20), fg=self.user_data['current_skin'], bg=THEME['bg'])
        self.lb_p.pack(side="left", padx=50)
        
        # Nút chức năng
        ctl = tk.Frame(inf, bg=THEME['bg']); ctl.pack(side="top")
        tk.Button(ctl, text="⏸ TẠM DỪNG", bg="#333", fg="white", font=("Arial", 10), command=self.pause_game).pack(side="left", padx=5)
        tk.Button(ctl, text="🏳 ĐẦU HÀNG", bg="red", fg="white", font=("Arial", 10), command=self.surrender).pack(side="left", padx=5)
        
        self.lb_e = tk.Label(inf, text=f"BOSS: {self.e_hp}", font=("Impact", 20), fg=THEME['p2'], bg=THEME['bg'])
        self.lb_e.pack(side="right", padx=50)
        
        self.msg = tk.Label(self, text="FIGHT!", font=("Consolas", 14, "bold"), fg="white", bg=THEME['bg']); self.msg.pack()
        self.btns = tk.Frame(self, bg=THEME['bg']); self.btns.pack(pady=10)
        self.draw_scene(); self.player_turn()

    def pause_game(self):
        # Dùng messagebox để chặn luồng xử lý -> Pause
        messagebox.showinfo("TẠM DỪNG", "Game đang dừng. Bấm OK để tiếp tục.")

    def surrender(self):
        confirm = messagebox.askyesno("ĐẦU HÀNG", "Bạn muốn đầu hàng? (Bị trừ 50 EXP)")
        if confirm:
            if self.user_data['exp'] >= 50:
                self.user_data['exp'] -= 50
            else:
                self.user_data['exp'] = 0
            self.end(False, surrendered=True)

    def draw_chibi(self, x, y, c, is_e, pose="idle"):
        d = -1 if is_e else 1
        self.cv.create_oval(x-30, y-90, x+30, y-30, outline=c, width=3, fill="black")
        self.cv.create_line(x, y-30, x, y+30, fill=c, width=6)
        if pose == "kick":
            self.cv.create_line(x, y+30, x-20*d, y+80, fill=c, width=5)
            self.cv.create_line(x, y+30, x+50*d, y, fill=c, width=5)
        else:
            self.cv.create_line(x, y+30, x-20, y+80, fill=c, width=5)
            self.cv.create_line(x, y+30, x+20, y+80, fill=c, width=5)
        if pose == "beam": 
            self.cv.create_line(x, y-10, x+40*d, y, fill=c, width=5)
        elif pose == "block":
            self.cv.create_line(x, y-10, x+20*d, y-20, fill=c, width=5)
            self.cv.create_arc(x+10*d, y-50, x+40*d, y+30, start=90, extent=180 if is_e else -180, outline="white", width=3, style="arc")
        else:
            self.cv.create_line(x, y-10, x+30*d, y+20, fill=c, width=5)
            self.cv.create_line(x, y-10, x-20*d, y+20, fill=c, width=5)

    def draw_scene(self, pp=None, ep="idle"):
        if pp is None: pp = self.current_def_pose
        try:
            self.cv.delete("all")
            for s in self.stars: self.cv.create_oval(s[0], s[1], s[0]+s[2], s[1]+s[2], fill="white")
            self.cv.create_oval(800, -100, 1100, 200, fill="#220044", outline="")
            self.cv.create_line(0, 420, 1100, 420, fill="white", width=3)
            self.draw_chibi(250, 340, self.user_data['current_skin'], False, pp)
            self.draw_chibi(850, 340, THEME['p2'], True, ep)
            for p in self.particles:
                self.cv.create_oval(p['x'], p['y'], p['x']+p['s'], p['y']+p['s'], fill=p['c'])
                p['x'] += p['dx']; p['y'] += p['dy']; p['life'] -= 1
            self.particles = [p for p in self.particles if p['life'] > 0]
        except: pass

    def fx_explode(self, x, y, c):
        for _ in range(10): 
            self.particles.append({'x':x, 'y':y, 's':random.randint(3,8), 'dx':random.uniform(-10,10), 'dy':random.uniform(-10,10), 'life':10, 'c':c})

    def animate(self, type, who, cb):
        is_p = (who == 'p'); sx, ex = (250, 850) if is_p else (850, 250); d = 1 if is_p else -1
        def draw_beam_fx(bx, ex, width):
            self.cv.create_line(bx, 330, ex, 330, width=width, fill=THEME['beam_out'], tag="fx")
            self.cv.create_line(bx, 330, ex, 330, width=width*0.6, fill=THEME['beam_mid'], tag="fx")
            self.cv.create_line(bx, 330, ex, 330, width=width*0.3, fill=THEME['beam_core'], tag="fx")

        if type == 'melee':
            def s(i):
                if i < 5:
                    cx = sx + (ex-sx-80*d)*(i/5)
                    self.draw_scene(pp="kick" if is_p else None, ep="kick" if not is_p else "idle")
                    if is_p: self.draw_chibi(cx, 340, self.user_data['current_skin'], False, "kick")
                    else: self.draw_chibi(cx, 340, THEME['p2'], True, "kick")
                    self.after(30, lambda:s(i+1))
                elif i == 5:
                    self.fx_explode(ex, 340, "white"); self.after(100, lambda:s(i+1))
                elif i < 10:
                    self.draw_scene(); self.after(30, lambda:s(i+1))
                else: cb()
            s(0)
        elif type == 'beam':
            def b(i):
                if i < 20:
                    self.draw_scene(pp="beam" if is_p else None, ep="beam" if not is_p else "idle")
                    bx = sx + 40*d
                    draw_beam_fx(bx, ex, i*2)
                    self.fx_explode(ex, 340, THEME['beam_out'])
                    self.after(40, lambda:b(i+1))
                else: cb()
            b(0)
        elif type == 'bomb':
            def bm(i):
                if i < 30:
                    prog = i/30; cx = sx + (ex-sx)*prog; cy = 100 + (340-100)*prog
                    self.draw_scene(pp="bomb" if is_p else None, ep="bomb" if not is_p else "idle")
                    self.cv.create_oval(cx-60, cy-60, cx+60, cy+60, fill="#00BFFF", outline="white", tag="fx")
                    self.after(30, lambda:bm(i+1))
                else:
                    self.fx_explode(ex, 340, "cyan"); cb()
            bm(0)
        elif type == 'teleport':
            def t(i):
                if i < 5:
                    self.draw_scene(); self.after(50, lambda:t(i+1))
                elif i == 5:
                    self.draw_scene()
                    if is_p: self.draw_chibi(ex-50*d, 340, self.user_data['current_skin'], False, "kick")
                    else: self.draw_chibi(ex-50*d, 340, THEME['p2'], True, "kick")
                    self.fx_explode(ex, 340, "cyan"); self.after(150, lambda:t(i+1))
                else: cb()
            t(0)
        else: cb()

    def lock_buttons(self):
        self.is_animating = True
        for widget in self.btns.winfo_children():
            widget.config(state="disabled", cursor="arrow")

    def unlock_buttons(self):
        self.is_animating = False
        self.current_def_pose = "idle"
        self.player_turn()

    def player_turn(self):
        for w in self.btns.winfo_children(): w.destroy()
        self.msg.config(text="LƯỢT BẠN!", fg=THEME['p1'])
        for k in sorted(self.user_data['skills'], key=lambda x: GAME_CONFIG['skills'][x]['dmg'][1]):
            rem = self.p_lim[k]
            state = "normal" if rem > 0 else "disabled"
            txt = f"{GAME_CONFIG['skills'][k]['name']} ({rem})"
            self.create_neon_btn(self.btns, txt, lambda k=k: self.p_atk(k), state=state).pack(side="left", padx=5)

    def p_atk(self, k):
        if self.is_animating: return
        self.lock_buttons()
        self.p_lim[k] -= 1
        def on_complete():
            self.draw_scene(); self.apply_dmg(k, 'p')
        self.animate(GAME_CONFIG['skills'][k]['type'], 'p', on_complete)

    def apply_dmg(self, k, who):
        dmg = random.randint(*GAME_CONFIG['skills'][k]['dmg'])
        if who == 'p':
            self.e_hp -= dmg
            self.msg.config(text=f"TRÚNG: -{dmg}")
            self.lb_e.config(text=f"BOSS: {self.e_hp}") 
            self.ai.learn(self.e_hp, self.p_hp, 500*self.diff, -dmg/10)
            if self.e_hp <= 0: self.end(True)
            else: self.after(1000, self.enemy_turn)
        else:
            self.p_hp -= dmg
            self.msg.config(text=f"BỊ ĐÁNH: -{dmg}", fg="red")
            self.lb_p.config(text=f"HP: {self.p_hp}") 
            self.ai.learn(self.e_hp, self.p_hp, 500*self.diff, dmg/5)
            if self.p_hp <= 0: self.end(False)
            else: self.after(1000, self.unlock_buttons)

    def enemy_turn(self):
        self.msg.config(text="AI ĐANG TÍNH...", fg=THEME['p2'])
        avail = [k for k,v in self.ai_lim.items() if v > 0]
        if not avail: avail = ['dam_nhe']
        self.ai_key = self.ai.choose_action(self.e_hp, self.p_hp, 500*self.diff, avail)
        self.ai_lim[self.ai_key] -= 1
        self.after(800, self.def_ui)

    def def_ui(self):
        self.msg.config(text=f"AI DÙNG: {GAME_CONFIG['skills'][self.ai_key]['name']}")
        for w in self.btns.winfo_children(): w.destroy()
        self.create_neon_btn(self.btns, "KHIÊN THẦN (-50 gold)", lambda: self.res_def(True), bg="orange").pack(side="left", padx=10)
        self.create_neon_btn(self.btns, "NÉ", lambda: self.res_def(False), bg="red").pack(side="left", padx=10)

    def res_def(self, block):
        def ai_done():
            self.draw_scene(); self.apply_dmg(self.ai_key, 'e')
        
        # Hàm xử lý khi đỡ đòn (AI đánh xong mới trừ máu)
        def after_ai_atk_block():
            self.draw_scene() # Vẽ lại cảnh bình thường
            # Tính damage
            dmg_raw = random.randint(*GAME_CONFIG['skills'][self.ai_key]['dmg'])
            dmg = int(dmg_raw * 0.1) # Giảm 90%
            self.msg.config(text=f"ĐÃ ĐỠ! Mất {dmg} HP", fg="orange")
            self.p_hp -= dmg
            self.lb_p.config(text=f"HP: {self.p_hp}")
            if self.p_hp <= 0: self.end(False)
            else: self.after(1000, self.unlock_buttons)

        if block:
            if self.user_data['gold'] >= 50:
                self.user_data['gold'] -= 50
                self.current_def_pose = "block" # Chuyển pose thành block
                self.draw_scene()
                # Gọi AI đánh, nhưng truyền pose của player là "block" để giữ nguyên hình ảnh
                self.animate(GAME_CONFIG['skills'][self.ai_key]['type'], 'e', after_ai_atk_block)
            else: messagebox.showwarning("Lỗi", "Hết tiền!")
        else:
            # NERF NÉ: Tỷ lệ 40% (0.4)
            if random.random() < 0.4:
                self.msg.config(text="NÉ THÀNH CÔNG!", fg="green")
                self.after(1000, self.unlock_buttons)
            else:
                self.animate(GAME_CONFIG['skills'][self.ai_key]['type'], 'e', ai_done)

    def end(self, win, surrendered=False):
        rw = 100 * self.diff
        self.ai.save_memory()
        
        if win:
            self.user_data['gold'] += rw
            self.user_data['exp'] += rw * 2
            req = self.user_data['level'] * GAME_CONFIG['exp_base']
            if self.user_data['exp'] >= req:
                self.user_data['level'] += 1; self.user_data['exp'] -= req
                msg = f"LÊN CẤP {self.user_data['level']}!"
                r = GAME_CONFIG['rewards'].get(self.user_data['level'])
                if r:
                    msg += f"\nNhận: {r['desc']}"
                    if r['type'] == 'gold': self.user_data['gold'] += r['val']
                    if r['type'] == 'hp': self.user_data['hp_max'] += r['val']
                    if r['type'] == 'skin' and r['val'] not in self.user_data['skins']: self.user_data['skins'].append(r['val'])
                messagebox.showinfo("LEVEL UP", msg)
            else: messagebox.showinfo("THẮNG", f"+{rw} Vàng | +{rw*2} EXP")
        else:
            msg = "ĐẦU HÀNG (-50 EXP)" if surrendered else "THUA CUỘC (-50 EXP)"
            if not surrendered: # Nếu thua thường cũng trừ EXP (cho đồng bộ)
                 if self.user_data['exp'] >= 50: self.user_data['exp'] -= 50
                 else: self.user_data['exp'] = 0
            messagebox.showinfo("THUA - CHICKEN!", msg)
            
        self.db.update(self.current_user, self.user_data)
        self.show_menu_screen()

if __name__ == "__main__":
    App().mainloop()