import subprocess
import requests
import time
# InfluxDB 2.x 기준
INFLUXDB_URL="http://localhost:8086/api/v2/write?org=ORGANIZATION_NAME&bucket=BUCKET_NAME&precision=s"
INFLUXDB_TOKEN = "Token" 

headers = {
    "Authorization": f"Token {INFLUXDB_TOKEN}",
    "Content-Type": "text/plain; charset=utf-8"
}

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

def get_gpu_temp():
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=temperature.gpu", "--format=csv,noheader"],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            return float(result.stdout.strip())
        else:
            print(f"GPU 온도 가져오기 실패:{result.stderr}")
            return None
    except FileNotFoundError:
        print(f"nvidia-smi 명령을 찾을 수 없음")
        return None

while True:
    cpu_temp = get_cpu_temp()
    gpu_temp = get_gpu_temp()

    lines = []
    if cpu_temp is not None:
        lines.append(f"cpu_temperature value={cpu_temp}")
    if gpu_temp is not None:
        lines.append(f"cpu_temperature value={gpu_temp}")

    if lines:
        data = '\n'.join(lines)
        try:
            response = requests.post(INFLUXDB_URL, headers = headers, data = data)
            print(f"전송됨: GPU={gpu_temp}°C | CPU={cpu_temp}°C | 코드: {response.status_code}")
        except Exception as e:
            print(f"전송 실패: {e}")
    else:
        print("측정값 없음")
        
    time.sleep(1)  # 1초마다 실행
