from django.urls import path
from . import views
from blog.views import ping_test

urlpatterns = [
    path('ping/', ping_test, name='ping_test'),                # SSH 連線測試用於首頁的「🧪 測試連線」功能
    # 這個路由處理從首頁發出的 SSH 連線測試請求（/ping/）
    # 接收表單欄位：hostname, port, username, password
    # 回傳 JSON 結果並顯示在首頁
    
    path('', views.home, name='home'),                         # 首頁(根目錄)
    path('train/', views.run_mamba_remote, name='train'),      # 模型訓練頁
    path('test/', views.test_model, name='test'),              # 測試模型頁
    path('results/', views.show_results, name='results'),      # 顯示結果頁
]