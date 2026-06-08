import socket
import threading
import random
import string

HOST = "127.0.0.1"
PORT = 28282
nb_joueur = 0
players = []
numero_player = 0
print("-----------------------------------------")
print("|                                       |")
print("|               Serveur prêt            |")
print("|                                       |")
print("-----------------------------------------")


def handle_client(client,lock):
    global nb_joueur
    global players

    def clrm():
        try:
            global nb_joueur
            client.close()
            print(f"Joueur {numero_player} déconnecté")
            with lock:
                nb_joueur -= 1
                players.remove(numero_player)
        except:
            pass


    numero_player = random.randint(0,10)
    with lock:
        while numero_player in players:
            numero_player = random.randint(0,10)
        players.append(numero_player)

    try:
        client.send(str(numero_player).encode())
        print(f"Joueur {numero_player} connecté")
        while True:
            data = client.recv(1024)
            if not data:
                break
            client.sendall(data)
        clrm()
    except ConnectionAbortedError:
        clrm()
    except ConnectionResetError:
        clrm()

def join_game():
    def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
        return ''.join(random.choice(chars) for _ in range(size))
    
    return id_generator()
    
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((HOST, PORT))
s.listen()
lock = threading.Lock()
while True:
    client, addr = s.accept()
    threading.Thread(target=handle_client, args=(client,lock)).start()
    with lock:
        nb_joueur +=1



# <length boat> : (x,y,"<orientation>")   --> x,y of the boat's back
# orientation : n ↑, o ←, e →, s ↓
grid_j1 = {"three_boat": (0,0,"n"), "two_boat1": (0,0,"n"), "two_boat2": (0,0,"n"),
           "boat1": (0,0,"n"), "boat2": (0,0,"n"), "boat3": (0,0,"n")}

grid_j2 = {"three_boat": (0,0,"n"), "two_boat1": (0,0,"n"), "two_boat2": (0,0,"n"),
           "boat1": (0,0,"n"), "boat2": (0,0,"n"), "boat3": (0,0,"n")}


# Simple server

