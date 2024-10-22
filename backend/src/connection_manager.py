import socket
import threading
import os
import json
from .utils import generate_keys, generate_shared_key, send_data, receive_data, get_local_ip, aes_encrypt, aes_decrypt

class ConnectionManager:
    def __init__(self):
        self.nickname = None
        self.client_sk = None
        self.client_pk = None
        self.server_socket = None
        self.shared_key = None
        self.client_address = None
        self.server_ip = None
        self.server_port = None
        self.is_connected = False
        self.receive_thread = None
        self.connection_state = {
            'nickname': None,
            'server_ip': None,
            'server_port': None
        }
        self.last_error = None

    def set_peer_info(self, nickname, ip, port, status):
        self.peer_info = {
            "nickname": nickname,
            "ip": ip,
            "port": port,
            "status": status
        }

    def set_message_callback(self, callback):
        self.message_callback = callback
        if self.is_connected and self.server_socket:
            self.start_receive_messages()

    def start_receive_messages(self):
        if self.receive_thread is None or not self.receive_thread.is_alive():
            self.receive_thread = threading.Thread(target=self.receive_messages)
            self.receive_thread.daemon = True
            self.receive_thread.start()

    def get_client_address(self):
        if self.server_socket:
            return self.server_socket.getsockname()
        return None

    def get_or_generate_keys(self, nickname, secret_key):
        try:
            self.nickname = nickname
            key_storage_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'key_storage')
            pk_file = os.path.join(key_storage_dir, f"{nickname}.pk.json")
            sk_file = os.path.join(key_storage_dir, f"{nickname}.sk.json")
            
            os.makedirs(key_storage_dir, exist_ok=True)
            
            if os.path.exists(pk_file) and os.path.exists(sk_file):
                with open(pk_file, 'r') as f:
                    self.client_pk = json.load(f)
                with open(sk_file, 'r') as f:
                    self.client_sk = json.load(f)
            else:
                self.client_sk, self.client_pk = generate_keys(secret_key)
                
                with open(pk_file, 'w') as f:
                    json.dump(self.client_pk, f)
                with open(sk_file, 'w') as f:
                    json.dump(self.client_sk, f)
                    
            return self.client_pk
        except Exception as e:
            self.last_error = f"鍵の生成/読み込み中にエラーが発生: {str(e)}"
            raise Exception(self.last_error)
    
    def connect_to_server(self, server_ip, server_port):
        self.connection_state['server_ip'] = server_ip
        self.connection_state['server_port'] = server_port
        self.is_connected = False

        try:
            if self.server_socket:
                try:
                    self.server_socket.close()
                except:
                    pass
                self.server_socket = None
                
            self.server_ip = server_ip
            self.server_port = int(server_port)
            client_ip = get_local_ip()
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.settimeout(10)
            self.server_socket.connect((self.server_ip, self.server_port))

            self.client_address = (client_ip, self.server_socket.getsockname()[1])
            client_address = self.perform_key_exchange(f"{self.client_address[0]}:{self.client_address[1]}")
            self.is_connected = True
            
            if hasattr(self, 'message_callback'):
                self.start_receive_messages()
                
            return client_address
            
        except socket.timeout:
            self.last_error = "接続がタイムアウトしました。"
            raise Exception(self.last_error)
        except ConnectionRefusedError:
            self.last_error = f"接続が拒否されました。{server_ip}:{server_port}でサーバーが実行されていることを確認してください。"
            raise Exception(self.last_error)
        except Exception as e:
            self.last_error = f"接続エラー: {str(e)}"
            raise Exception(self.last_error)

    def get_connection_state(self):
        return self.connection_state

    def perform_key_exchange(self, client_address):
        try:
            server_data = receive_data(self.server_socket)
            if not server_data or 'pk' not in server_data:
                raise Exception("サーバーから無効なデータを受信しました")
            
            server_pk = server_data['pk']
            
            send_data(self.server_socket, {
                "pk": self.client_pk,
                "address": client_address,
                "nickname": self.nickname
            })
        
            self.shared_key = generate_shared_key(self.client_sk, server_pk)
            return client_address
            
        except Exception as e:
            self.last_error = f"鍵交換に失敗: {str(e)}"
            raise Exception(self.last_error)

    def send_message(self, message):
        if not self.is_connected or not self.server_socket or not self.shared_key:
            raise Exception("サーバーに接続されていません")
            
        try:
            encrypted_message = aes_encrypt(message, self.shared_key)
            send_data(self.server_socket, encrypted_message)
        except Exception as e:
            self.is_connected = False
            self.last_error = f"メッセージ送信エラー: {str(e)}"
            raise Exception(self.last_error)

    def receive_messages(self):
        while self.is_connected and self.server_socket and hasattr(self, 'message_callback'):
            try:
                if not self.server_socket:
                    break
                    
                encrypted_message = receive_data(self.server_socket)
                if not encrypted_message:
                    print("サーバーから切断されました")
                    break
                    
                decrypted_message = aes_decrypt(encrypted_message, self.shared_key)
                self.message_callback(decrypted_message)
                
            except (ConnectionResetError, BrokenPipeError):
                print("サーバーとの接続が切断されました")
                self.is_connected = False
                break
            except Exception as e:
                if not self.is_connected or not self.server_socket:
                    break
                continue
        
        self.is_connected = False
        print("メッセージ受信ループを終了しました")

    def close_connection(self):
        self.is_connected = False
        if self.server_socket:
            try:
                self.server_socket.shutdown(socket.SHUT_RDWR)
            except:
                pass
            finally:
                try:
                    self.server_socket.close()
                except:
                    pass
                self.server_socket = None
        self.shared_key = None