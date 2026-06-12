import tkinter as tk
import socket
import threading
import random
import string
from PIL import Image, ImageTk
import uuid
import ast
import json
import time

with open('config.json', 'r') as f:
    config = json.load(f)

HOST = config.get("host", "127.0.0.1")
PORT = config.get("port", 28282)
BOATS_CONFIG = config.get("boats", {})
TOTAL_BOATS = sum(info["count"] for info in BOATS_CONFIG.values())

icones = {
    "welcome": r"img\boats\accueil.png",
    "icone": r"img\boats\icone.ico",
    "water": r"img\water\water.png"
}
resize_dims = {"welcome": (290, 315), "water": (35, 35)}

for b_name, b_info in BOATS_CONFIG.items():
    length = b_info["length"]
    b_num = b_name.split('_')[1]
    icones[b_name] = f"img\\boats\\{b_name}.png"
    resize_dims[b_name] = (40 * length, 40) 
    if length == 1:
        icones[f"b{b_num}"] = f"img\\boats\\box\\b{b_num}.png"
        resize_dims[f"b{b_num}"] = (35, 35)
    else:
        for i in range(1, length + 1):
            icones[f"b{b_num}_{i}"] = f"img\\boats\\box\\b{b_num}_{i}.png"
            resize_dims[f"b{b_num}_{i}"] = (35, 35)

my_pseudo = ""
pwd = ''
players_list_str = "En attente du serveur..."
players_label_ref = None
main_root_ref = None
current_window = None
imgs = {}
your_turn = False
login_root_ref = None
my_final_boats = {}  
game_status_label = None
boats_count_label = None
my_canvas = None
enemy_canvas = None
chat_box = None
err_lbl = None
CELL_SIZE = 35

# Dictionnaire de stockage des IDs Tkinter des sections de nos bateaux sur my_canvas
# Clé : coordonée tuple (x,y) -> Valeur : id de l'image sur le canvas
my_canvas_boat_sections = {}

def style_button(btn, bg_color, fg_color):
    btn.config(bg=bg_color, fg=fg_color, font=("Arial", 10, "bold"), relief="raised", bd=3, padx=10, pady=5)
    btn.bind("<Enter>", lambda e: btn.config(bg=fg_color, fg=bg_color))
    btn.bind("<Leave>", lambda e: btn.config(bg=bg_color, fg=fg_color))

def login_screen():
    """Écran d'accueil pour l'authentification."""
    global s, my_pseudo, login_root_ref, err_lbl
    
    login_root = tk.Tk()
    login_root_ref = login_root
    login_root.title("Connexion - Bataille Navale")
    login_root.geometry("320x220")
    login_root.resizable(False, False)
    
    tk.Label(login_root, text="Saisissez votre Pseudo :", font=("Arial", 12, "bold")).pack(pady=20)
    pseudo_entry = tk.Entry(login_root, font=("Arial", 12), width=18, justify="center")
    pseudo_entry.pack(pady=5)
    pseudo_entry.insert(0, f"Player_{random.randint(10,99)}")

    err_lbl = tk.Label(login_root, text="", fg="red", font=("Arial", 9))
    err_lbl.pack()

    def submit_auth():
        global my_pseudo
        chosen = pseudo_entry.get().strip().replace(" ", "_")
        if not chosen: return
        my_pseudo = chosen
        try:
            # On envoie la commande d'identification attendue par votre serveur
            # Note : Votre serveur d'origine utilise "ID <pseudo>", et non "AUTH <pseudo>"
            s.sendall(f"ID {chosen}\n".encode())
        except Exception as e:
            err_lbl.config(text="Impossible de joindre le serveur.")

    btn = tk.Button(login_root, text="Entrer en jeu", command=submit_auth)
    btn.pack(pady=15)
    
    # Lancement de la fenêtre de login en premier !
    login_root.mainloop()

