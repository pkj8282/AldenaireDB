import websocket
import json
import zlib
import threading
import time
from datetime import datetime

# --- [CONFIGURATION] ---
CONFIG = {
    "TOKEN": "",
    "GUILD_ID": "1414190614362193972",
    "CHANNEL_ID": "1444377099887706239",
    "SAVE_PATH": "list.json",
    "RANGES": [
        [[0, 99]],
        [[0, 99], [100, 199]],
        [[0, 99], [200, 299]],
        [[0, 99], [300, 399]],
    ],
    "WHITE_LIST": [
        '1328251938734870681',
        '1285106038315679789',
        '938703449061736480',
        '842018013640392725',
        '708274928360751186',
        '856775767107436584'
    ]
}

class DiscordMemberScraper:
    def __init__(self):
        self.ws = websocket.WebSocket()
        self.decompressor = zlib.decompressobj()
        self.collected_db = {}
        self.is_running = True

    # 1. 네트워크 및 통신 레이어
    def connect(self):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 게이트웨이 연결 중...")
        self.ws.connect("wss://gateway.discord.gg/?v=9&encoding=json")
        self.listen()

    def send_json(self, payload):
        self.ws.send(json.dumps(payload))

    def listen(self):
        while self.is_running:
            try:
                raw_msg = self.ws.recv()
                data = self._decompress_msg(raw_msg)
                if not data: continue
                
                self._handle_payload(data)
            except Exception as e:
                print(f"수신 에러: {e}")
                break

    def _decompress_msg(self, raw_msg):
        """압축된 바이너리 패킷 해제 및 JSON 로드"""
        if isinstance(raw_msg, bytes):
            msg_data = self.decompressor.decompress(raw_msg)
            return json.loads(msg_data.decode('utf-8')) if msg_data else None
        return json.loads(raw_msg)

    # 2. 프로토콜 핸들러 (OP 코 및 이벤트 관리)
    def _handle_payload(self, data):
        op = data.get('op')
        t = data.get('t')

        if op == 10: # Hello
            interval = data['d']['heartbeat_interval']
            threading.Thread(target=self._heartbeat, args=(interval,), daemon=True).start()
            self._identify()

        elif t == 'READY':
            print("인증 성공. 스캔 시퀀스를 시작합니다.")
            threading.Thread(target=self._scan_sequence, daemon=True).start()

        elif t == 'GUILD_MEMBER_LIST_UPDATE':
            self._parse_member_list(data)

    def _identify(self):
        self.send_json({
            "op": 2,
            "d": {
                "token": CONFIG["TOKEN"],
                "capabilities": 16381,
                "properties": {"os": "Windows", "browser": "Chrome", "device": ""}
            }
        })

    def _heartbeat(self, interval):
        while self.is_running:
            time.sleep(interval / 1000)
            self.send_json({"op": 1, "d": None})

    # 3. 비즈니스 로직 (멤버 스캔 및 저장)
    def _scan_sequence(self):
        """브라우저의 스크롤 동작을 시뮬레이션"""
        for r in CONFIG["RANGES"]:
            print(f"구간 요청: {r}")
            self._request_range(r)
            time.sleep(4) # 서버 응답 대기 및 안전 지연
        
        print(f"\n수집 완료. 총 {len(self.collected_db)}명 확보.")
        self.save_to_file()
        self.is_running = False

    def _request_range(self, ranges):
        """브라우저 규격의 op:37 패킷 전송"""
        payload = {
            "op": 37,
            "d": {
                "subscriptions": {
                    CONFIG["GUILD_ID"]: {
                        "typing": True, "threads": True, "activities": True,
                        "members": [], "member_updates": False,
                        "channels": { CONFIG["CHANNEL_ID"]: ranges },
                        "thread_member_lists": []
                    }
                }
            }
        }
        self.send_json(payload)

    def _parse_member_list(self, data):
        """전역 변수에 유저 정보 적재 (중복 자동 제거)"""
        ops = data['d'].get('ops', [])
        for op in ops:
            if op.get('op') in ['SYNC', 'INSERT']:
                for item in op.get('items', []):
                    if 'member' in item:
                        m = item['member']
                        u = m['user']
                        if u['bot'] == False:
                            self.collected_db[u['id']] = {'global_name' : u['global_name'], 'username' : u['username'], 'server_name' : m['nick']}
                            print(f"{u['id']} : {u['global_name']}, {u['username']}, {m['nick']}")
        print(f"수집 진행도: {len(self.collected_db)}명 명단 확보 중...", end='\r')

    def save_to_file(self):
        for i in range(len(CONFIG["WHITE_LIST"])):
            _person = CONFIG["WHITE_LIST"][i]
            print(_person)
            if _person in self.collected_db:
                self.collected_db.pop(_person)
        print(f"화이트 리스트 처리 후 : {len(self.collected_db.keys())} 명 확인됨.")
        with open(CONFIG["SAVE_PATH"], "w", encoding="utf-8") as f:
            json.dump(self.collected_db, f, ensure_ascii=False, indent=4)
        print(f"데이터가 {CONFIG["SAVE_PATH"]}에 성공적으로 저장되었습니다.")

# --- [MAIN] ---
if __name__ == "__main__":
    scraper = DiscordMemberScraper()
    try:
        scraper.connect()
    except KeyboardInterrupt:
        print("\n사용자에 의해 중단됨. 현재까지의 데이터를 저장합니다.")
        scraper.save_to_file()