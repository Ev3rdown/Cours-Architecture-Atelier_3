import json
from socket import socket, AF_INET, SOCK_STREAM
from struct import pack, unpack

PORT = 0x4BAE
SERVER = "127.0.0.1"

if __name__ == '__main__':
    with socket(AF_INET, SOCK_STREAM) as sock:
        sock.connect((SERVER, PORT))
        num = unpack('!i', sock.recv(4))[0]
        print("Vous êtes le joueur "+str(num))
        try:
            while True:
                data = sock.recv(4)
                lenght = unpack("!i",data)[0]
                message = sock.recv(lenght).decode('utf-8')
                jsonRPC = json.loads(message)
                method = jsonRPC['method']
                if message == "wait":
                    print("en attente")
                elif message == "next_player":
                    print(display_grid())
                    print("au tour de l'autre joueur")
                elif message == "update_grid":
                    update_grid(jsonRPC['params']['grid'])
                elif message == "can_play":
                    case = 10
                    while case > 8 or case < 0:
                        try:
                            case=int(input("Entrer un numéro de case entre 1 et 9:"))-1
                        except ValueError:
                            print("Ceci n'est pas une valeur correcte, réessayez")
                            case = 10
                    send_case(case)
                elif message == "end_game":
                    params = jsonRPC['params']
                    if jsonRPC['params']['']
                    break
        except KeyboardInterrupt:
            print("\n")
            print("Rage quit is bad -_-")
        sock.close()