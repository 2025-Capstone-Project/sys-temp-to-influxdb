import subprocess
import psutil
import socket
import time
import random
import json

HOST = 'IP'          # Raspberry Pi 서버 IP
PORT = 5000          # Raspberry Pi 서버 Port

# CPU 온도
def get_cpu_temp():
    try:
        temps= psutil.sensors_temperatures()
        for name, entries in temps.items():
            for entry in entries:
                if entry.label == '' or 'Package' in entry.label or 'Core' in entry.label:
                    return entry.current
        return None
    except Exception as e:
        print(f"CPU 온도 가져오기 실패:{e}")
        return None

# GPU 온도
def get_gpu_temp():
    try:
        result = subprocess.run(
            ['nvidia-smi', '--query-gpu=temperature.gpu', '--format=csv,noheader,nounits'],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        if result.returncode == 0:
            return float(result.stdout.strip())
        else:
            print(f"GPU 온도 가져오기 실패:{result.stderr}")
            return None
    except FileNotFoundError:
        print(f"nvidia-smi 명령을 찾을 수 없음")
        return None
        
# 소켓 통신 코드 (loop)
def send_loop():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        print(f"[A] Connected to {HOST}:{PORT}")
        while True:
            cpu_temp = get_cpu_temp()
            gpu_temp = get_gpu_temp()
            payload = json.dumps({'cpu_temp': cpu_temp, 'gpu_temp': gpu_temp})
            s.sendall(payload.encode('utf-8') + b'\n')
            print(f"[A] Sent -> cpu_temp: {cpu_temp:.2f}, gpu_temp: {gpu_temp:.2f}")
            time.sleep(1)  # 1초마다 전송

if __name__ == '__main__':
    send_loop()
