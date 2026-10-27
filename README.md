# 교정하는 화면 비서

Windows의 Edge/Chrome에서 웹페이지 화면을 공유하고, 답변에 대한 교정을 저장해 다음 분석에 재사용하는 로컬 프로토타입입니다.

## 가장 쉬운 Windows 실행 방법

1. Python 3.12 이상을 설치합니다. 설치할 때 Python Launcher(`py`)도 설치하세요.
2. GitHub의 **Code → Download ZIP**으로 내려받아 압축을 풉니다. 폴더 이름은 `aihelper`로 바꿔도 됩니다.
3. 폴더 안의 **start-windows.cmd**를 더블클릭합니다. 처음에는 의존성을 설치하므로 인터넷이 필요합니다.
4. `Uvicorn running`이 표시되면 Edge/Chrome 주소창에 `http://127.0.0.1:8000`을 입력합니다.
5. 종료하려면 실행 창에서 Ctrl+C를 누릅니다. 다음 실행에도 같은 파일을 더블클릭하세요.

Windows 실행 파일은 클라우드 Linux에서 실제 실행하지 않았습니다. 실패하면 창에 표시되는 오류를 확인하세요. 이미 8000번 포트를 쓰는 비서 창이 있다면 먼저 종료하세요.

Git이 있는 경우 PowerShell의 **프로젝트를 둘 폴더**에서:

```powershell
git clone https://github.com/yakan0099/aihelper.git
cd aihelper
.\start-windows.cmd
```

이미 `aihelper`를 Git으로 내려받았다면 **해당 aihelper 폴더**에서:

```powershell
git pull --ff-only
.\start-windows.cmd
```

직접 명령을 실행하려면 **aihelper 폴더**에서:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app:app --host 127.0.0.1 --port 8000
```

## 처음 확인할 기능: 교정 재사용

1. 화면 선택에서 읽고 싶은 웹페이지 탭을 선택합니다. 비서 자체 화면은 UI가 바뀌므로 공유하지 않는 것이 좋습니다.
2. 적용 상황은 `웹페이지 핵심 정리`로 두고 본문을 붙여넣어 분석합니다.
3. 키가 없으면 **데모 모드**입니다. 화면을 해석하거나 AI로 요약하지 않고 본문 발췌와 관련 교정을 보여줍니다.
4. `결론 → 근거 3개 → 주의점 순서로 요약`을 입력하고 수정하기를 누릅니다.
5. 같은 적용 상황에서 다시 분석하면 교정을 불러옵니다. 데모는 교정을 나열하고 API 모드는 모델 입력에 교정을 전달합니다. 모델이 따르는지는 실제 평가가 필요합니다.
6. 기억을 수정·삭제하고 재분석해 확인합니다. 다른 적용 상황에는 사용하지 않습니다.
7. 결과 복사는 공유 세션·픽셀·경과 시간(5분)을 재확인합니다. 화면이 달라졌으면 다시 분석합니다. 영상이나 애니메이션도 변경으로 감지됩니다.

## 실제 이미지 이해와 AI 요약 연결 (선택)

이미지 입력과 Chat Completions JSON 출력을 지원하는 OpenAI 호환 제공자와 모델을 선택하세요. **aihelper 폴더에서 PowerShell**로 다음을 실행합니다. 키를 코드·Git·채팅에 넣지 마세요.

```powershell
$secureKey = Read-Host 'API key' -AsSecureString
$env:ASSISTANT_API_KEY = [System.Net.NetworkCredential]::new('', $secureKey).Password
$env:ASSISTANT_API_BASE = 'https://api.openai.com/v1'
$env:ASSISTANT_MODEL = '선택한 이미지 지원 모델 ID'
.\start-windows.cmd
```

설정은 해당 PowerShell 창에만 적용됩니다. `.env` 파일은 자동으로 읽지 않습니다. 브라우저에는 키를 전달하지 않습니다. 분석 클릭당 API 요청 한 번, 최대 출력 1,200토큰, 자동 재시도 없음입니다. 월 비용 제한은 제공자 콘솔에서 설정하세요. 실제 API 호출과 모델 품질은 아직 검증하지 않았습니다.

## 기록과 제한

FastAPI(MIT), Uvicorn(BSD-3-Clause), HTTPX(BSD-3-Clause), Python SQLite와 브라우저 화면 공유 API를 사용합니다. 학습이나 자동 PC 조작 없이 교정을 조회해 모델 입력에 반영합니다.

`data/assistant.db`에 입력 메타데이터, 출력, 판단 요약, 실패 유형과 시각을 저장합니다. 화면 원본과 붙여넣은 본문은 DB에 저장하지 않지만 답변의 인용문과 교정에는 민감정보가 남을 수 있습니다. API 모드에서는 화면·본문·관련 교정 최대 5개를 제공자에게 전송합니다. DB는 암호화하지 않습니다.

기억 삭제는 미래 검색에서 제외하며, 과거 기록 사본은 `과거 분석·단계 기록 전체 삭제`로 지웁니다. 모델의 비공개 내부 추론은 저장하지 않습니다. 조회를 모델 입력 전에 수행하므로 실제 순서는 화면 수집 → 기억 조회 → 화면 이해 → 답변 결정 → 사용자 확인/실행 → 결과 확인 → 피드백 저장입니다. 복사 요청 시 행동 직전 재확인이 추가됩니다. 실행하지 않은 단계는 성공 기록을 만들지 않습니다. 화면 이해와 요약은 한 번의 API 요청으로 이루어져 두 출력의 오류를 완벽히 독립 진단할 수는 없습니다.

공유 세션 ID는 실제 OS 창 ID가 아닙니다. 검사 이후에도 화면이 바뀔 수 있으므로 이 검사를 자동 클릭·송금 등의 안전 근거로 사용할 수 없습니다. 첫 버전은 결과 텍스트 복사만 제공합니다.

이 앱은 **localhost 전용 프로토타입**입니다. 인터넷에 서버를 공개하지 마세요. 배포 전에는 사용자별 인증·저장소, 데이터 보관 정책, 비용 제한, 설치 패키징과 Windows 실기 검증이 필요합니다.

## 테스트

**aihelper 폴더**에서 Windows:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Linux:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m uvicorn app:app --host 127.0.0.1 --port 8000
```

테스트는 교정 저장·재사용·상황 분리·수정·삭제, 창/픽셀/시간 변경 차단, API 실패 시 키 비노출, 모의 API 교정 전달, 수집 실패 기록, 다른 출처 차단을 다룹니다. 모의 API 테스트는 실제 화면 이해 검증이 아닙니다.
