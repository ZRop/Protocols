import subprocess
import re
import socket
import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

def resolve_hostname(hostname):
    try:
        return socket.gethostbyname(hostname)
    except socket.gaierror:
        raise ValueError(f"Не удалось разрешить доменное имя: {hostname}")

def run_traceroute(target):
    try:
        command = ['tracert', '-d', '-w', '1000', '-h', '30', target]
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,encoding="cp866", text=True)
        
        output, error = process.communicate(timeout=60)
        
        if process.returncode != 0:
            if "Unable to resolve target system name" in error:
                raise ValueError(f"Не удалось разрешить имя: {target}")
            elif "timed out" in error.lower():
                raise TimeoutError("Трассировка прервана по таймауту")
            else:
                raise RuntimeError(f"Ошибка трассировки: {error.strip()}")
        
        return output
    except subprocess.TimeoutExpired:
        process.kill()
        raise TimeoutError("Трассировка заняла слишком много времени")
    except FileNotFoundError:
        raise RuntimeError("Команда tracert/traceroute не найдена. Убедитесь, что она установлена в системе.")

def parse_traceroute(output):
    ip_pattern = re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b')
    hops = []
    
    for line in output.splitlines():
        # Пропускаем пустые строки и строки с *
        if not line.strip() or '*' in line:
            continue
        
    
        ips = ip_pattern.findall(line)
        if ips:
            hop_ip = ips[-1]
            
            hops.append(hop_ip)
    
    return hops

def get_as_number(ip):
    if is_private_ip(ip):
        return "Private"
    try:
       
        url = f"https://stat.ripe.net/data/network-info/data.json?resource={ip}"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if 'data' in data and 'asns' in data['data'] and data['data']['asns']:
            return data['data']['asns'][0]
        return "Unknown"
    except requests.RequestException:
        return "Error"

def is_private_ip(ip):
    parts = list(map(int, ip.split('.')))
    
    # 10.0.0.0/8
    if parts[0] == 10:
        return True
    # 172.16.0.0/12
    if parts[0] == 172 and 16 <= parts[1] <= 31:
        return True
    # 192.168.0.0/16
    if parts[0] == 192 and parts[1] == 168:
        return True
    
    return False

def main():
    print("Трассировка автономных систем")
    print("Введите доменное имя или IP-адрес для трассировки:")
    
    target = input().strip()
    
    try:
        try:
            socket.inet_aton(target)
            target_ip = target
        except socket.error:
            target_ip = resolve_hostname(target)
        
        print(f"\nНачинаем трассировку до {target} ({target_ip})...\n")
        
        traceroute_output = run_traceroute(target_ip)
        print("Результат трассировки:")
        print(traceroute_output)
        hops = parse_traceroute(traceroute_output)
        
        if not hops:
            print("\nНе удалось определить маршрут. Возможно, трассировка не удалась.")
            return
        
        print("\nОпределение автономных систем для каждого узла...")
        
        as_numbers = {}
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_ip = {executor.submit(get_as_number, ip): ip for ip in hops}
            for future in as_completed(future_to_ip):
                ip = future_to_ip[future]
                try:
                    as_numbers[ip] = future.result()
                except Exception as e:
                    as_numbers[ip] = f"Error: {str(e)}"
                time.sleep(0.5)


        #print("Вывод парсинга галимый",parse_traceroute(traceroute_output))
        print("\nРезультаты:")
        print("{:<5} {:<15} {:<15}".format("No", "IP", "AS"))
        print("-" * 40)
        for i, ip in enumerate(hops[1:], 1):
            print("{:<5} {:<15} {:<15}".format(i, ip, as_numbers.get(ip, "Unknown")))
    
    except Exception as e:
        print(f"\nОшибка: {str(e)}")

if __name__ == "__main__":
    main()
