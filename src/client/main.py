import tkinter as tk
import socket
import threading
import time
import random, string
from PIL import Image, ImageTk, ImageOps
import uuid

print("-----------------------------------------")
print("|                                       |")
print("|           Connexion en cours          |")
print("|                                       |")
print("-----------------------------------------")

# Images
icones={
    "boat_1": r"img\\boats\\boat_1.png",
    "boat_2": r"img\\boats\\boat_2.png",
    "boat_3": r"img\\boats\\boat_3.png",
    "welcome": r"img\\boats\\accueil.png",
    "icone": r"img\\boats\\icone.ico",
    "water": r"img\\water\\water.png",
    "b1": r"img\\boats\\box\\b1.png",
    "b2_1": r"img\\boats\\box\\b2_1.png",
    "b2_2": r"img\\boats\\box\\b2_2.png",
    "b3_1": r"img\\boats\\box\\b3_1.png",
    "b3_2": r"img\\boats\\box\\b3_2.png",
    "b3_3": r"img\\boats\\box\\b3_3.png"
}

# <length boat> : (x,y,"<orientation>")   --> x,y of the boat's back
# orientation : n ↑, o ←, e →, s ↓
grid_j1 = {"three_boat": (0,0,"n"), "two_boat1": (0,0,"n"), "two_boat2": (0,0,"n"),
           "boat1": (0,0,"n"), "boat2": (0,0,"n"), "boat3": (0,0,"n")}

grid_j2 = {"three_boat": (0,0,"n"), "two_boat1": (0,0,"n"), "two_boat2": (0,0,"n"),
           "boat1": (0,0,"n"), "boat2": (0,0,"n"), "boat3": (0,0,"n")}

completed_grid = False
num = 0
enough_player = 0
pwd = ''
cooldown_code = False
players_list_str = "Players (1/2) :\n- Waiting..."
players_label_ref = None
start = False
main_root_ref = None
current_window = None
imgs = []

def id_generator():
    def id_generator(size=10, chars=string.ascii_uppercase + string.digits):
        return ''.join(random.choice(chars) for _ in range(size))
    
    return id_generator()

