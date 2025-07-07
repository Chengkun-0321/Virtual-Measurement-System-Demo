from django.shortcuts import render
import paramiko  # 用來做 SSH
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt

def execute_train_command(ssh, model_dir, venv_dir, py_file, dataset):
    # 執行訓練指令
    train_cmd = (
        f"python {py_file} "
        f"--train_x './training_data/{dataset}/cnn-2d_2020-09-09_11-45-24_x.npy' "
        f"--train_y './training_data/{dataset}/cnn-2d_2020-09-09_11-45-24_y.npy' "
        f"--valid_x './validation_data/{dataset}/cnn-2d_2020-09-09_11-45-24_x.npy' "
        f"--valid_y './validation_data/{dataset}/cnn-2d_2020-09-09_11-45-24_y.npy' "
        "--epochs 2 --batch_size 129 --lr 0.0001 --validation_freq 100"
    )
    stdin, stdout, stderr = ssh.exec_command(
        f"cd {model_dir} && source ~/anaconda3/etc/profile.d/conda.sh && conda activate {venv_dir} && {train_cmd}"
    )
    output = stdout.read().decode()
    error = stderr.read().decode()
    return output + error

# 首頁畫面
@csrf_exempt
def home(request):
    # 透過 mysite/setting.py TEMPLATES = [....] 自動尋找 blog/home.html 顯示首頁
    if request.method == "POST":
        # 存進 session
        request.session['hostname'] = request.POST.get('hostname', '')
        request.session['port'] = request.POST.get('port', '')
        request.session['username'] = request.POST.get('username', '')
        request.session['password'] = request.POST.get('password', '')
        return render(request, 'home.html')

    
    # 讀取 session 並傳到 template
    context = {
        'hostname': request.session.get('hostname', ''),
        'port': request.session.get('port', ''),
        'username': request.session.get('username', ''),
        'password': request.session.get('password', '')
    }
    return render(request, 'blog/home.html', context)
    

def run_mamba_remote(request):
    if request.method == "POST":
        hostname = request.POST.get('hostname') or request.session.get('hostname')     # 伺服器IP
        port = int(request.POST.get('port') or request.session.get('port'))            # 埠號
        username = request.POST.get('username') or request.session.get('username')     # 使用者帳號
        password = request.POST.get('password') or request.session.get('password')     # 密碼

        model = request.POST['model']                   # 選擇的模型架構名稱
        dataset = request.POST['dataset']               # 資料來源
        mean = request.POST['mean']                     # 中心值
        upper = request.POST['boundary_upper']          # 上界
        lower = request.POST['boundary_lower']          # 下界
        checkpoint = request.POST['checkpoint_path']    # 權重檔路徑

        # 根據 model 名稱決定路徑與環境
        if model == "Mamba":
            model_dir = "~/Virtual_Measurement_System_model/HMamba_code"
            venv_dir = "mamba"
            py_file = "HMambaTrain_ov.py"
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

        # SSH 連線與執行
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname = hostname, port = port, username = username, password = password)

        '''
        # 分三段執行，並收集輸出
        # 1. 進入模型資料夾
        stdin, stdout, stderr = ssh.exec_command(f"cd {model_dir} && pwd")
        folder_info = stdout.read().decode() + stderr.read().decode()

        # 2. 啟動 conda 環境
        stdin, stdout, stderr = ssh.exec_command(f"source ~/anaconda3/etc/profile.d/conda.sh && conda activate {venv_dir} && conda info --envs")
        env_info = stdout.read().decode() + stderr.read().decode()

        # 3. 執行訓練指令
        train_output = execute_train_command(ssh, model_dir, venv_dir, py_file, dataset)

        # 合併三段輸出
        result = folder_info + "\n" + env_info + "\n" + train_output
        ssh.close()

        print("🔄 載入模型訓練頁面")
        return render(request, 'blog/model_train.html', {'output': result})
        '''
        return render(request, 'blog/model_train.html')
    
    return render(request, 'blog/model_train.html')

# 測試模型畫面
def test_model(request):
    return render(request, 'blog/model_test.html')  # 測試模型頁（可以空的先）

def show_results(request):
    return render(request, 'blog/results.html')  # 顯示結果頁（也可以先空白）

def ping_test(request):
    if request.method == 'POST':
        # 取得 port 並檢查格式是否正確（必須是數字）
        port_str = request.POST.get('port')
        if not port_str or not port_str.isdigit():
            # 如果 port 沒有填或不是數字，回傳錯誤訊息
            return JsonResponse({'status': 'error', 'message': '⚠️ 請輸入有效的 Port 號碼'})

        # 取得其他 SSH 連線資訊（hostname、username、password）
        hostname = request.POST.get('hostname')
        username = request.POST.get('username')
        password = request.POST.get('password')

        # 將這些 SSH 資訊暫存到 Django session（給其他頁面用）
        request.session['ssh_info'] = {
            'hostname': hostname,
            'port': port_str,
            'username': username,
            'password': password
        }

        # 建立 SSH 連線測試
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            ssh.connect(hostname=hostname, port=int(port_str), username=username, password=password)
            ssh.close()
            return JsonResponse({'status': 'success', 'message': '✅ 成功連線！'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'❌ 連線失敗：{str(e)}'})
        
# 模型管理畫面
def manage_models(request):
    return render(request, 'blog/model_manage.html')