import paramiko
import asyncio
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

            self.model_dir = data.get('model_dir', '~/code/HMamba_code')
            self.venv_dir = data.get('venv_dir', 'mamba')
            self.py_file = data.get('py_file', 'HMambaTrain.py')
            self.dataset = data.get('dataset', 'PETBottle')
            self.epochs = data.get('epochs', '10')
            self.batch_size = data.get('batch_size', '129')
            self.learning_rate = data.get('learning_rate', '0.0001')
            self.validation_freq = data.get('validation_freq', '1')

            self.ssh = paramiko.SSHClient()
            self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.ssh.connect(hostname=hostname, port=port, username=username, password=password)
            if self.ssh is None:
                await self.send("❌ 尚未建立 SSH 連線")
            else:
                await self.send("✅ SSH 連線成功！")

        elif action == 'run-train':
            # 傳送開始訓練的通知訊息給前端
            await self.send(f"🚀 收到 start_training 指令！")

            model = data.get('model')
            if model == 'Mamba':
                self.model_dir = "~/code/HMamba_code"  # 改這裡
            elif model == 'mamba_ok':
                self.model_dir = "~/HMamba_code_OK"
                
            # 執行訓練指令
            cmd = (
                f"cd {self.model_dir} && "
                f"source ~/anaconda3/etc/profile.d/conda.sh && "
                f"conda activate {self.venv_dir} && "
                f"python -u {self.py_file} "
                f"--train_x './training_data/{self.dataset}/cnn-2d_2020-09-09_11-45-24_x.npy' "
                f"--train_y './training_data/{self.dataset}/cnn-2d_2020-09-09_11-45-24_y.npy' "
                f"--valid_x './validation_data/{self.dataset}/cnn-2d_2020-09-09_11-45-24_x.npy' "
                f"--valid_y './validation_data/{self.dataset}/cnn-2d_2020-09-09_11-45-24_y.npy' "
                f"--epochs {self.epochs} "
                f"--batch_size {self.batch_size} "
                f"--lr {self.learning_rate} "
                f"--validation_freq {self.validation_freq}"
            )

            await self.run_command(cmd)

    async def run_command(self, cmd):
        '''
        if self.ssh is None:
            await self.send("❌ 尚未建立 SSH 連線")
            return'''

        shell = self.ssh.invoke_shell()
        shell.send(cmd + "\n")

        buffer = ""
        while True:
            await asyncio.sleep(0.5)
            if shell.recv_ready():
                data = shell.recv(1024).decode("utf-8")
                buffer += data
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    await self.send(line)
            if shell.recv_stderr_ready():
                err = shell.recv_stderr(1024).decode("utf-8")
                await self.send(f"❌ {err}")
            if shell.exit_status_ready():
                break