# ------- Menu -------
def tkinter_menu(s):
    global icones
    global main_root_ref
    global imgs

    main_root = tk.Tk()
    main_root_ref = main_root
    main_root.title("Menu")
    main_root.iconbitmap(icones["icone"])
    main_root.resizable(False,False)
    def start_game(s,code):
        data = f'START {code}'
        s.sendall(data.encode())

    def load_img(images):
            loaded_img = {}
            resize_dims = {
                "welcome": (290, 315),
                "boat_1": (150, 50),
                "boat_2": (150, 50),
                "boat_3": (150, 50),
                "water": (40,40),
                "b1": (40,40),
                "b2_1": (40,40),
                "b2_2": (40,40),
                "b3_1": (40,40),
                "b3_2": (40,40),
                "b3_3": (40,40)
            }

            for n_img, p_img in images.items():
                if p_img.endswith(".ico"):
                    continue

                pil_img = Image.open(p_img)
                if n_img in resize_dims:
                    target_size = resize_dims[n_img]
                    pil_img.thumbnail(target_size, Image.Resampling.LANCZOS)
                    background = Image.new("RGBA", target_size, (0, 0, 0, 0))
                    x = (target_size[0] - pil_img.width) // 2
                    y = (target_size[1] - pil_img.height) // 2
                    background.paste(pil_img, (x, y), pil_img)
                    pil_img = background

                loaded_img[n_img] = {
                    "tk": ImageTk.PhotoImage(pil_img),
                    "pil": pil_img,
                    "angle": 0
                }

            return loaded_img
    
    imgs = load_img(icones)
    placeholder = ''
    image = tk.Label(main_root, image=imgs["welcome"]["tk"])
    image.grid()
    start_btn = tk.Button(text="Start a game", command=lambda: create_game(s,placeholder))
    start_btn.place(relx=0.2, rely=1, anchor="sw")
    join_btn = tk.Button(text="Join a game", command=lambda: join_game(s,placeholder))
    join_btn.place(relx=0.8, rely=1, anchor="se")

    def join_game(s,btn_code):
        global pwd
        global pwd2
        global players_label_ref
        global current_window
        main_root.withdraw()
        join_root = tk.Toplevel(main_root)
        current_window = join_root
        join_root.title("Lobby")
        join_root.iconbitmap(icones["icone"])
        image = tk.Label(join_root, image=imgs["welcome"]["tk"])
        image.grid()

        players_label = tk.Label(join_root, text=players_list_str, justify="left", font=("Arial", 12, "bold"), fg="blue")
        players_label.place(relx=0.5, rely=0.2, anchor="center")
        players_label_ref = players_label

        code_label = tk.Label(join_root, text=f"Code :")
        code_label.place(relx=0, rely=1, anchor="sw")
        code = tk.Entry(join_root)
        code.grid(sticky="sw")
        start_btn = tk.Button(join_root, text="Join the game", command=lambda: connect_game(s,code.get()))
        start_btn.place(relx=0.8, rely=1, anchor="s")

        def connect_game(s, code):
            data = f'Join {code}'
            s.sendall(data.encode())

        def on_close():
            join_root.destroy()
            main_root.deiconify()
        join_root.protocol("WM_DELETE_WINDOW", on_close)

    def create_game(s,btn_code):
        global start_btn
        global pwd
        global pwd2
        global players_label_ref
        global current_window
        main_root.withdraw()
        create_root = tk.Toplevel(main_root)
        current_window = create_root
        create_root.title("Game Creator")
        create_root.iconbitmap(icones["icone"])
        create_root.resizable(False,False)
        image = tk.Label(create_root, image=imgs["welcome"]["tk"])
        image.grid()
        players_label = tk.Label(create_root, text=players_list_str, justify="left", font=("Arial", 12, "bold"), fg="green")
        players_label.place(relx=0.5, rely=0.2, anchor="center")
        players_label_ref = players_label

        def get_code(arg,e,block_redeem):
            global pwd
            global cooldown_code
            global enough_player
            if cooldown_code == False:
                cooldown_code = True
                pwd = ''
                block_redeem.config(state="disabled")
                s.sendall(arg)

                def check_pwd():
                    global pwd
                    global cooldown_code
                    if pwd != '':
                        block_redeem.config(state="normal")
                        e.config(state="normal")
                        e.delete(0,tk.END)
                        e.insert(0,pwd)
                        e.config(state="readonly")
                        cooldown_code = False
                    else:
                        e.after(100, check_pwd)
                check_pwd()

            else:
                pass
            
        s.sendall(b'Create')
        code_label = tk.Label(create_root, text=f"Code :")
        code_label.place(relx=0, rely=1, anchor="sw")
        code = tk.Entry(create_root)
        code.grid(sticky="sw")
        code.insert(0, pwd)
        code.config(state="readonly")
        redeem = tk.Button(create_root, text="Redeem a code", command=lambda: get_code(b'Create', code, redeem))
        redeem.place(relx=0.5, rely=1, anchor="s")
        start_btn = tk.Button(create_root, text="Launch a game", command=lambda: start_game(s,code.get()))
        start_btn.place(relx=1, rely=1, anchor="se")

        """
        def start_button_status(btn):
            while True:
                if enough_player < 2:
                    btn.config(state="disabled")
                else:
                    btn.config(state="normal")
                time.sleep(0.1)
        threading.Thread(target=start_button_status, args=(start_btn,), daemon=True).start()"""

        def on_close():
            create_root.destroy()
            main_root.deiconify()
        create_root.protocol("WM_DELETE_WINDOW", on_close)

    main_root.mainloop()

