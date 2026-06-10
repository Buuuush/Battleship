import tkinter as tk
import socket
import threading
import time
import random, string

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

    def start_game(s,code):
        data = f'START {code}'
        s.sendall(data.encode())

    def load_img(images):
        loaded_img = {}
        resize = {
            "welcome": (2, 2),  # 583x635
            "boat_1": (4, 4),   # 457x237
            "boat_2": (5, 5), # 914x457
            "boat_3": (6, 6), # 1371x591
            "water": (26, 26),  # 880x880
            "b1": (8, 8),
            "b2_1": (8, 8),
            "b2_2": (8, 8),
            "b3_1": (8, 8),
            "b3_2": (8, 8),
            "b3_3": (8, 8)
        }

        for n_img, p_img in images.items():
            if p_img.endswith(".ico"):
                continue
            img_tk = tk.PhotoImage(file=p_img)
            x, y = resize.get(n_img, (1, 1))
            img_tk = img_tk.subsample(x, y)
            loaded_img[n_img] = img_tk

        return loaded_img
    imgs = load_img(icones)
    placeholder = ''
    image = tk.Label(main_root, image=imgs["welcome"])
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
        image = tk.Label(join_root, image=imgs["welcome"])
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
        image = tk.Label(create_root, image=imgs["welcome"])
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

    if current_window and current_window.winfo_exists():
        current_window.destroy()

    if main_root_ref and main_root_ref.winfo_exists():
        main_root_ref.withdraw()

    grid_root = tk.Toplevel(main_root_ref)
    grid_root.title("Warships location")
    grid_root.iconbitmap(icones["icone"])

    current_window = grid_root
    canva = tk.Canvas(current_window, width=700, height=500)
    canva.pack(pady=15, padx=10)

    cases = []
    alphabet = {0: "A", 1: "B", 2: "C", 3: "D", 4: "E", 5: "F", 6: "G", 7: "H", 8: "I", 9: "J"}
    for y in range(10):
        line = []

        for x in range(10):
            if y == 0:
                lbl = canva.create_text(200+35*x, 10, text=alphabet[x], fill="black")
            if x == 0:
                lbl = canva.create_text(165, 35+35*y, text=y, fill="black")
            btn = canva.create_image(200+35*x, 36+35*y, image=imgs["water"])
            line.append(btn)

        cases.append(line)

    boats_frame = tk.Frame(grid_root)
    boats_frame.pack(pady=20)

    boat_list = []
    for y in range(3):
        lbl = canva.create_image(100, 400 + 40*y, image=imgs["boat_1"])
        boat_list.append(lbl)

    for y in range(2):
        lbl = canva.create_image(300, 400 + 60*y, image=imgs["boat_2"])
        boat_list.append(lbl)

    lbl = canva.create_image(550, 450, image=imgs["boat_3"])
    boat_list.append(lbl)

    def left(e):
        nonlocal boat_list
        canva.coords(boat_list[0], e.x, e.y)

    def get_final_pos(e):
        x = round((e.x - 200) / 35)
        y = round((e.y - 36) / 35)
        x = max(0, min(9, x))
        y = max(0, min(9, y))
        cx = 200 + 35 * x
        cy = 36 + 35 * y
        canva.coords(boat_list[0], cx, cy)

        canva.delete(boat_list[0])
        boat_list[0] = canva.create_image(cx, cy, image=imgs["b1"])

    grid_root.bind("<B1-Motion>", left)
    grid_root.bind("<ButtonRelease-1>", get_final_pos)
    grid_root.bind("<KeyPress-r>", rotate_img)
    def on_close():
        grid_root.destroy()
        if main_root_ref and main_root_ref.winfo_exists():
            main_root_ref.deiconify()

    grid_root.protocol("WM_DELETE_WINDOW", on_close)

try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))
    threading.Thread(target=mailbox, args=(s,), daemon=True).start()
    tkinter_menu(s)

except ConnectionRefusedError:
    print("The server is offline. Please restart later.")