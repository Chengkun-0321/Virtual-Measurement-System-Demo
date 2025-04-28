import paramiko
import json
from channels.generic.websocket import AsyncWebsocketConsumer

class TrainConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        self.ssh = None  # 預設 SSH 為 None

    async def disconnect(self, close_code):
        if self.ssh:
            self.ssh.close()

    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get('action')

        if action == 'ssh_connect':
            # SSH 連線
            hostname = data['hostname']
            port = int(data['port'])
            username = data['username']
            password = data['password']

            self.model_dir = data.get('model_dir', '~/HMamba_code')
            self.venv_dir = data.get('venv_dir', 'test_env')
            self.py_file = data.get('py_file', 'HMambaTrain_ov.py')
            self.dataset = data.get('dataset', 'PETBottle')

            self.ssh = paramiko.SSHClient()
            self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.ssh.connect(hostname=hostname, port=port, username=username, password=password)
            await self.send("✅ SSH 連線成功！")

        elif action == 'enter_folder':
            if action == 'enter_folder':
                model = data.get('model')
                if model == 'Mamba':
                    model_dir = "~/桌面/HMamba_code"  # 改這裡
                elif model == 'mamba_ok':
                    model_dir = "~/HMamba_code_OK"
                # 其他模型
                cmd = f"cd {model_dir} && pwd"
                await self.run_command(cmd)

        elif action == 'activate_env':
            cmd = f"source ~/anaconda3/etc/profile.d/conda.sh && conda activate {self.venv_dir} && conda info --envs"
            await self.run_command(cmd)

        elif action == 'run-train':
            # 傳送開始訓練的通知訊息給前端
            await self.send(json.dumps({"message": "🚀 收到 start_training 指令"}))
            # 執行訓練指令
            cmd = (
                f"cd {self.model_dir} && "
                f"source ~/anaconda3/etc/profile.d/conda.sh && "
                f"conda activate {self.venv_dir} && "
                f"python {self.py_file} "
                f"--train_x './training_data/{self.dataset}/cnn-2d_2020-09-09_11-45-24_x.npy' "
                f"--train_y './training_data/{self.dataset}/cnn-2d_2020-09-09_11-45-24_y.npy' "
                f"--valid_x './validation_data/{self.dataset}/cnn-2d_2020-09-09_11-45-24_x.npy' "
                f"--valid_y './validation_data/{self.dataset}/cnn-2d_2020-09-09_11-45-24_y.npy' "
                "--epochs 2 --batch_size 129 --lr 0.0001 --validation_freq 100"
            )
            await self.run_command(cmd)

    async def run_command(self, cmd):
        stdin, stdout, stderr = self.ssh.exec_command(cmd)
        # 即時回傳每一行輸出
        for line in stdout:
            await self.send(line.strip())
        for line in stderr:
            await self.send(line.strip())