import paramiko
import json
from channels.generic.websocket import AsyncWebsocketConsumer

class TrainConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()

    async def receive(self, text_data):
        data = json.loads(text_data)
        hostname = data['hostname']
        port = int(data['port'])
        username = data['username']
        password = data['password']

        print(f"接收到 SSH 連線資料：hostname={hostname}, port={port}, username={username}")

        # 建立 SSH
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=hostname, port=port, username=username, password=password)
        
        cmd = "echo 'Hello from remote!'"  # 這裡換成你要跑的指令
        stdin, stdout, stderr = ssh.exec_command(cmd)
        
        for line in stdout:
            await self.send(line.strip())

        ssh.close()