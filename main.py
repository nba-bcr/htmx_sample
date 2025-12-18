from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import pandas as pd
from typing import Optional

app = FastAPI(title="NBA Games Dashboard")
templates = Jinja2Templates(directory="templates")

# Load and prepare data
def load_data():
    df = pd.read_csv("games1946-2025.csv")
    # Filter for 2000 onwards
    df = df[df["seasonStartYear"] >= 2000]
    df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")
    df["totalPoints"] = df["pointsHome"] + df["pointsAway"]
    return df

df = load_data()


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Main dashboard page"""
    seasons = sorted(df["seasonStartYear"].unique(), reverse=True)
    teams = sorted(df["Winner"].dropna().unique())
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "seasons": seasons, "teams": teams}
    )


@app.get("/api/stats/overview", response_class=HTMLResponse)
async def get_overview(request: Request):
    """Overview statistics"""
    total_games = len(df)
    avg_home_points = df["pointsHome"].mean()
    avg_away_points = df["pointsAway"].mean()
    home_wins = (df["pointsHome"] > df["pointsAway"]).sum()
    home_win_rate = home_wins / total_games * 100

    return templates.TemplateResponse(
        "partials/overview.html",
        {
            "request": request,
            "total_games": f"{total_games:,}",
            "avg_home_points": f"{avg_home_points:.1f}",
            "avg_away_points": f"{avg_away_points:.1f}",
            "home_win_rate": f"{home_win_rate:.1f}",
        }
    )


@app.get("/api/stats/season-trend", response_class=HTMLResponse)
async def get_season_trend(request: Request):
    """Points trend by season"""
    season_stats = df.groupby("seasonStartYear").agg({
        "pointsHome": "mean",
        "pointsAway": "mean",
        "totalPoints": "mean",
        "game_id": "count"
    }).reset_index()
    season_stats.columns = ["season", "avg_home", "avg_away", "avg_total", "games"]

    return templates.TemplateResponse(
        "partials/season_trend.html",
        {
            "request": request,
            "seasons": season_stats.to_dict("records")
        }
    )


@app.get("/api/stats/team-rankings", response_class=HTMLResponse)
async def get_team_rankings(request: Request, season: Optional[int] = None):
    """Team win rankings"""
    data = df.copy()
    if season:
        data = data[data["seasonStartYear"] == season]

    # Calculate wins for each team
    wins = data["Winner"].value_counts().head(15)
    total_games_by_team = {}

    for team in wins.index:
        home_games = len(data[data["homeTeam"] == team])
        away_games = len(data[data["awayTeam"] == team])
        total_games_by_team[team] = home_games + away_games

    rankings = []
    for team, win_count in wins.items():
        total = total_games_by_team.get(team, 1)
        win_rate = (win_count / total * 100) if total > 0 else 0
        rankings.append({
            "team": team,
            "wins": win_count,
            "games": total,
            "win_rate": f"{win_rate:.1f}"
        })

    return templates.TemplateResponse(
        "partials/team_rankings.html",
        {"request": request, "rankings": rankings, "selected_season": season}
    )


@app.get("/api/stats/high-scoring", response_class=HTMLResponse)
async def get_high_scoring_games(request: Request):
    """Top 10 highest scoring games"""
    top_games = df.nlargest(10, "totalPoints")[
        ["datetime", "homeTeam", "pointsHome", "awayTeam", "pointsAway", "totalPoints", "seasonStartYear"]
    ].copy()
    top_games["datetime"] = top_games["datetime"].dt.strftime("%Y-%m-%d")

    games = []
    for _, row in top_games.iterrows():
        games.append({
            "date": row["datetime"],
            "home_team": row["homeTeam"],
            "home_points": int(row["pointsHome"]),
            "away_team": row["awayTeam"],
            "away_points": int(row["pointsAway"]),
            "total": int(row["totalPoints"]),
            "season": int(row["seasonStartYear"])
        })

    return templates.TemplateResponse(
        "partials/high_scoring.html",
        {"request": request, "games": games}
    )


@app.get("/api/stats/team-detail", response_class=HTMLResponse)
async def get_team_detail(request: Request, team: str):
    """Team specific stats"""
    team_home = df[df["homeTeam"] == team]
    team_away = df[df["awayTeam"] == team]

    home_wins = (team_home["pointsHome"] > team_home["pointsAway"]).sum()
    away_wins = (team_away["pointsAway"] > team_away["pointsHome"]).sum()
    total_wins = home_wins + away_wins
    total_games = len(team_home) + len(team_away)

    avg_points_home = team_home["pointsHome"].mean()
    avg_points_away = team_away["pointsAway"].mean()
    avg_points = (avg_points_home * len(team_home) + avg_points_away * len(team_away)) / max(total_games, 1)

    # Season by season performance
    seasons_data = []
    for season in sorted(df["seasonStartYear"].unique()):
        season_home = team_home[team_home["seasonStartYear"] == season]
        season_away = team_away[team_away["seasonStartYear"] == season]

        wins = (season_home["pointsHome"] > season_home["pointsAway"]).sum() + \
               (season_away["pointsAway"] > season_away["pointsHome"]).sum()
        games = len(season_home) + len(season_away)

        if games > 0:
            seasons_data.append({
                "season": season,
                "wins": wins,
                "games": games,
                "win_rate": f"{(wins/games*100):.1f}"
            })

    return templates.TemplateResponse(
        "partials/team_detail.html",
        {
            "request": request,
            "team": team,
            "total_wins": total_wins,
            "total_games": total_games,
            "win_rate": f"{(total_wins/max(total_games,1)*100):.1f}",
            "avg_points": f"{avg_points:.1f}",
            "seasons": seasons_data[-10:]  # Last 10 seasons
        }
    )


@app.get("/api/stats/playoffs-vs-regular", response_class=HTMLResponse)
async def get_playoffs_vs_regular(request: Request):
    """Compare playoffs vs regular season stats"""
    regular = df[df["isRegular"] == 1]
    playoffs = df[df["isRegular"] == 0]

    stats = {
        "regular": {
            "games": len(regular),
            "avg_total": f"{regular['totalPoints'].mean():.1f}",
            "avg_home": f"{regular['pointsHome'].mean():.1f}",
            "avg_away": f"{regular['pointsAway'].mean():.1f}",
            "home_win_rate": f"{((regular['pointsHome'] > regular['pointsAway']).sum() / len(regular) * 100):.1f}"
        },
        "playoffs": {
            "games": len(playoffs),
            "avg_total": f"{playoffs['totalPoints'].mean():.1f}",
            "avg_home": f"{playoffs['pointsHome'].mean():.1f}",
            "avg_away": f"{playoffs['pointsAway'].mean():.1f}",
            "home_win_rate": f"{((playoffs['pointsHome'] > playoffs['pointsAway']).sum() / max(len(playoffs), 1) * 100):.1f}"
        }
    }

    return templates.TemplateResponse(
        "partials/playoffs_comparison.html",
        {"request": request, "stats": stats}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