def tkinter_menu(socket_obj):
    global icones, main_root_ref, imgs
    main_root = tk.Tk()
    main_root_ref = main_root
    main_root.title(f"Menu - {my_pseudo}")
    main_root.resizable(False, False)

    def load_img(images):
        loaded_img = {}
        for n_img, p_img in images.items():
            if p_img.endswith(".ico"): continue
            try:
                pil_img = Image.open(p_img)
                if n_img in resize_dims:
                    target_size = resize_dims[n_img]
                    pil_img.thumbnail(target_size, Image.Resampling.LANCZOS)
                    background = Image.new("RGBA", target_size, (0, 0, 0, 0))
                    x = (target_size[0] - pil_img.width) // 2
                    y = (target_size[1] - pil_img.height) // 2
                    background.paste(pil_img, (x, y), pil_img)
                    pil_img = background
                loaded_img[n_img] = {"tk": ImageTk.PhotoImage(pil_img), "pil": pil_img}
            except:
                size = resize_dims.get(n_img, (35, 35))
                fallback_img = Image.new("RGBA", size, color=(50, 120, 180, 255))
                loaded_img[n_img] = {"tk": ImageTk.PhotoImage(fallback_img), "pil": fallback_img}
        return loaded_img
    
    imgs = load_img(icones)
    if "welcome" in imgs: tk.Label(main_root, image=imgs["welcome"]["tk"]).grid()
        
    btn_create = tk.Button(text="Créer Partie", command=lambda: create_game(socket_obj))
    btn_create.place(relx=0.25, rely=0.88, anchor="center")
    style_button(btn_create, "#2c3e50", "white")

    btn_join = tk.Button(text="Rejoindre", command=lambda: join_game(socket_obj))
    btn_join.place(relx=0.75, rely=0.88, anchor="center")
    style_button(btn_join, "#27ae60", "white")

    def join_game(s):
        global players_label_ref, current_window
        main_root.withdraw()
        join_root = tk.Toplevel(main_root)
        current_window = join_root
        join_root.title("Lobby d'attente")
        if "welcome" in imgs: tk.Label(join_root, image=imgs["welcome"]["tk"]).grid()
        players_label = tk.Label(join_root, text=players_list_str, justify="left", font=("Arial", 12, "bold"), fg="#2980b9")
        players_label.place(relx=0.5, rely=0.2, anchor="center")
        players_label_ref = players_label
        tk.Label(join_root, text="Code secret :", font=("Arial", 10, "bold")).place(relx=0.05, rely=0.85, anchor="w")
        code_entry = tk.Entry(join_root, font=("Arial", 12), width=10)
        code_entry.place(relx=0.35, rely=0.85, anchor="w")
        tk.Button(join_root, text="Connexion", command=lambda: s.sendall(f'Join {code_entry.get()}'.encode())).place(relx=0.8, rely=0.85, anchor="center")
        join_root.protocol("WM_DELETE_WINDOW", lambda: [join_root.destroy(), main_root.deiconify()])

    def create_game(s):
        global pwd, players_label_ref, current_window
        main_root.withdraw()
        create_root = tk.Toplevel(main_root)
        current_window = create_root
        create_root.title("Création de Salon")
        if "welcome" in imgs: tk.Label(create_root, image=imgs["welcome"]["tk"]).grid()
        players_label = tk.Label(create_root, text=players_list_str, justify="left", font=("Arial", 12, "bold"), fg="#27ae60")
        players_label.place(relx=0.5, rely=0.2, anchor="center")
        players_label_ref = players_label
        s.sendall(b'Create')
        code_entry = tk.Entry(create_root, font=("Arial", 12, "bold"), width=10, fg="darkgreen")
        code_entry.place(relx=0.35, rely=0.85, anchor="w")

        def check_pwd():
            global pwd
            if pwd != '':
                code_entry.config(state="normal")
                code_entry.delete(0, tk.END)
                code_entry.insert(0, pwd)
                code_entry.config(state="readonly")
            else: create_root.after(100, check_pwd)
        check_pwd()
        tk.Button(create_root, text="Lancer Combat", command=lambda: s.sendall(f'START {code_entry.get()}'.encode())).place(relx=0.85, rely=0.85, anchor="center")
        create_root.protocol("WM_DELETE_WINDOW", lambda: [create_root.destroy(), main_root.deiconify()])

    main_root.mainloop()

