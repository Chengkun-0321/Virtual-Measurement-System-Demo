"""
ASGI config for mysite project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

# 匯入 Python 標準庫 os，用來設定環境變數
import os

# 匯入 Django 提供的 ASGI 應用，處理 HTTP 協定（網頁請求）
from django.core.asgi import get_asgi_application

# 匯入 Django Channels 的路由模組
# ProtocolTypeRouter 根據協定類型分配不同應用（HTTP 或 WebSocket）
# URLRouter 負責處理 WebSocket 的路由
from channels.routing import ProtocolTypeRouter, URLRouter

# 匯入自訂的 WebSocket 路由配置（blog/routing.py）
import blog.routing

# 設定 Django 專案的設定檔位置（告訴 Django 要用哪個 settings）
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')

# 定義 ASGI 應用程式
application = ProtocolTypeRouter({
    # HTTP 協定交給 Django 預設的 ASGI 應用處理（一般網頁請求）
    "http": get_asgi_application(),

    # WebSocket 協定交給 URLRouter，並使用 blog.routing 裡的 websocket_urlpatterns 路由
    "websocket": URLRouter(
        blog.routing.websocket_urlpatterns
    ),
})