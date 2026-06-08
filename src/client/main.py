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
    "accueil": r"img\\boats\\accueil.png",
    "icone": r"img\\boats\\icone.ico",
    "water": r"img\\water\\water.png"
}



# <length boat> : (x,y,"<orientation>")   --> x,y of the boat's back
# orientation : n ↑, o ←, e →, s ↓
grid_j1 = {"three_boat": (0,0,"n"), "two_boat1": (0,0,"n"), "two_boat2": (0,0,"n"),
           "boat1": (0,0,"n"), "boat2": (0,0,"n"), "boat3": (0,0,"n")}

grid_j2 = {"three_boat": (0,0,"n"), "two_boat1": (0,0,"n"), "two_boat2": (0,0,"n"),
           "boat1": (0,0,"n"), "boat2": (0,0,"n"), "boat3": (0,0,"n")}

completed_grid = False
num = 0


# ------- Menu -------
def tkinter_menu(s):
    global icones
    main_root = tk.Tk()
    main_root.title("Menu")
    main_root.iconbitmap(icones["icone"])

    def join_re(s,e,parent_btn):
        if e == 0:
            s.sendall(b"Create")
            pwd = s.recv(1024).decode()
            code_label = tk.Label(main_root, text=f"Code :").grid(sticky="sw")
            code = tk.Entry(main_root)
            code.grid(sticky="sw")
            code.insert(0, pwd)
            code.config(state="readonly")
            parent_btn.pack_forget()
        if e == 1:
            s.sendall(b"Rejoin")

    def load_img(images):
        loaded_img = {}
        for n_img, p_img in images.items():
            if p_img.endswith(".ico"):
                continue

            img_tk = tk.PhotoImage(file=p_img)
            loaded_img[n_img] = img_tk.subsample(2,2)

        return loaded_img
    imgs = load_img(icones)

    image = tk.Label(main_root, image=imgs["accueil"]).grid()
    start_btn = tk.Button(text="Start a game", command=lambda: join_re(s,0, start_btn))
    start_btn.place(relx=0.2, rely=1, anchor="sw")
    join_btn = tk.Button(text="Join a game", command=lambda: join_re(s,1,join_btn))
    join_btn.place(relx=0.8, rely=1)
    main_root.mainloop()



# ------- Serveur -------

HOST = "127.0.0.1"  # The server's hostname or IP address
PORT = 28282  # The port used by the server

def connection(s):
    global num
    global completed_grid
    num = s.recv(1024).decode()
    print(f"Vous êtes le joueur {num}")
    while True:
        s.sendall(b"1")
        if completed_grid == False:
            pass
        else:
             break
        time.sleep(10)
    while True:
        s.sendall(b"Hello, world")
        data = s.recv(1024)

try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))
    threading.Thread(target=connection, args=(s,)).start()
    threading.Thread(target=tkinter_menu, args=(s,)).start()

except ConnectionRefusedError:
    print("Le serveur n'est pas connecté. Veuillez recommencer plus tard.")
