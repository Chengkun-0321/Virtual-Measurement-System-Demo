import os
import re
import time
from django.shortcuts import render
import paramiko  # 用來做 SSH
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import json

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
    # 掃描 static/plt 資料夾取得資料夾名稱列表
    static_dir = os.path.join('static', 'plt')
    try:
        checkpoint_folders = [name for name in os.listdir(static_dir) if os.path.isdir(os.path.join(static_dir, name))]
    except FileNotFoundError:
        checkpoint_folders = []

    return render(request, 'blog/model_test.html', {'checkpoint_folders': checkpoint_folders})

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

def list_checkpoint(request):
    """
    先讀取 static/plt/ 下的資料夾名稱，並透過 SSH 查詢遠端權重檔大小
    """
    weights_dir = os.path.join('static', 'plt')
    ssh_info = request.session.get('ssh_info', None)

    if not ssh_info:
        return JsonResponse({"error": "尚未建立 SSH 連線"}, status=400)

    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(
            hostname=ssh_info['hostname'],
            port=int(ssh_info['port']),
            username=ssh_info['username'],
            password=ssh_info['password']
        )

        weights = []
        for folder in os.listdir(weights_dir):
            folder_path = os.path.join(weights_dir, folder)
            if os.path.isdir(folder_path):
                mse_match = re.search(r"valmse_([\d.]+)", folder)
                mse = float(mse_match.group(1)) if mse_match else None
                stat_info = os.stat(folder_path)
                create_time_str = time.strftime(
                    "%Y-%m-%d %H:%M", time.localtime(stat_info.st_mtime)
                )

                # 查詢遠端檔案大小
                remote_dir = "/home/vms/Virtual_Measurement_System_model/Model_code/checkpoints"
                remote_file = f"{remote_dir}/{folder}.h5"
                stdin, stdout, stderr = ssh.exec_command(f'ls -lh "{remote_file}"')
                output = stdout.read().decode()
                if output.strip():
                    parts = output.strip().split()
                    size = output.split()[4]
                    remote_date = f"{parts[5]} {parts[6]}"
                else:
                    size = "未知"
                    remote_date = "未知"

                weights.append({
                    "name": folder,
                    "date": create_time_str,
                    "size": size,
                    "remote_date": remote_date,
                    "mse": mse
                })

        ssh.close()
        weights.sort(key=lambda x: x['date'], reverse=True)
        return JsonResponse(weights, safe=False)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
    
def get_remote_weight_size(request):
    """
    根據檔名查詢遠端權重檔的檔案大小與建立時間
    """
    ssh_info = request.session.get('ssh_info', None)
    filename = request.GET.get('filename')  # 從 GET 參數取得檔案名稱

    if not ssh_info or not filename:
        return JsonResponse({"error": "缺少 SSH 資訊或檔案名稱"}, status=400)

    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(
            hostname=ssh_info['hostname'],
            port=int(ssh_info['port']),
            username=ssh_info['username'],
            password=ssh_info['password']
        )

        remote_dir = "/home/vms/Virtual_Measurement_System_model/Model_code/checkpoints"
        remote_file = f"{remote_dir}/{filename}.h5"

        # 查詢檔案大小與建立時間
        stdin, stdout, stderr = ssh.exec_command(f'ls -l --time-style=+"%Y-%m-%d %H:%M" "{remote_file}"')
        output = stdout.read().decode()
        ssh.close()

        if not output.strip():
            return JsonResponse({"error": "找不到檔案"}, status=404)

        parts = output.strip().split()
        size = parts[4]  # 第 5 欄是檔案大小
        date = f"{parts[5]} {parts[6]}"  # 第 6, 7 欄是時間

        return JsonResponse({"filename": filename, "size": size, "remote_date": date})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
def delete_remote_weights(request):
    """
    刪除遠端權重檔
    """
    if request.method == "POST":
        ssh_info = request.session.get('ssh_info', None)
        if not ssh_info:
            return JsonResponse({"status": "error", "error": "尚未建立 SSH 連線"})

        try:
            data = json.loads(request.body)
            filenames = data.get("filenames", [])

            if not filenames:
                return JsonResponse({"status": "error", "error": "未指定要刪除的檔案"})

            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(
                hostname=ssh_info['hostname'],
                port=int(ssh_info['port']),
                username=ssh_info['username'],
                password=ssh_info['password']
            )

            remote_dir = "/home/vms/Virtual_Measurement_System_model/Model_code"
            for filename in filenames:
                # 刪除權重檔
                remote_file = f"{remote_dir}/checkpoints/{filename}.h5"
                cmd_file = f'rm -f "{remote_file}"'
                stdin, stdout, stderr = ssh.exec_command(cmd_file)
                err = stderr.read().decode()
                if err.strip():
                    return JsonResponse({"status": "error", "error": f"刪除 {filename} 失敗: {err}"})

                # 刪除對應資料夾
                folder_name = f"{remote_dir}/Training_History_Plot/{filename}"
                cmd_folder = f'rm -rf "{folder_name}"'
                stdin, stdout, stderr = ssh.exec_command(cmd_folder)
                err_folder = stderr.read().decode()
                if err_folder.strip():
                    return JsonResponse({"status": "error", "error": f"刪除資料夾 {folder_name} 失敗: {err_folder}"})

            ssh.close()
            return JsonResponse({"status": "success"})
        except Exception as e:
            return JsonResponse({"status": "error", "error": str(e)})

    return JsonResponse({"status": "error", "error": "無效的請求"})