def mailbox(s):
    global num, completed_grid, pwd, players_list_str, players_label_ref, start
    global enough_player, your_turn, status_label, enemy_canva
    global login_root_ref, err_lbl

    buffer = ""

    while True:
        try:
            data = s.recv(1024).decode()
            if not data: break
            buffer += data

            while "\n" in buffer:
                msg, buffer = buffer.split("\n", 1)
                msg = msg.strip()
                if not msg: continue

                print("RECV:", msg)

                # -------- ID VALIDATION (DÉBLOCAGE DU MENU) --------
                if msg == "ID_g":
                    print("Pseudo validé par le serveur. Passage au menu.")
                    if login_root_ref and login_root_ref.winfo_exists():
                        # .after(0, ...) est obligatoire pour demander à Tkinter de modifier les fenêtres depuis un thread secondaire
                        login_root_ref.after(0, lambda: [login_root_ref.destroy(), tkinter_menu(s)])
                    continue

                if msg == "ID_b":
                    print("Pseudo déjà refusé ou existant.")
                    if login_root_ref and login_root_ref.winfo_exists() and err_lbl:
                        login_root_ref.after(0, lambda: err_lbl.config(text="Ce pseudo est déjà utilisé."))
                    continue

                # -------- VOTRE CODE DE MAILBOX ADVERSAIRE / GRILLE EXISTANT DÉJÀ --------
                if msg.startswith("Player"):
                    parts = msg.split(" ")
                    num = parts[1]
                    print(f"You are Player {num}")
                    continue

                if msg.startswith("Code"): pwd = msg.split(" ")[1]
                elif msg.startswith("PLAYERS_LIST"):
                    raw_list = msg.split(" ")[1]
                    list_players = raw_list.split(",")
                    players_list_str = f"Flottes en présence :\n" + "\n".join([f"⚓ {p}" for p in list_players])
                    if players_label_ref and players_label_ref.winfo_exists(): players_label_ref.config(text=players_list_str)
                elif msg == "GAME_FULL":
                    if players_label_ref and players_label_ref.winfo_exists(): players_label_ref.config(text="Erreur : Salon Complet !", fg="red")
                elif msg.startswith("START"): main_root_ref.after(0, open_placement_window)
                elif msg == "GAME_START": main_root_ref.after(0, open_main_game_window)
                elif msg == "RECONNECT_OK": main_root_ref.after(0, open_main_game_window)
                
                elif msg.startswith("RESTORE_STATE "):
                    # Reconstruction complète de la grille de combat lors d'une reconnexion forcée
                    parts = msg.split("RESTORE_STATE ", 1)[1].split(" | ")
                    my_final_boats = ast.literal_eval(parts[0])
                    shots_taken = ast.literal_eval(parts[1])
                    shots_received = ast.literal_eval(parts[2])
                    is_my_turn = parts[3] == "True"
                    
                    main_root_ref.after(0, open_main_game_window)
                    main_root_ref.after(100, lambda st=shots_taken, sr=shots_received, it=is_my_turn: restore_ui_state(st, sr, it))

                elif msg == "YOUR_TURN":
                    your_turn = True
                    main_root_ref.after(0, lambda: game_status_label.config(text="🔴 À VOUS DE TIRER !", fg="#e74c3c"))
                
                elif msg.startswith("HIT "):
                    _, x, y = msg.split()
                    main_root_ref.after(0, lambda: play_fire_animation(enemy_canvas, int(x), int(y), "HIT"))
                elif msg.startswith("MISS "):
                    _, x, y = msg.split()
                    main_root_ref.after(0, lambda: play_fire_animation(enemy_canvas, int(x), int(y), "MISS"))
                elif msg.startswith("HIT_BY"):
                    _, x, y = msg.split()
                    main_root_ref.after(0, lambda: play_fire_animation(my_canvas, int(x), int(y), "HIT_BY"))
                elif msg.startswith("MISS_BY"):
                    _, x, y = msg.split()
                    main_root_ref.after(0, lambda: play_fire_animation(my_canvas, int(x), int(y), "MISS_BY"))
                
                elif msg.startswith("SUNK_ENEMY"):
                    _, b_id, alive = msg.split()
                    main_root_ref.after(0, lambda b=b_id, a=alive: [
                        game_status_label.config(text=f"☠️ COULÉ ! {b.split('_')[1]} adverse détruit !", fg="darkgreen"),
                        boats_count_label.config(text=f"Bateaux ennemis restants : {a} / {TOTAL_BOATS}")
                    ])
                elif msg.startswith("SUNK_YOU"):
                    _, b_id = msg.split()
                    main_root_ref.after(0, lambda b=b_id: [
                        game_status_label.config(text=f"⚠️ ALERTE : Votre {b.split('_')[1]} a sombré !", fg="darkred"),
                        tint_boat_sunk(b)
                    ])

                elif msg.startswith("CHAT "):
                    chat_line = msg.split("CHAT ", 1)[1]
                    main_root_ref.after(0, lambda cl=chat_line: [
                        chat_box.config(state="normal"),
                        chat_box.insert(tk.END, cl + "\n"),
                        chat_box.config(state="disabled"),
                        chat_box.see(tk.END)
                    ])

                elif msg.startswith("OPPONENT_TEMPORARY_DISCONNECTED"):
                    main_root_ref.after(0, lambda: game_status_label.config(text="⏳ Connexion adverse perdue... Attente (30s max)", fg="orange"))
                elif msg.startswith("OPPONENT_BACK"):
                    main_root_ref.after(0, lambda: game_status_label.config(text="Adversaire de retour ! Reprise du combat.", fg="green"))
                elif msg == "OPPONENT_TIMEOUT_DISCONNECTED":
                    main_root_ref.after(0, lambda: show_end_screen("VICTOIRE PAR FORFAIT (Adversaire expiré)", "gold", ""))

                elif msg.startswith("STATS "):
                    latest_stats = msg.split("STATS ", 1)[1] # precision miss best_boat
                elif msg == "WIN":
                    main_root_ref.after(0, lambda: show_end_screen("VICTOIRE NAVALE !", "#27ae60", latest_stats))
                elif msg == "LOSE":
                    main_root_ref.after(0, lambda: show_end_screen("FLOTTE DÉTRUITE... DÉFAITE", "#c0392b", latest_stats))
        except: break

