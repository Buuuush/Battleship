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
pwd = ''
cooldown_code = False
players_list_str = "Joueurs (1/2) :\n- Waiting..."
players_label_ref = None

def id_generator():
    def id_generator(size=10, chars=string.ascii_uppercase + string.digits):
        return ''.join(random.choice(chars) for _ in range(size))
    
    return id_generator()

# ------- Menu -------
def tkinter_menu(s):
    global icones
    print("[DEBUG] Initialisation du menu Tkinter")
    main_root = tk.Tk()
    main_root.title("Menu")
    main_root.iconbitmap(icones["icone"])

    def start_game(s,code):
        print(f"[DEBUG] Action start_game pour le code: {code}")
        data = f'START {code}'
        s.sendall(data.encode())

    def load_img(images):
        loaded_img = {}
        for n_img, p_img in images.items():
            if p_img.endswith(".ico"):
                continue
            print(f"[DEBUG] Chargement image: {n_img} -> {p_img}")
            img_tk = tk.PhotoImage(file=p_img)
            loaded_img[n_img] = img_tk.subsample(2,2)

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
        print("[DEBUG] Ouverture de l'interface Join Game")
        main_root.withdraw()
        join_root = tk.Toplevel(main_root)
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
        start = tk.Button(join_root, text="Launch a game", command=lambda: connect_game(s,code.get()))
        start.place(relx=1, rely=1, anchor="s")

        def connect_game(s, code):
            print(f"[DEBUG] Tentative de connexion au code: {code}")
            data = f'Join {code}'
            s.sendall(data.encode())

        def on_close():
            print("[DEBUG] Fermeture interface Join Game")
            join_root.destroy()
            main_root.deiconify()
        join_root.protocol("WM_DELETE_WINDOW", on_close)

    def create_game(s,btn_code):
        global pwd
        global pwd2
        global players_label_ref
        print("[DEBUG] Ouverture de l'interface Create Game")
        main_root.withdraw()
        create_root = tk.Toplevel(main_root)
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
            print(f"[DEBUG] get_code appele. Cooldown actuel: {cooldown_code}")

            if cooldown_code == False:
                cooldown_code = True
                pwd = ''
                block_redeem.config(state="disabled")
                print(f"[DEBUG] Envoi demande de code au serveur: {arg}")
                s.sendall(arg)

                def check_pwd():
                    global pwd
                    global cooldown_code

                    if pwd != '':
                        print(f"[DEBUG] Code recu avec succes: {pwd}")
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
            
        print("[DEBUG] Envoi initial 'Create' au serveur")
        s.sendall(b'Create')
        code_label = tk.Label(create_root, text=f"Code :")
        code_label.place(relx=0, rely=1, anchor="sw")
        code = tk.Entry(create_root)
        code.grid(sticky="sw")
        code.insert(0, pwd)
        code.config(state="readonly")
        redeem = tk.Button(create_root, text="Redeem a code", command=lambda: get_code(b'Create', code, redeem))
        redeem.place(relx=0.5, rely=1, anchor="s")
        start = tk.Button(create_root, text="Launch a game", command=lambda: start_game(s,code.get()))
        start.place(relx=1, rely=1, anchor="se")

        def on_close():
            print("[DEBUG] Fermeture interface Create Game")
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
    id = ''
    id_tmp = ''
    id_sent = False
    print("[DEBUG] Thread Mailbox demarre")
    while True:
        try:
            raw_data = s.recv(1024)
            if not raw_data:
                print("[DEBUG] Connexion fermee par le serveur (reception vide)")
                break
            data = raw_data.decode()
            print(f"[DEBUG] Mailbox a recu: {data}")
            
            if not id and not id_sent:
                id_tmp = f'ID {id_generator()}'
                print(f"[DEBUG] Envoi proposition d'ID: {id_tmp}")
                s.sendall(id_tmp.encode())
                id_sent = True
            if "ID_g" == data:
                id = id_tmp
                print(f"[DEBUG] ID valide par le serveur: {id}")
            if "ID_b" == data:
                id_sent = False
            if "Code" in data:
                pwd = data.split(" ")[1]
                print(f"[DEBUG] Variable globale pwd mise a jour: {pwd}")
            if "Player" in data:
                num = data.split(" ")[1]
                print(f"You are Player {num}")

            if "PLAYERS_LIST" in data:
                raw_list = data.split(" ")[1]
                list_players = raw_list.split(",")
                nb_p = len(list_players)
                players_list_str = f"Joueurs ({nb_p}/2) :\n" + "\n".join([f"- {p_id}" for p_id in list_players])
                print(f"[DEBUG] Liste locale mise à jour : {players_list_str}")
                
                if players_label_ref and players_label_ref.winfo_exists():
                    players_label_ref.config(text=players_list_str, fg="green" if nb_p == 2 else "blue")

            if "GAME_FULL" == data:
                players_list_str = "Error : Game is full (2/2 max) !"
                print(f"[DEBUG] Connexion refusee : la partie est pleine.")
                if players_label_ref and players_label_ref.winfo_exists():
                    players_label_ref.config(text=players_list_str, fg="red")

        except Exception as e:
            print(f"[DEBUG] Exception dans mailbox: {e}")
            break

try:
    print(f"[DEBUG] Tentative de connexion a {HOST}:{PORT}")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))
    print("[DEBUG] Connecte. Demarrage du thread mailbox")
    threading.Thread(target=mailbox, args=(s,), daemon=True).start()
    tkinter_menu(s)

except ConnectionRefusedError:
    print("The server is offline. Please restart later.")