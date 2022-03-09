from socket import SO_OOBINLINE, socket, AF_INET, SOCK_STREAM
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
                type = unpack("!i",data)[0]
                # type 1 = show text to user
                if type == 1:
                    lenght = unpack("!i",sock.recv(4))[0]
                    text = sock.recv(lenght).decode('utf-8')
                    print(text)
                # type 2 = get case from user
                elif type == 2:
                    case = 10
                    while case > 8 or case < 0:
                        try:
                            case=int(input("Entrer un numéro de case entre 1 et 9:"))-1
                        except ValueError:
                            print("Ceci n'est pas une valeur correcte, réessayez")
                            case = 10
                    sock.send(pack("!i",case))
                # type 3 = game as ended
                elif type == 3:
                    break
        except KeyboardInterrupt:
            print("\n")
            print("Rage quit is bad -_-")
        sock.close()