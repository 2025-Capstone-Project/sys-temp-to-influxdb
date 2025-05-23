import subprocess
import requests
import time

INFLUXDB_URL="http://localhost:8086/api/v2/write?org=조직이름&bucket=버킷이름&precision=s"
INFLUXDB_TOKEN = "토큰"  # 토큰 필요 (InfluxDB 2.x 기준)



def get_gpu_temp():
    result = subprocess.run(
        ["nvidia-smi", "--query-gpu=temperature.gpu", "--format=csv,noheader"],
        capture_output=True, text=True
    )
    return int(result.stdout.strip())

while True:
    temp = get_gpu_temp()
    line = f"gpu_temperature value={temp}"
    headers = {"Authorization": f"Token {INFLUXDB_TOKEN}"}
    r = requests.post(INFLUXDB_URL, data=line, headers=headers)
    
    print(f"Sent GPU Temp: {temp}°C | Status: {r.status_code}")
    time.sleep(1)  # 1초마다 실행