# server_b.py

import socket
import threading
import json
import time
import requests

HOST = '0.0.0.0'
PORT = 5000
PORT2 = 5001

# InfluxDB 2.x 기준
INFLUXDB_URL="http://localhost:8086/api/v2/write?org=HANBAT&bucket=TEST_TEMPER&precision=s"
INFLUXDB_TOKEN = "DBVhHP1YdnCf-WIQNgZe_Z_ttZbtol60gKZ_Y3OLVY5LlcuHhfUzu5-JoocVr94uHyFidB48tQCSXpVBmBTvOg==" 

headers = {
    "Authorization": f"Token {INFLUXDB_TOKEN}",
    "Content-Type": "text/plain; charset=utf-8"
}

# 공유 데이터 구조와 동기화를 위한 락
data = {
    'cpu_temperature': None,
    'gpu_temperature': None,
    'model_result': None
}

REQUIRED_KEYS = {
    'Temperature': ['cpu_temperature', 'gpu_temperature'],
    'Model': ['model_result']
}

flags = {
    'Temperature': False,  # client_ab로부터 a,b가 들어왔는지 여부
    'Model': False   # client_cd로부터 c,d가 들어왔는지 여부
}

# 스레드 간 안전을 위한 Lock
lock = threading.Lock()

def handle_client(conn, addr):
    """
    클라이언트(A)로부터 a, b 값을 수신하여
    전역 변수 c, d에 저장.
    """
    print(f"[B] Connection from {addr}")
    with conn, conn.makefile('r') as rf:
        for line in rf:
            line = line.strip()
            if not line:
                continue

            try:
                data_json= json.loads(line)
                cpu_val = data_json.get('a')
                gpu_val = data_json.get('b')
            except json.JSONDecodeError:
                print(f"[서버-CPU/GPU] JSON 파싱 실패: {line}")
                continue

            with lock:
                data['cpu_temperature']= cpu_val
                data['gpu_temperature']= gpu_val
                print(f"Clien 1 lock || cpu = {data['cpu_temperature']} gpu = {data['gpu_temperature']}")

                if data['cpu_temperature'] is not None and data['gpu_temperature'] is not None:
                    flags['Temperature']= True
                else:
                    flags['Temperature']= False
                
                if flags['Temperature'] and flags['Model']:
                    _send_to_influxdb_and_reset()             

def handle_client2(conn, addr):
    """
    클라이언트(A)로부터 a, b 값을 수신하여
    전역 변수 c, d에 저장.
    """
    print(f"[B] Connection from {addr}")
    with conn, conn.makefile('r') as rf:
        for line in rf:
            line = line.strip()
            if not line:
                continue

            try:
                data_json= json.loads(line)
                model_val = data_json.get('c')
                print("Clien 2 으로 수신받음")
            except json.JSONDecodeError:
                print(f"[서버-CPU/GPU] JSON 파싱 실패: {line}")
                continue

            with lock:
                data['model_result']= model_val
                print(f"Clien 2 lock || model = {data['model_result']}")

                if data['model_result'] is not None:
                    flags['Model']= True
                else:
                    flags['Model']= False
                
                if flags['Temperature'] and flags['Model']:
                    _send_to_influxdb_and_reset()

def _send_to_influxdb_and_reset():
    lines= []
    lines.append(f"cpu_temperature value={data['cpu_temperature']}")
    lines.append(f"gpu_temperature value={data['gpu_temperature']}")
    lines.append(f"model_result value=\"{data['model_result']}\"")
    print("gogogogoog")

    payload = "\n".join(lines)
    print(payload)

    try:
        print(payload)
        response = requests.post(INFLUXDB_URL, headers=headers, data=payload)
        print(response.text)
        print(f"[서버:INFLUX] 전송 완료 → "
              f"CPU={data['cpu_temperature']} | GPU={data['gpu_temperature']} | "
              f"MODEL={data['model_result']} | HTTP {response.status_code}")
    except Exception as e:
        print(f"[서버:INFLUX] 전송 실패: {e}")

    # 플래그와 데이터를 리셋
    flags['Temperature'] = False
    flags['Model'] = False
    data['cpu_temperature']= None
    data['gpu_temperature']= None
    data['model_result']= None


def main():

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server1, socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server2:
        server1.bind((HOST, PORT))
        server1.listen()
        print(f"[B] Listening on {HOST}:{PORT}")
        
        server2.bind((HOST, PORT2))
        server2.listen()
        print(f"[B] Listening on {HOST}:{PORT2}")
        
        while True:
            conn1, addr1 = server1.accept()
            # 클라이언트마다 별도 스레드로 처리
            threading.Thread(target=handle_client, args=(conn1, addr1), daemon=True).start()
            
            conn2, addr2 = server2.accept()
            # 클라이언트마다 별도 스레드로 처리
            threading.Thread(target=handle_client2, args=(conn2, addr2), daemon=True).start()

if __name__ == '__main__':
    main()


