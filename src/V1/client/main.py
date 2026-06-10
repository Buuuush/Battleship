import tkinter as tk
import socket
import threading
import time

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

# ------- Menu -------
def tkinter_menu(s):
    global icones
    main_root = tk.Tk()
    main_root.title("Menu")
    main_root.iconbitmap(icones["icone"])

    def join_game(s,code):
        data = f'join {code}'
        s.sendall(data.encode())

    def start_game(s,code):
        data = f'start {code}'
        s.sendall(data.encode())

    def load_img(images):
        loaded_img = {}
        for n_img, p_img in images.items():
            if p_img.endswith(".ico"):
                continue

            img_tk = tk.PhotoImage(file=p_img)
            loaded_img[n_img] = img_tk.subsample(2,2)

        return loaded_img
    imgs = load_img(icones)

    placeholder = ''
    image = tk.Label(main_root, image=imgs["welcome"]).grid()
    start_btn = tk.Button(text="Start a game", command=lambda: join_re(s,placeholder))
    start_btn.place(relx=0.2, rely=1, anchor="sw")
    join_btn = tk.Button(text="Join a game", command=lambda: join_re(s,placeholder))
    join_btn.place(relx=0.8, rely=1, anchor="se")

    def join_re(s,btn_code):
        global pwd
        global pwd2
        main_root.withdraw()
        join_root = tk.Toplevel(main_root)
        join_root.title("Game Creator")
        join_root.iconbitmap(icones["icone"])
        image = tk.Label(join_root, image=imgs["welcome"]).grid()

        def get_code(arg,e,block_redeem):
            global pwd
            global cooldown_code

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
        code_label = tk.Label(join_root, text=f"Code :")
        code_label.place(relx=0, rely=1, anchor="sw")
        code = tk.Entry(join_root)
        code.grid(sticky="sw")
        code.insert(0, pwd)
        code.config(state="readonly")
        redeem = tk.Button(join_root, text="Redeem a code", command=lambda: get_code(b'Create', code, redeem))
        redeem.place(relx=0.5, rely=1, anchor="s")
        start = tk.Button(join_root, text="Launch a game", command=lambda: start_game(s,code.get()))
        start.place(relx=1, rely=1, anchor="se")

        def on_close():
            join_root.destroy()
            main_root.deiconify()
        join_root.protocol("WM_DELETE_WINDOW", on_close)


    main_root.mainloop()



# ------- Serveur -------

HOST = "127.0.0.1"  # The server's hostname or IP address
PORT = 28282  # The port used by the server

def mailbox(s):
    global num
    global completed_grid
    global pwd
    while True:
        data = s.recv(1024).decode()
        if "Code" in data:
            pwd = data.split(" ")[1]
        
        if "Player" in data:
            num = data.split(" ")[1]
            print(f"You are Player {num}")

try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))
    threading.Thread(target=mailbox, args=(s,), daemon=True).start()
    tkinter_menu(s)

except ConnectionRefusedError:
    print("The server is offline. Please restart later.")