# ------- Serveur -------
HOST = "127.0.0.1"  # The server's hostname or IP address
PORT = 28282  # The port used by the server

def mailbox(s):
    global num
    global completed_grid
    global pwd
    global players_list_str
    global players_label_ref
    global start
    global enough_player
    id = ''
    id_tmp = ''
    id_sent = False

    while True:
        data = s.recv(1024).decode()

        if id == '' and id_sent == False:
            id_tmp = "ID " + str(id_generator())
            s.sendall(id_tmp.encode())
            id_sent = True

        if data == "ID_g":
            id = id_tmp

        if data == "ID_b":
            id_sent = False

        if "Code" in data:
            parts = data.split(" ")
            if len(parts) > 1:
                pwd = parts[1]

        if "Player" in data:
            parts = data.split(" ")
            num = parts[1]
            print(f"You are Player {num}")

        if "PLAYERS_LIST" in data:
            raw_list = data.split(" ")[1]
            list_players = raw_list.split(",")
            nb_player = 0
            for _ in list_players:
                nb_player += 1
            players_list_str = f"Joueurs ({nb_player}/2) :"
            enough_player = nb_player

            for p_id in list_players:
                players_list_str += "\n- " + p_id
            players_list_str = players_list_str.strip()


            if players_label_ref:
                if players_label_ref.winfo_exists():
                    if nb_player == 2:
                        players_label_ref.config(text=players_list_str, fg="green")
                    else:
                        players_label_ref.config(text=players_list_str, fg="blue")

        if data == "GAME_FULL":
            players_list_str = "Error : Game is full (2/2 max) !"

            if players_label_ref:
                if players_label_ref.winfo_exists():
                    players_label_ref.config(text=players_list_str, fg="red")

        if "START" in data:
            init_grid()

