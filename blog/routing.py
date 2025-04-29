# 匯入 Django 提供的 re_path，用來建立 WebSocket 的路由（支援正規表達式）
from django.urls import re_path

# 匯入同資料夾的 consumers 模組（裡面定義了 WebSocket 的邏輯）
from . import consumers

# 定義 WebSocket 路由列表
websocket_urlpatterns = [
    # 當網址為 ws/train/ 時，使用 TrainConsumer 處理 WebSocket 連線
    re_path(r'ws/CMD/$', consumers.CMDConsumer.as_asgi()),
]