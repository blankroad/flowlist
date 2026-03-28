# FlowList

GTD(Getting Things Done) 기반의 할 일 관리 도구. [Things](https://culturedcode.com/things/)를 벤치마킹하여 깔끔한 UI와 GTD 워크플로우를 구현했습니다.

## Features

- **GTD 뷰** — Inbox, Today, Upcoming, Anytime, Someday, Logbook
- **프로젝트 & 영역** — 프로젝트별/책임 영역별 태스크 관리
- **태그** — 태스크에 색상 태그 부착
- **체크리스트** — 태스크 내 하위 항목 관리
- **검색** — FTS5 기반 전문 검색 (`Cmd+F`)
- **Quick Entry** — 빠른 태스크 추가 (`Cmd+Shift+N`)
- **키보드 단축키** — `Cmd+1~6` 뷰 전환, `Cmd+N` 새 태스크
- **그룹 뷰** — Today(Overdue/Today), Upcoming(Tomorrow/This Week/Later), Logbook(Today/Yesterday/Earlier)

## Tech Stack

- **Backend**: Python + Flask
- **Frontend**: Vanilla HTML/CSS/JS (프레임워크 없음)
- **Database**: SQLite (FTS5 검색 지원)
- **License-friendly**: Qt/PySide 없이 웹 기반 UI

## Quick Start

```bash
pip install flask
python main.py
```

브라우저가 자동으로 `http://127.0.0.1:5000` 에서 열립니다.

## Project Structure

```
├── main.py              # 서버 시작 + 브라우저 열기
├── requirements.txt     # flask>=3.0
├── app/
│   ├── api.py           # REST API 엔드포인트
│   ├── config.py        # 설정
│   └── models/          # SQLite 모델 (Task, Project, Area, Tag)
├── static/
│   ├── index.html       # 3-panel 레이아웃
│   ├── style.css        # Things 스타일 CSS
│   └── app.js           # 클라이언트 로직
└── tests/
```

## Keyboard Shortcuts

| 단축키 | 기능 |
|--------|------|
| `Cmd+N` | 새 태스크 입력 포커스 |
| `Cmd+Shift+N` | Quick Entry 다이얼로그 |
| `Cmd+F` | 검색 |
| `Cmd+1~6` | GTD 뷰 전환 |
| `Escape` | 패널/검색 닫기 |
