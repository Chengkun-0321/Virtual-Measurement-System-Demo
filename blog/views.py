from django.shortcuts import render
import paramiko  # 用來做 SSH

# 首頁畫面
def home(request):
    # 透過 mysite/setting.py TEMPLATES = [....] 自動尋找 blog/home.html 顯示首頁
    return render(request, 'blog/home.html')

# 訓練模型畫面
def run_mamba_remote(request):
    if request.method == "POST":
        model = request.POST['model']           # 選擇的模型架構名稱
        dataset = request.POST['dataset']       # 資料來源
        mean = request.POST['mean']             # 中心值
        upper = request.POST['upper']           # 上界
        lower = request.POST['lower']           # 下界
        checkpoint = request.POST['checkpoint'] # 權重檔路徑

        # 根據 model 名稱決定路徑與環境
        if model == "mamba_original":
            model_dir = "~/HMamba_code"
            venv_dir = "venv"
            py_file = "HMambaTest.py"
        elif model == "mamba_ok":
            model_dir = "~/HMamba_code_OK"
            venv_dir = "env_ok"
            py_file = "HMambaTest_ok.py"
        elif model == "mamba_hotpic":
            model_dir = "~/HMamba_code_HotPic"
            venv_dir = "env_hotpic"
            py_file = "HMambaTest_ok_HotPicture.py"
        else:
            return render(request, 'blog/model_train.html', {'output': "❌ 無效的模型選擇"})

        # 組合遠端指令（格式化排版）
        cmd = (
            f"cd {model_dir} && "       #進入模型的資料夾
            f"source ~/anaconda3/etc/profile.d/conda.sh && conda activate {venv_dir} && "   #進入專屬訓練環境
            f"python {py_file} \\ \n"
            f"  --test_x_path './testing_data/{dataset}/cnn-2d_2020-09-09_11-45-24_x.npy' \\ \n"
            f"  --test_y_path './testing_data/{dataset}/cnn-2d_2020-09-09_11-45-24_y.npy' \\ \n"
            f"  --checkpoint_path '{checkpoint}' \\ \n"
            f"  --mean {mean} \\ \n"
            f"  --boundary_upper {upper} \\ \n"
            f"  --boundary_lower {lower}"
        )

        # SSH 連線與執行
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname='你的伺服器IP', port=22, username='你的帳號', password='你的密碼')

        stdin, stdout, stderr = ssh.exec_command(cmd)
        result = stdout.read().decode() + stderr.read().decode()
        ssh.close()

        return render(request, 'blog/model_train.html', {'output': result})

# 測試模型畫面
def test_model(request):
    return render(request, 'blog/model_test.html')  # 測試模型頁（可以空的先）

def show_results(request):
    return render(request, 'blog/results.html')  # 顯示結果頁（也可以先空白）