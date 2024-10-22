from django.shortcuts import render, redirect
from django.http import JsonResponse
from backend.src.connection_manager import ConnectionManager
from backend.src.chat_manager import ChatManager

connection_manager = None
chat_manager = None

def connect_view(request):
    global connection_manager, chat_manager
    if request.method == 'POST':
        nickname = request.POST.get('nickname')
        secret_key = request.POST.get('secret_key')
        ip_address = request.POST.get('ip_address')
        port = request.POST.get('port')

        try:
            connection_manager = ConnectionManager()
            connection_manager.get_or_generate_keys(nickname, secret_key)
            client_address = connection_manager.connect_to_server(ip_address, port)

            chat_manager = ChatManager(connection_manager)
            chat_manager.set_message_callback(lambda message: print(f"受信したメッセージ: {message}"))

            return redirect('chat')
        except Exception as e:
            return render(request, 'connect.html', {'error_message': str(e)})

    return render(request, 'connect.html')

def chat_view(request):
    if not chat_manager:
        return redirect('connect')
    return render(request, 'chat.html')

def send_message(request):
    if request.method == 'POST' and chat_manager:
        message = request.POST.get('message')
        print(f"送信するメッセージ: {message}")
        try:
            formatted_message = f"{message}"
            chat_manager.send_message(formatted_message)
            print("メッセージが正常に送信されました")
            return JsonResponse({'status': 'success'})
        except Exception as e:
            print(f"メッセージ送信中にエラーが発生しました: {str(e)}")
            return JsonResponse({'status': 'error', 'message': str(e)})
    return JsonResponse({'status': 'error', 'message': '無効なリクエストです'})

def get_messages(request):
    global chat_manager
    if chat_manager:
        limit = request.GET.get('limit')
        limit = int(limit) if limit and limit.isdigit() else None
        messages = chat_manager.get_messages(limit)
        return JsonResponse({"messages": messages})
    return JsonResponse({"messages": []})

def get_client_info(request):
    global connection_manager
    if connection_manager:
        # クライアントの情報を辞書形式で整形
        client_info = {
            "nickname": connection_manager.nickname,
            "client_address": {
                "ip": connection_manager.client_address[0] if connection_manager.client_address else None,
                "port": connection_manager.client_address[1] if connection_manager.client_address else None
            },
            "server_connection": {
                "ip": connection_manager.server_ip,
                "port": connection_manager.server_port
            }
        }
        return JsonResponse(client_info)
    return JsonResponse({})

def get_peer_info(request):
    if chat_manager:
        return JsonResponse(chat_manager.peer_info)
    return JsonResponse({})

def disconnect(request):
    global chat_manager, connection_manager
    if chat_manager:
        chat_manager.disconnect()
    chat_manager = None
    connection_manager = None
    return JsonResponse({'status': 'success'})