def play_fire_animation(canvas, x, y, status, step=0):
    """Génère l'animation d'un obus (clignotement jaune/orange) avant l'impact."""
    cx, cy = x * CELL_SIZE + CELL_SIZE // 2, y * CELL_SIZE + CELL_SIZE // 2
    if step < 4:
        color = "orange" if step % 2 == 0 else "yellow"
        oval = canvas.create_oval(cx-12, cy-12, cx+12, cy+12, fill=color, outline="red")
        main_root_ref.after(80, lambda: [canvas.delete(oval), play_fire_animation(canvas, x, y, status, step+1)])
    else:
        # Fin d'animation -> Application définitive des marqueurs graphiques
        if status in ["HIT", "HIT_BY"]:
            canvas.create_line(cx-10, cy-10, cx+10, cy+10, fill="#e74c3c", width=3)
            canvas.create_line(cx+10, cy-10, cx-10, cy+10, fill="#e74c3c", width=3)
            if status == "HIT": game_status_label.config(text="💥 TOUCHÉ !", fg="#e74c3c")
        else:
            canvas.create_oval(cx-5, cy-5, cx+5, cy+5, fill="white", outline="#7f8c8d", width=1)
            if status == "MISS": game_status_label.config(text="💧 DANS L'EAU...", fg="#3498db")

