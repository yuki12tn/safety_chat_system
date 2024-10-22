from datetime import datetime
from zoneinfo import ZoneInfo
from django.core.management.base import BaseCommand
from django.conf import settings
import socket
import threading
import hashlib
import json
import logging
from ...src.utils import send_data, receive_data, generate_keys, aes_encrypt, aes_decrypt, get_local_ip
from py_ecc.secp256k1.secp256k1 import multiply

class Command(BaseCommand):
    help = 'Runs the socket server for chat'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.SERVER_SK, self.SERVER_PK = generate_keys("server")
        self.clients = {}
        self.clients_lock = threading.Lock()
        self.running = True
        self.server_socket = None

    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

    def perform_key_exchange(self, client_socket):
        try:
            send_data(client_socket, {"pk": self.SERVER_PK})
            client_data = receive_data(client_socket)
            
            if not client_data or not all(k in client_data for k in ['pk', 'address', 'nickname']):
                raise ValueError("無効なクライアントデータを受信しました")
            
            client_pk = client_data['pk']
            client_address = client_data['address']
            client_nickname = client_data['nickname']
            
            shared_secret = multiply(client_pk, self.SERVER_SK)
            shared_key = hashlib.sha256(str(shared_secret[0]).encode()).digest()
            
            return client_address, client_nickname, shared_key
            
        except (ConnectionResetError, BrokenPipeError) as e:
            self.stderr.write(self.style.ERROR(f"キー交換中に接続が切断されました: {e}"))
            raise
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"キー交換中にエラーが発生: {e}"))
            raise

    def send_client_update(self, client_socket, client_info, shared_key):
        try:
            encrypted = aes_encrypt(json.dumps(client_info), shared_key)
            send_data(client_socket, encrypted)
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"クライアント更新の送信中にエラーが発生: {e}"))
            raise

    def handle_client(self, client_socket):
        client_address = None
        client_nickname = None
        
        try:
            # キー交換
            client_address, client_nickname, shared_key = self.perform_key_exchange(client_socket)
            
            with self.clients_lock:
                self.clients[client_socket] = (client_address, client_nickname, shared_key)
            
            self.stdout.write(self.style.SUCCESS(f'新しいユーザーが接続しました: {client_nickname}'))
            
            # 接続通知の送信
            ip, port = client_address.rsplit(':', 1)
            update_message = {
                "type": "user_update",
                "username": client_nickname,
                "ip": ip,
                "port": port,
                "status": "オンライン"
            }
            
            # 新規クライアントに既存ユーザーの情報を送信
            with self.clients_lock:
                for sock, (addr, nick, key) in self.clients.items():
                    if sock != client_socket:
                        existing_ip, existing_port = addr.rsplit(':', 1)
                        try:
                            self.send_client_update(client_socket, {
                                "type": "user_update",
                                "username": nick,
                                "ip": existing_ip,
                                "port": existing_port,
                                "status": "オンライン"
                            }, shared_key)
                        except Exception:
                            continue

            # 他のクライアントに新規ユーザーの情報を通知
            self.broadcast_message(json.dumps(update_message), client_socket)

            # メッセージ受信ループ
            while self.running:
                try:
                    encrypted_message = receive_data(client_socket)
                    if not encrypted_message:
                        break
                    
                    decrypted_message = aes_decrypt(encrypted_message, shared_key)
                    self.stdout.write(self.style.SUCCESS(f'{client_nickname}: {decrypted_message}'))
                    
                    message_data = {
                        "type": "message",
                        "username": client_nickname,
                        "ip": ip,
                        "port": port,
                        "content": decrypted_message
                    }
                    
                    self.broadcast_message(json.dumps(message_data), None)
                    
                except (ConnectionResetError, BrokenPipeError):
                    break
                except Exception as e:
                    self.stderr.write(self.style.ERROR(f"メッセージ処理中にエラーが発生: {e}"))
                    continue

        except Exception as e:
            self.stderr.write(self.style.ERROR(f"クライアント処理中にエラーが発生: {e}"))
        finally:
            self.cleanup_client(client_socket, client_address, client_nickname)

    def cleanup_client(self, client_socket, client_address, client_nickname):
        try:
            with self.clients_lock:
                if client_socket in self.clients:
                    del self.clients[client_socket]
            
            client_socket.close()
            
            if client_nickname and client_address:
                self.stdout.write(self.style.WARNING(f"{client_nickname} ({client_address}) が切断しました"))
                
                ip, port = client_address.rsplit(':', 1)
                current_time = datetime.now(ZoneInfo("Asia/Tokyo")).strftime('%Y/%m/%d %H:%M')
                
                disconnect_message = {
                    "type": "user_update",
                    "username": client_nickname,
                    "ip": ip,
                    "port": port,
                    "status": f"最終ログイン: {current_time}"
                }
                
                self.broadcast_message(json.dumps(disconnect_message), None)
                
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"クライアントのクリーンアップ中にエラーが発生: {e}"))

    def broadcast_message(self, message, exclude_socket=None):
        disconnected_clients = []
        
        with self.clients_lock:
            for sock, (_, _, key) in self.clients.items():
                if sock != exclude_socket:
                    try:
                        encrypted = aes_encrypt(message, key)
                        send_data(sock, encrypted)
                    except Exception as e:
                        self.stderr.write(self.style.ERROR(f"ブロードキャスト中にエラーが発生: {e}"))
                        disconnected_clients.append(sock)

    def handle(self, *args, **options):
        self.setup_logging()
        host = getattr(settings, 'CHAT_SERVER_HOST', get_local_ip()) #好きなIP
        port = getattr(settings, 'CHAT_SERVER_PORT', 12345) #好きなPort

        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((host, port))
            self.server_socket.listen(5)
            self.stdout.write(self.style.SUCCESS(f"サーバーが {host}:{port} で待機中"))

            while self.running:
                try:
                    client_socket, _ = self.server_socket.accept()
                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(client_socket,),
                        daemon=True
                    )
                    client_thread.start()
                except Exception as e:
                    if self.running:
                        self.stderr.write(self.style.ERROR(f"クライアント接続の受け入れ中にエラーが発生: {e}"))

        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING("シャットダウン中..."))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"サーバーエラー: {e}"))
        finally:
            self.running = False
            self.cleanup_server()

    def cleanup_server(self):
        try:
            with self.clients_lock:
                for sock in list(self.clients.keys()):
                    try:
                        sock.close()
                    except:
                        pass
                self.clients.clear()

            if self.server_socket:
                try:
                    self.server_socket.shutdown(socket.SHUT_RDWR)
                except:
                    pass
                finally:
                    self.server_socket.close()
                    
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"サーバーのクリーンアップ中にエラーが発生: {e}"))