import socket
import threading
import random

HOST = "127.0.0.1"
PORT = 28282
nb_joueur = 0
numero_player = 0

print("-----------------------------------------")
print("|                                       |")
print("|               Serveur prêt            |")
print("|                                       |")
print("-----------------------------------------")


def handle_client(client, addr):
    global nb_joueur
    global numero_player
    if numero_player == 0:
        numero_player = 3 - random.randint(1,2)
    else:
        numero_player = 3 - numero_player
    try:
        client.send(str(numero_player).encode())
        print(f"Joueur {numero_player} connecté")
        while True:
            data = client.recv(1024)
            if not data:
                break
            client.sendall(data)
        nb_joueur -= 1
    except ConnectionAbortedError:
        client.close()
        print(f"Joueur {numero_player} déconnecté")
        nb_joueur -= 1
    except ConnectionResetError:
        client.close()
        print(f"Joueur {numero_player} déconnecté")
        nb_joueur -= 1

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((HOST, PORT))
s.listen()
while True:
    client, addr = s.accept()
    if nb_joueur < 2:
        threading.Thread(target=handle_client, args=(client, addr)).start()
        nb_joueur +=1
    else:
        client.close()


# <length boat> : (x,y,"<orientation>")   --> x,y of the boat's back
# orientation : n ↑, o ←, e →, s ↓
grid_j1 = {"three_boat": (0,0,"n"), "two_boat1": (0,0,"n"), "two_boat2": (0,0,"n"),
           "boat1": (0,0,"n"), "boat2": (0,0,"n"), "boat3": (0,0,"n")}

grid_j2 = {"three_boat": (0,0,"n"), "two_boat1": (0,0,"n"), "two_boat2": (0,0,"n"),
           "boat1": (0,0,"n"), "boat2": (0,0,"n"), "boat3": (0,0,"n")}


# Simple server