def tint_boat_sunk(boat_id):
    """Teinte en noir/gris foncé toutes les sections du bateau coulé."""
    global my_canvas, my_final_boats
    if boat_id not in my_final_boats: return
    
    # Récupérer la structure géométrique du bateau
    x, y, orient = my_final_boats[boat_id]
    b_name = "_".join(boat_id.split("_")[:2])
    length = BOATS_CONFIG[b_name]["length"]
    vx, vy = (1, 0) if orient == "e" else (0, 1) if orient == "s" else (-1, 0) if orient == "o" else (0, -1)
    
    for i in range(length):
        tx, ty = x + vx*i, y + vy*i
        if (tx, ty) in my_canvas_boat_sections:
            tk_id = my_canvas_boat_sections[(tx, ty)]
            # Applique un rectangle gris translucide/sombre sur le canvas au-dessus de la section
            my_canvas.create_rectangle(tx*CELL_SIZE, ty*CELL_SIZE, (tx+1)*CELL_SIZE, (ty+1)*CELL_SIZE, fill="#1e272e", stipple="gray50")

def restore_ui_state(shots_taken, shots_received, is_my_turn):
    """Recrée visuellement les tirs après une reconnexion réseau."""
    global your_turn, game_status_label
    your_turn = is_my_turn
    game_status_label.config(text="🔴 À VOUS DE TIRER !" if your_turn else "En attente du tir adverse...", fg="#e74c3c" if your_turn else "gray")
    
    for (x, y) in shots_taken:
        cx, cy = x * CELL_SIZE + CELL_SIZE // 2, y * CELL_SIZE + CELL_SIZE // 2
        # Ne pouvant recalculer le hit exact instantanément, on replace la marque rouge/blanche standard de présence
        enemy_canvas.create_oval(cx-4, cy-4, cx+4, cy+4, fill="red", outline="white")
    for (x, y) in shots_received:
        cx, cy = x * CELL_SIZE + CELL_SIZE // 2, y * CELL_SIZE + CELL_SIZE // 2
        my_canvas.create_oval(cx-4, cy-4, cx+4, cy+4, fill="black", outline="red")

