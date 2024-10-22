from datetime import datetime
import json
import threading

class ChatManager:
    def __init__(self, connection_manager):
        self.connection_manager = connection_manager
        self.message_callback = None
        self.peer_info_callback = None
        self.peer_info = {}
        self.messages = []
        self.connection_manager.set_message_callback(self._internal_message_handler)
        self.message_lock = threading.Lock()

    def set_message_callback(self, callback):
        self.message_callback = callback

    def set_peer_info_callback(self, callback):
        self.peer_info_callback = callback

    def update_peer_info(self, nickname, ip, port, status):
        self.peer_info[nickname] = {"ip": ip, "port": port, "status": status}
        if self.peer_info_callback:
            self.peer_info_callback(self.peer_info)

    def send_message(self, message):
        try:
            self.connection_manager.send_message(message)
        except Exception as e:
            print(f"メッセージ送信中にエラーが発生: {str(e)}")
            raise

    def _internal_message_handler(self, message):
        try:
            try:
                decoded_message = json.loads(message)
                if decoded_message.get("type") == "user_update":
                    self.update_peer_info(
                        decoded_message["username"],
                        decoded_message["ip"],
                        decoded_message["port"],
                        decoded_message["status"]
                    )
                    return
                elif decoded_message.get("type") == "message":
                    self.add_message(message)
                    return
            except json.JSONDecodeError:
                pass
        except Exception as e:
            print(f"メッセージ処理中にエラーが発生: {str(e)}")

    def _clean_message(self, message):
        parts = message.split(':\n')
        if len(parts) > 1:
            return parts[0] + ': ' + parts[-1].strip()
        return message

    def add_message(self, message):
        with self.message_lock:
            if message not in self.messages:
                self.messages.append(message)
                if self.message_callback:
                    self.message_callback(message)

    def disconnect(self):
        try:
            self.connection_manager.close_connection()
        except Exception as e:
            print(f"切断中にエラーが発生: {str(e)}")

    def get_messages(self, limit=None, since_timestamp=None):
        with self.message_lock:
            if since_timestamp:
                filtered_messages = [msg for msg in self.messages if self._get_timestamp(msg) > since_timestamp]
            else:
                filtered_messages = self.messages.copy()

            if limit:
                return filtered_messages[-limit:]
            return filtered_messages

    def _get_timestamp(self, message):
        try:
            parts = message.split(' - ')
            if len(parts) >= 2:
                timestamp_str = parts[1].split(':')[0] + ':' + parts[1].split(':')[1]
                return datetime.strptime(timestamp_str, "%H:%M:%S %d/%m/%Y")
        except:
            pass
        return datetime.min