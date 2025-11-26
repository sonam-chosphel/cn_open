import socket 
import time 
import sys 
from urllib.parse import urlparse 
 
# Constants 
DEFAULT_TIMEOUT = 5 # seconds 
 
def fetch_and_analyze(url_string): 
    """ 
    Initiates an HTTP request, tracks performance metrics, and analyzes the response. 
    """ 
    print(f"--- Starting Analysis for: {url_string} ---") 
     
    # 1. Parse URL 
    try: 
        parsed_url = urlparse(url_string) 
        host = parsed_url.netloc 
        path = parsed_url.path if parsed_url.path else "/" 
        port = 80 # Default to HTTP port 80 for this tool 
         
        # Check if the protocol is supported 
        if parsed_url.scheme not in ('http', ''): 
             raise ValueError("Only plain HTTP (port 80) is supported for low-level analysis.") 
         
    except Exception as e: 
        print(f"Error parsing URL: {e}") 
        return 
 
    T0 = time.time() 
 
    # 2. DNS Lookup (T_DNS) 
    try: 
        ip_address = socket.gethostbyname(host) 
        T_DNS = time.time() 
         
    except socket.gaierror: 
        print(f"Error: Could not resolve hostname '{host}'.") 
        return 
 
    # 3. TCP Connect (T_Connect) 
    try: 
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
        sock.settimeout(DEFAULT_TIMEOUT) 
        sock.connect((ip_address, port)) 
        T_Connect = time.time() 
         
    except socket.error as e: 
        print(f"Error connecting to server {ip_address}:{port}: {e}") 
        return 
 
    # 4. Send Request 
    request_headers = f"GET {path} HTTP/1.1\r\nHost: {host}\r\nConnection: close\r\n\r\n" 
    sock.sendall(request_headers.encode('utf-8')) 
 
    # 5. Receive First Byte (T_TTFB) 
    try: 
        response_data = b"" 
        first_chunk = sock.recv(4096) 
        T_TTFB = time.time() 
        response_data += first_chunk 
         
        # 6. Receive Remaining Data (T_Total) 
        while True: 
            chunk = sock.recv(4096) 
            if not chunk: 
                break 
            response_data += chunk 
         
        T_Total = time.time() 
         
    except socket.timeout: 
        print("Error: Socket timed out while receiving data.") 
        return 
    except socket.error as e: 
        print(f"Error during data transfer: {e}") 
        return 
    finally: 
        sock.close() 
 
    # --- ANALYZER MODULE: Calculate and Print Metrics --- 
     
    t_dns_duration = (T_DNS - T0) * 1000 
    t_connect_duration = (T_Connect - T_DNS) * 1000 
    t_ttfb_latency = (T_TTFB - T_Connect) * 1000 
    t_transfer_duration = (T_Total - T_TTFB) * 1000 
    t_total_time = (T_Total - T0) * 1000 
 
    try: 
        response_text = response_data.decode('utf-8', errors='ignore') 
        header_end = response_text.find('\r\n\r\n') 
         
        if header_end != -1: 
            headers = response_text[:header_end] 
            body = response_text[header_end+4:] 
        else: 
            headers = response_text 
            body = "(No body content found)" 
             
    except Exception: 
        headers = "(Error decoding headers)" 
        body = "(Error decoding body)" 
     
    print("\n--- TIMING METRICS (ms) ---") 
    print(f"| {'Metric':<30} | {'Duration (ms)':<15} |") 
    print(f"| {'-'*30} | {'-'*15} |") 
    print(f"| {'DNS Lookup Duration':<30} | {t_dns_duration:^15.3f} |") 
    print(f"| {'TCP Connection Duration':<30} | {t_connect_duration:^15.3f} |") 
    print(f"| {'Time to First Byte (TTFB)':<30} | {t_ttfb_latency:^15.3f} |") 
    print(f"| {'Content Transfer Duration':<30} | {t_transfer_duration:^15.3f} |") 
    print(f"| {'Total Request Time':<30} | {t_total_time:^15.3f} |") 
     
    print("\n--- RESPONSE HEADERS ---") 
    print(headers) 
     
    print("\n--- RESPONSE BODY PREVIEW ---") 
    print(body[:200] + ('...' if len(body) > 200 else '')) 
 
# Main execution block 
if __name__ == "__main__": 
    if len(sys.argv) != 2: 
        print("Usage: python http_client.py <URL>") 
        print("Example: python http_client.py http://example.com") 
        sys.exit(1) 
         
    url_to_fetch = sys.argv[1] 
    fetch_and_analyze(url_to_fetch)
