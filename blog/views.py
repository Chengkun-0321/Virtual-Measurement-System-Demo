from django.shortcuts import render
import paramiko  # 用來做 SSH

# 首頁畫面
def home(request):
    # 透過 mysite/setting.py TEMPLATES = [....] 自動尋找 blog/home.html 顯示首頁
    return render(request, 'blog/home.html')

# 訓練模型畫面
def run_mamba_remote(request):
    output = ""
    if request.method == "POST":
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            ssh.connect(
                hostname='140.137.41.136',  # ✅ ← 改成你的
                username='mamba',
                password='test7410',      # 或使用 key_filename='~/.ssh/id_rsa'
                port=6600
            )
            # ✅ 這裡是你想執行的指令
            stdin, stdout, stderr = ssh.exec_command('python3 /path/to/mamba.py')
            output = stdout.read().decode() + stderr.read().decode()
            ssh.close()
        except Exception as e:
            output = f"連線錯誤：{str(e)}"
    return render(request, 'blog/model_train.html', {'output': output})

# 測試模型畫面
def test_model(request):
    return render(request, 'blog/model_test.html')  # 測試模型頁（可以空的先）

def show_results(request):
    return render(request, 'blog/results.html')  # 顯示結果頁（也可以先空白）