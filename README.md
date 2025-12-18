# NBA Dashboard

FastAPI + HTMX で作成した NBA 試合データダッシュボード。

## Features

- **Overview Stats** - 総試合数、平均得点、ホーム勝率
- **Points by Season** - シーズン別の平均得点推移
- **Regular vs Playoffs** - レギュラーシーズンとプレイオフの比較
- **Team Rankings** - チーム勝率ランキング（シーズン絞り込み可）
- **Highest Scoring Games** - 高得点試合 TOP8
- **Team Analysis** - チーム別詳細統計

## Tech Stack

- **Backend**: FastAPI
- **Frontend**: HTMX + Jinja2 Templates
- **Data**: NBA Games 2000-2025 (CSV)

## Setup

```bash
pip install -r requirements.txt
python main.py
```

http://localhost:8000 にアクセス

## Screenshot

![Dashboard](https://via.placeholder.com/800x450?text=NBA+Dashboard)
