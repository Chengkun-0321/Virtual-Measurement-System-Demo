from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),                         # 首頁
    path('train/', views.run_mamba_remote, name='train'),      # 模型訓練頁
    path('test/', views.test_model, name='test'),              # 測試模型頁
    path('results/', views.show_results, name='results'),      # 顯示結果頁
]