def open_placement_window():
    global current_window, imgs, my_final_boats
    if current_window and current_window.winfo_exists(): current_window.destroy()

    place_root = tk.Toplevel(main_root_ref)
    place_root.title("Quartier Maître - Placement des Navires")
    current_window = place_root
    place_root.geometry("720x620")
    place_root.config(bg="#f5f6fa")

    canva = tk.Canvas(place_root, width=690, height=520, bg="#dcdde1", relief="sunken", bd=4)
    canva.pack(pady=10)
    status_lbl = tk.Label(place_root, text="Glissez les bateaux. 'R' pour pivoter.", font=("Arial", 11, "italic"), bg="#f5f6fa")
    status_lbl.pack()

    step = 41
    grid = [[None]*10 for _ in range(10)]
    selected_boat = None

    for y in range(10):
        for x in range(10): canva.create_image(240 + step*x, 40 + step*y, image=imgs["water"]["tk"])

    boat_list = []
    x_offset, y_offset = 20, 40
    
    for b_name, b_info in BOATS_CONFIG.items():
        for b_idx in range(b_info["count"]):
            length = b_info["length"]
            b_num = b_name.split("_")[1]
            parts = [imgs[f"b{b_num}"]["tk"]] if length == 1 else [imgs[f"b{b_num}_{i}"]["tk"] for i in range(1, length + 1)]
            boat_id = canva.create_image(x_offset + (length*step)//2, y_offset, image=imgs[b_name]["tk"])
            
            boat_list.append({
                "id": boat_id, "uid": str(uuid.uuid4()), "ship_id": f"{b_name}_{b_idx}",
                "name": b_name, "length": length, "parts": parts, "base_pos": (x_offset + (length*step)//2, y_offset),
                "angle": 0, "ids": []
            })
            y_offset += 45
            if y_offset > 450: y_offset = 40; x_offset += 80

    def select_boat(e):
        nonlocal selected_boat
        items = canva.find_overlapping(e.x, e.y, e.x, e.y)
        for b in boat_list:
            if b["id"] in items or any(pid in items for pid in b["ids"]):
                selected_boat = b; break

    def drag(e):
        if not selected_boat: return
        if not selected_boat["ids"]: canva.coords(selected_boat["id"], e.x, e.y)
        else:
            dx = e.x - canva.coords(selected_boat["ids"][0])[0]
            dy = e.y - canva.coords(selected_boat["ids"][0])[1]
            for pid in selected_boat["ids"]: canva.move(pid, dx, dy)

    def rotate(e):
        if not selected_boat: return
        b = selected_boat
        b["angle"] = (b["angle"] + 90) % 360
        b_num = b["name"].split("_")[1]
        keys = [f"b{b_num}"] if b["length"] == 1 else [f"b{b_num}_{i}" for i in range(1, b["length"] + 1)]
        if b["angle"] in [180, 270]: keys.reverse()
        new_parts = []
        for k in keys:
            rot = imgs[k]["pil"].rotate(-b["angle"], expand=True)
            new_parts.append(ImageTk.PhotoImage(rot))
        b["rotated_tks"] = new_parts

    def drop(e):
        nonlocal selected_boat, grid
        if not selected_boat: return
        b = selected_boat
        x = max(0, min(9, round((e.x - 240) / step)))
        y = max(0, min(9, round((e.y - 40) / step)))
        vx, vy = (1, 0) if b["angle"] == 0 else (0, 1) if b["angle"] == 90 else (-1, 0) if b["angle"] == 180 else (0, -1)

        for yy in range(10):
            for xx in range(10):
                if grid[yy][xx] == b["uid"]: grid[yy][xx] = None

        valid = True
        for i in range(b["length"]):
            tx, ty = x + vx*i, y + vy*i
            if not (0 <= tx < 10 and 0 <= ty < 10) or grid[ty][tx] is not None:
                valid = False; break

        if valid:
            for pid in b["ids"]: canva.delete(pid)
            canva.delete(b["id"])
            b["ids"] = []
            tks = b.get("rotated_tks", b["parts"])
            for i, tk_p in enumerate(tks):
                px = 240 + step*(x + vx*i)
                py = 40 + step*(y + vy*i)
                b["ids"].append(canva.create_image(px, py, image=tk_p))
                grid[y + vy*i][x + vx*i] = b["uid"]
            orient = "e" if b["angle"] == 0 else "s" if b["angle"] == 90 else "o" if b["angle"] == 180 else "n"
            my_final_boats[b["ship_id"]] = (x, y, orient)
        else:
            for pid in b["ids"]: canva.delete(pid)
            b["ids"] = []
            canva.delete(b["id"])
            b["id"] = canva.create_image(b["base_pos"][0], b["base_pos"][1], image=imgs[b["name"]]["tk"])
            if b["ship_id"] in my_final_boats: del my_final_boats[b["ship_id"]]
        selected_boat = None

    canva.bind("<Button-1>", select_boat)
    canva.bind("<B1-Motion>", drag)
    canva.bind("<ButtonRelease-1>", drop)
    place_root.bind("<KeyPress-r>", rotate)

    def validate():
        if len(my_final_boats) < TOTAL_BOATS:
            status_lbl.config(text="Alerte : Tous vos navires ne sont pas placés !", fg="#c0392b")
            return
        s.sendall(f"GRID {my_final_boats}\n".encode())
        status_lbl.config(text="En attente de la flotte adverse...", fg="#27ae60")
        validate_btn.config(state="disabled")

    validate_btn = tk.Button(place_root, text="Valider la Disposition", command=validate)
    validate_btn.pack(pady=5)
    style_button(validate_btn, "#2c3e50", "white")

def open_main_game_window():
    global current_window, game_status_label, boats_count_label, my_canvas, enemy_canvas, CELL_SIZE, chat_box, my_canvas_boat_sections
    if current_window and current_window.winfo_exists(): current_window.destroy()

    game_root = tk.Toplevel(main_root_ref)
    game_root.title(f"Poste de Commandement Naval - {my_pseudo}")
    game_root.geometry("860x660")
    game_root.config(bg="#f5f6fa")

    game_status_label = tk.Label(game_root, text="Initialisation des liaisons tactiques...", font=("Arial", 14, "bold"), bg="#f5f6fa", fg="#7f8c8d")
    game_status_label.pack(pady=5)

    boats_count_label = tk.Label(game_root, text=f"Bateaux ennemis restants : {TOTAL_BOATS} / {TOTAL_BOATS}", font=("Arial", 11, "bold"), bg="#f5f6fa", fg="#2c3e50")
    boats_count_label.pack(pady=2)

    tables_frame = tk.Frame(game_root, bg="#f5f6fa")
    tables_frame.pack(pady=5)

    my_frame = tk.Frame(tables_frame, bg="#f5f6fa")
    my_frame.grid(row=0, column=0, padx=25)
    tk.Label(my_frame, text="VOTRE FLOTTE", font=("Arial", 11, "bold"), bg="#f5f6fa", fg="#2c3e50").pack(pady=2)
    my_canvas = tk.Canvas(my_frame, width=350, height=350, bg="#cbd5e0", relief="groove", bd=3)
    my_canvas.pack()

    enemy_frame = tk.Frame(tables_frame, bg="#f5f6fa")
    enemy_frame.grid(row=0, column=1, padx=25)
    tk.Label(enemy_frame, text="RADAR TACTIQUE", font=("Arial", 11, "bold"), bg="#f5f6fa", fg="#c0392b").pack(pady=2)
    enemy_canvas = tk.Canvas(enemy_frame, width=350, height=350, bg="#2f3542", relief="groove", bd=3)
    enemy_canvas.pack()

    for y in range(10):
        for x in range(10):
            my_canvas.create_image(x*CELL_SIZE + CELL_SIZE//2, y*CELL_SIZE + CELL_SIZE//2, image=imgs["water"]["tk"])
            enemy_canvas.create_rectangle(x*CELL_SIZE, y*CELL_SIZE, (x+1)*CELL_SIZE, (y+1)*CELL_SIZE, fill="#2f3542", outline="#57606f")

    my_canvas_boat_sections.clear()
    for ship_id, (x, y, orient) in my_final_boats.items():
        b_name = "_".join(ship_id.split("_")[:2])
        b_num = b_name.split("_")[1]
        length = BOATS_CONFIG[b_name]["length"]
        vx, vy = (1, 0) if orient == "e" else (0, 1) if orient == "s" else (-1, 0) if orient == "o" else (0, -1)
        angle = 0 if orient == "e" else 90 if orient == "s" else 180 if orient == "o" else 270
        keys = [f"b{b_num}"] if length == 1 else [f"b{b_num}_{i}" for i in range(1, length + 1)]
        if angle in [180, 270]: keys.reverse()

        for i, k in enumerate(keys):
            rot = imgs[k]["pil"].rotate(-angle, expand=True).resize((CELL_SIZE, CELL_SIZE), Image.Resampling.LANCZOS)
            img_tk = ImageTk.PhotoImage(rot)
            if "finals" not in imgs: imgs["finals"] = []
            imgs["finals"].append(img_tk)
            
            tx, ty = x + vx*i, y + vy*i
            tk_id = my_canvas.create_image(tx*CELL_SIZE + CELL_SIZE//2, ty*CELL_SIZE + CELL_SIZE//2, image=img_tk)
            my_canvas_boat_sections[(tx, ty)] = tk_id

    def enemy_click(e):
        global your_turn
        if not your_turn: return
        x, y = e.x // CELL_SIZE, e.y // CELL_SIZE
        if 0 <= x < 10 and 0 <= y < 10:
            s.sendall(f"SHOOT {x} {y}\n".encode())
            your_turn = False
            game_status_label.config(text="🌐 Obus en route...", fg="#f39c12")

    enemy_canvas.bind("<Button-1>", enemy_click)

    # --- ZONE DE CHAT EN DIRECT ---
    chat_frame = tk.Frame(game_root, bg="#f5f6fa")
    chat_frame.pack(pady=10, fill="x", padx=30)
    
    chat_box = tk.Text(chat_frame, height=5, width=80, font=("Arial", 10), state="disabled", bg="#ffffff", relief="solid", bd=1)
    chat_box.pack(pady=2)
    
    entry_frame = tk.Frame(chat_frame, bg="#f5f6fa")
    entry_frame.pack(fill="x")
    
    chat_entry = tk.Entry(entry_frame, font=("Arial", 11), width=65)
    chat_entry.pack(side="left", padx=2, pady=2)
    
    def send_chat_msg():
        msg = chat_entry.get().strip()
        if msg:
            s.sendall(f"CHAT {msg}\n".encode())
            chat_entry.delete(0, tk.END)

    chat_entry.bind("<Return>", lambda e: send_chat_msg())
    btn_send = tk.Button(entry_frame, text="Envoyer", command=send_chat_msg)
    btn_send.pack(side="right", padx=2)
    style_button(btn_send, "#2980b9", "white")

def show_end_screen(title_text, color, stats_str):
    """Écran de fin enrichi affichant les statistiques précises du serveur."""
    global current_window
    if current_window and current_window.winfo_exists(): current_window.destroy()

    end_root = tk.Toplevel(main_root_ref)
    end_root.title("Rapport de Fin de Bataille")
    end_root.geometry("450x380")
    end_root.config(bg="#2c3e50")
    current_window = end_root

    tk.Label(end_root, text=title_text, font=("Arial", 16, "bold"), fg=color, bg="#2c3e50").pack(pady=20)

    # Formatage des stats issues du serveur : "precision miss best_boat"
    if stats_str:
        try:
            prec, miss, boat = stats_str.split()
            stats_text = (
                f"📊 STATISTIQUES DE GUERRE :\n\n"
                f"🎯 Précision des tirs : {prec}%\n"
                f"💧 Nombre d'obus manqués : {miss}\n"
                f"🛡️ Meilleur survivant : {boat.replace('_', ' ')}"
            )
        except:
            stats_text = "Statistiques indisponibles."
    else:
        stats_text = "Fin prématurée : Pas de données."

    lbl_stats = tk.Label(end_root, text=stats_text, font=("Courier New", 11, "bold"), fg="#ecf0f1", bg="#34495e", relief="solid", bd=2, padx=15, pady=15, justify="left")
    lbl_stats.pack(pady=15)

    btn_frame = tk.Frame(end_root, bg="#2c3e50")
    btn_frame.pack(pady=10)

    btn_retry = tk.Button(btn_frame, text="Menu Principal", command=lambda: [end_root.destroy(), main_root_ref.deiconify()])
    btn_retry.grid(row=0, column=0, padx=15)
    style_button(btn_retry, "#27ae60", "white")

    btn_quit = tk.Button(btn_frame, text="Quitter", command=main_root_ref.quit)
    btn_quit.grid(row=0, column=1, padx=15)
    style_button(btn_quit, "#7f8c8d", "white")

try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))
    
    # 1. On lance le thread d'écoute réseau en arrière-plan
    threading.Thread(target=mailbox, args=(s,), daemon=True).start()
    
    # 2. On affiche l'écran de login (qui va bloquer le script principal ici via son mainloop)
    login_screen()

except ConnectionRefusedError:
    print("The server is offline. Please restart later.")