def init_grid():
    global current_window
    global main_root_ref
    global icones
    global s
    selected_boat = None
    grid = []
    grid_locked = False
    for y in range(10):
        line = []
        for x in range(10):
            line.append(None)
        grid.append(line)

    if current_window and current_window.winfo_exists():
        current_window.destroy()

    if main_root_ref and main_root_ref.winfo_exists():
        main_root_ref.withdraw()

    grid_root = tk.Toplevel(main_root_ref)
    grid_root.title("Warships location")
    grid_root.iconbitmap(icones["icone"])
    #grid_root.resizable(False,False)
    current_window = grid_root
    canva = tk.Canvas(current_window, width=700, height=600)
    canva.pack(pady=15, padx=10)

    alphabet = {0: "A", 1: "B", 2: "C", 3: "D", 4: "E", 5: "F", 6: "G", 7: "H", 8: "I", 9: "J"}
    cell_size = imgs["water"]["pil"].width
    gap = 1
    step = cell_size + gap

    for y in range(10):

        for x in range(10):
            if y == 0:
                letters = canva.create_text(200+step*x, 10, text=alphabet[x], fill="black")
            if x == 0:
                number = canva.create_text(165, step+step*y, text=y, fill="black")
            btn = canva.create_image(200+step*x, step+step*y, image=imgs["water"]["tk"])

    boats_frame = tk.Frame(grid_root)
    boats_frame.pack(pady=20)

    boat_list = []
    BASE_Y = 420
    X_START = 200

    boats_layout = [
        ("boat_1", 0, 20),
        ("boat_2", 180, 45),

        ("boat_1", 0, 70),
        ("boat_3", 350, 60),

        ("boat_1", 0, 120),
        ("boat_2", 180, 95),
    ]

    for name, dx, dy in boats_layout:
        x = X_START + dx
        y = BASE_Y + dy
        pil_copy = imgs[name]["pil"].copy()
        tk_copy = ImageTk.PhotoImage(pil_copy)

        if name == "boat_1":
            parts = [imgs["b1"]["tk"]]
        elif name == "boat_2":
            parts = [imgs["b2_1"]["tk"], imgs["b2_2"]["tk"]]
        else:
            parts = [imgs["b3_1"]["tk"], imgs["b3_2"]["tk"], imgs["b3_3"]["tk"]]

        boat_id = canva.create_image(x, y, image=tk_copy)

        boat_list.append({
            "id": boat_id,
            "uid": str(uuid.uuid4()),
            "name": name,
            "mirror": False,
            "parts": parts,
            "base_pos": (x, y),
            "pil": pil_copy,
            "tk": tk_copy,
            "angle": 0
        })

    def serialize_grid_boats(grid):
        boats = {}
        visited = [[False]*10 for _ in range(10)]

        count = {
            "boat_1": 0,
            "boat_2": 0,
            "boat_3": 0
        }

        def get_boat_by_uid(uid):
            for b in boat_list:
                if b["uid"] == uid:
                    return b
            return None

        for y in range(10):
            for x in range(10):

                if grid[y][x] is None or visited[y][x]:
                    continue

                uid = grid[y][x]
                boat = get_boat_by_uid(uid)

                if boat is None:
                    continue

                name = boat["name"]

                coords = []
                stack = [(x, y)]

                while stack:
                    cx, cy = stack.pop()

                    if not (0 <= cx < 10 and 0 <= cy < 10):
                        continue
                    if visited[cy][cx]:
                        continue
                    if grid[cy][cx] != uid:
                        continue

                    visited[cy][cx] = True
                    coords.append((cx, cy))

                    stack.extend([
                        (cx+1, cy), (cx-1, cy),
                        (cx, cy+1), (cx, cy-1)
                    ])

                coords.sort()

                if len(coords) == 1:
                    orientation = "n"
                    back = coords[0]

                else:
                    x0, y0 = coords[0]
                    x1, y1 = coords[1]

                    if x0 != x1:
                        # horizontal
                        if coords[-1][0] > coords[0][0]:
                            orientation = "e"
                            back = coords[0]
                        else:
                            orientation = "o"
                            back = coords[-1]
                    else:
                        # vertical
                        if coords[-1][1] > coords[0][1]:
                            orientation = "s"
                            back = coords[0]
                        else:
                            orientation = "n"
                            back = coords[-1]

                count[name] += 1

                if name == "boat_3":
                    key = "three_boat"
                elif name == "boat_2":
                    key = f"two_boat{count[name]}"
                else:
                    key = f"boat{count[name]}"

                boats[key] = (back[0], back[1], orientation)

        return boats
    def validate_grid():
        nonlocal grid_locked
        global s

        for boat in boat_list:
            if "ids" not in boat:
                return

        grid_locked = True
        boats = serialize_grid_boats(grid)
        data = f'GRID {boats}'
        s.sendall(data.encode())

        print(boats)

    def block_valid(btn):
        all_placed = True

        for boat in boat_list:
            if "ids" not in boat:
                all_placed = False
                break

        if all_placed:
            btn.config(state="normal")
        else:
            btn.config(state="disabled")

        grid_root.after(100, block_valid, btn)

    GRID_X = 200
    CELL_SIZE = step
    GRID_SIZE = 10

    button_x = GRID_X + GRID_SIZE * CELL_SIZE
    button_y = 20

    validate_btn = tk.Button(
        grid_root,
        text="Validate the grid",
        command=validate_grid
    )

    validate_btn.place(x=button_x, y=button_y)

    block_valid(validate_btn)


    def select_boat(e):
        nonlocal boat_list
        nonlocal selected_boat
        nonlocal grid_locked

        if grid_locked:
            return
        grid_root.focus_set()
        selected_boat = None
        items = canva.find_overlapping(e.x, e.y, e.x, e.y)

        for boat in boat_list:
            if "ids" in boat:
                for pid in boat["ids"]:
                    if pid in items:
                        selected_boat = boat
                        return
            else:
                if boat["id"] in items:
                    selected_boat = boat
                    return
    def drag(e):
        nonlocal selected_boat
        nonlocal grid_locked
        if grid_locked:
            return
        if selected_boat:
            canva.coords(selected_boat["id"], e.x, e.y)

    def rotate_img(e):
        nonlocal selected_boat, grid_locked

        if grid_locked:
            return
        if not selected_boat:
            return

        current_boat = selected_boat
        img_key = current_boat["name"]

        current_boat["angle"] = (current_boat["angle"] + 90) % 360
        angle = current_boat["angle"]

        if angle == 0:     dx, dy = 1, 0
        elif angle == 90:  dx, dy = 0, 1
        elif angle == 180: dx, dy = -1, 0
        elif angle == 270: dx, dy = 0, -1

        if img_key == "boat_1":
            keys = ["b1"]
        elif img_key == "boat_2":
            keys = ["b2_1", "b2_2"] if dx >= 0 and dy >= 0 else ["b2_2", "b2_1"]
        elif img_key == "boat_3":
            keys = ["b3_1", "b3_2", "b3_3"] if dx >= 0 and dy >= 0 else ["b3_3", "b3_2", "b3_1"]

        rotated_tks = []
        for key in keys:
            pil_part = imgs[key]["pil"]
            rotated = pil_part.rotate(-angle, expand=True)
            tk_part = ImageTk.PhotoImage(rotated)
            rotated_tks.append(tk_part)

        current_boat["rotated_tks"] = rotated_tks

        if "ids" not in current_boat:
            current_boat["tk"] = rotated_tks[0]
            canva.itemconfig(current_boat["id"], image=current_boat["tk"])
            return

        first_coords = canva.coords(current_boat["ids"][0])
        if not first_coords:
            return
        base_x, base_y = first_coords[0], first_coords[1]

        for i, (pid, tk_part) in enumerate(zip(current_boat["ids"], rotated_tks)):
            canva.itemconfig(pid, image=tk_part)
            canva.coords(pid, base_x + step * dx * i, base_y + step * dy * i)

    def get_final_pos(e):
        nonlocal selected_boat, grid, grid_locked

        if grid_locked:
            return
        if not selected_boat:
            return

        x = round((e.x - 200) / step)
        y = round((e.y - step) / step)
        x = max(0, min(9, x))
        y = max(0, min(9, y))

        img_key = selected_boat["name"]
        angle = selected_boat["angle"]

        if angle == 0:     dx, dy = 1, 0
        elif angle == 90:  dx, dy = 0, 1
        elif angle == 180: dx, dy = -1, 0
        elif angle == 270: dx, dy = 0, -1
        else:              dx, dy = 1, 0

        length_boat = len(selected_boat["parts"])

        old_cells = set()
        if "ids" in selected_boat:
            for yy in range(10):
                for xx in range(10):
                    if grid[yy][xx] == selected_boat["uid"]:
                        old_cells.add((xx, yy))

        is_valid = True
        for i in range(length_boat):
            tx, ty = x + dx*i, y + dy*i
            if not (0 <= tx < 10 and 0 <= ty < 10):
                is_valid = False
                break

        if is_valid:
            for i in range(length_boat):
                tx, ty = x + dx*i, y + dy*i
                if grid[ty][tx] is not None and (tx, ty) not in old_cells:
                    is_valid = False
                    break

        if not is_valid:
            base_x, base_y = selected_boat["base_pos"]
            if "ids" in selected_boat:
                for pid in selected_boat["ids"]:
                    canva.delete(pid)
                rotated_tks = selected_boat.get("rotated_tks", None)
                if rotated_tks is None:
                    if img_key == "boat_1":
                        rotated_tks = [ImageTk.PhotoImage(imgs["b1"]["pil"])]
                    elif img_key == "boat_2":
                        rotated_tks = [ImageTk.PhotoImage(imgs["b2_1"]["pil"]),
                                    ImageTk.PhotoImage(imgs["b2_2"]["pil"])]
                    elif img_key == "boat_3":
                        rotated_tks = [ImageTk.PhotoImage(imgs["b3_1"]["pil"]),
                                    ImageTk.PhotoImage(imgs["b3_2"]["pil"]),
                                    ImageTk.PhotoImage(imgs["b3_3"]["pil"])]

                angle = selected_boat["angle"]
                if angle == 0:     dx2, dy2 = 1, 0
                elif angle == 90:  dx2, dy2 = 0, 1
                elif angle == 180: dx2, dy2 = -1, 0
                elif angle == 270: dx2, dy2 = 0, -1
                else:              dx2, dy2 = 1, 0

                new_ids = []
                for i, tk_part in enumerate(rotated_tks):
                    old_list = sorted(old_cells)
                    ox, oy = old_list[0] if old_list else (0, 0)
                    px = 200 + step * (ox + dx2*i)
                    py = step  + step * (oy + dy2*i)
                    new_id = canva.create_image(px, py, image=tk_part)
                    new_ids.append(new_id)
                    grid[oy + dy2*i][ox + dx2*i] = selected_boat["uid"]

                idx = boat_list.index(selected_boat)
                boat_list[idx] = {**selected_boat, "id": new_ids[0], "ids": new_ids, "rotated_tks": rotated_tks}
            else:
                canva.coords(selected_boat["id"], base_x, base_y)

            selected_boat = None
            return

        for (xx, yy) in old_cells:
            grid[yy][xx] = None

        if "ids" in selected_boat:
            for pid in selected_boat["ids"]:
                canva.delete(pid)
        else:
            canva.delete(selected_boat["id"])

        rotated_tks = selected_boat.get("rotated_tks", None)
        if rotated_tks is None:
            if img_key == "boat_1":
                rotated_tks = [ImageTk.PhotoImage(imgs["b1"]["pil"])]
            elif img_key == "boat_2":
                rotated_tks = [ImageTk.PhotoImage(imgs["b2_1"]["pil"]),
                            ImageTk.PhotoImage(imgs["b2_2"]["pil"])]
            elif img_key == "boat_3":
                rotated_tks = [ImageTk.PhotoImage(imgs["b3_1"]["pil"]),
                            ImageTk.PhotoImage(imgs["b3_2"]["pil"]),
                            ImageTk.PhotoImage(imgs["b3_3"]["pil"])]

        new_ids = []
        for i, tk_part in enumerate(rotated_tks):
            px = 200 + step * (x + dx*i)
            py = step  + step * (y + dy*i)
            new_id = canva.create_image(px, py, image=tk_part)
            new_ids.append(new_id)
            grid[y + dy*i][x + dx*i] = selected_boat["uid"]

        boat_list.remove(selected_boat)
        boat_list.append({
            "id": new_ids[0],
            "ids": new_ids,
            "uid": selected_boat["uid"],
            "name": selected_boat["name"],
            "parts": selected_boat["parts"],
            "base_pos": selected_boat["base_pos"],
            "angle": angle,
            "pil": selected_boat["pil"],
            "tk": selected_boat["tk"],
            "rotated_tks": rotated_tks
        })

        selected_boat = None

    canva.bind("<Button-1>", select_boat)
    canva.bind("<B1-Motion>", drag)
    canva.bind("<ButtonRelease-1>", get_final_pos)
    grid_root.bind("<KeyPress-r>", rotate_img)

    def on_close():
        grid_root.destroy()
        if main_root_ref and main_root_ref.winfo_exists():
            main_root_ref.deiconify()

    grid_root.protocol("WM_DELETE_WINDOW", on_close)
    grid_root.wait_visibility()
    grid_root.focus_set()

try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))
    threading.Thread(target=mailbox, args=(s,), daemon=True).start()
    tkinter_menu(s)

except ConnectionRefusedError:
    print("The server is offline. Please restart later.")