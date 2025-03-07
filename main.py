from flask import Flask, request, jsonify, render_template_string
import requests

app = Flask(__name__)

# API setup for RapidAPI Bet365
RAPIDAPI_KEY = "a99d97b8a4msh3c9add594bc309dp109ed3jsn8061a3f46309"
RAPIDAPI_HOST = "bet365-api-inplay.p.rapidapi.com"


def fetch_bet365_odds():
    url = "https://bet365-api-inplay.p.rapidapi.com/bet365/get_betfair_forks"
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": RAPIDAPI_HOST
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching Bet365 odds: {e}")
        return None


# Dummy probability function (replace with ML model later)
def estimate_probabilities(game, market):
    # Dummy probs for demo; refine with real data or ML
    if "Manchester United" in game["teams"]:
        base = {"home": 0.50, "draw": 0.20, "away": 0.30, "btts_yes": 0.60, "btts_no": 0.40}
    elif "Chelsea" in game["teams"]:
        base = {"home": 0.35, "draw": 0.25, "away": 0.40, "btts_yes": 0.55, "btts_no": 0.45}
    else:
        base = {"home": 0.40, "draw": 0.25, "away": 0.35, "btts_yes": 0.50, "btts_no": 0.50}

    # Extend for other markets
    if market.startswith("correct_score_"):
        score = market.split("_")[2:]
        return 0.10 if score in ["1-0", "0-1", "1-1"] else 0.05  # Higher for common scores
    elif market.startswith("goalscorer_"):
        return 0.30  # Flat prob for demo
    elif market.startswith("corners_"):
        return 0.50 if market == "corners_over_8" else 0.40  # Over/under example
    return base.get(market, 0.0)


# Calculate Expected Value
def calculate_ev(odds, prob, stake=1):
    return (prob * odds * stake) - stake


# Optimize bets based on EV and capital
def optimize_bets(games, capital):
    bets = []
    for game in games:
        odds = game.get("odds", {})
        for market, odd in odds.items():
            if odd:  # Skip blank inputs
                prob = estimate_probabilities(game, market)
                ev = calculate_ev(odd, prob)
                if ev > 0:  # Only bet on positive EV
                    bets.append({
                        "game": game["teams"],
                        "market": market.replace("_", " ").capitalize(),
                        "odds": odd,
                        "prob": prob,
                        "ev": ev
                    })

    total_ev = sum(bet["ev"] for bet in bets)
    if total_ev <= 0:
        return {"bets": [], "message": "No positive EV bets found"}

    for bet in bets:
        stake = (bet["ev"] / total_ev) * capital
        bet["stake"] = round(stake, 2)
        bet["return"] = round(stake * bet["odds"], 2)

    return {"bets": sorted(bets, key=lambda x: x["ev"], reverse=True),
            "message": "Bets optimized for maximum likelihood"}


# Frontend HTML
FRONTEND_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sports Betting Optimizer</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .game-input { margin-bottom: 15px; padding: 10px; border: 1px solid #ccc; }
        #results { margin-top: 20px; }
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
        .market-group { margin-top: 5px; }
    </style>
</head>
<body>
    <h1>Sports Betting Optimizer</h1>
    <button onclick="loadDummyData()">Load Dummy Data</button>
    <button onclick="loadBet365Data()">Load Bet365 Data</button>
    <div id="game-container">
        <div class="game-input">
            <label>Teams: <input type="text" class="teams" placeholder="Team A vs. Team B"></label><br>
            <label>Date: <input type="date" class="date"></label>
            <label>Time: <input type="time" class="time"></label><br>
            <div class="market-group">
                <h4>Match Result</h4>
                <label>Home: <input type="number" step="0.01" class="odds-home" min="1"></label>
                <label>Draw: <input type="number" step="0.01" class="odds-draw" min="1"></label>
                <label>Away: <input type="number" step="0.01" class="odds-away" min="1"></label>
            </div>
            <div class="market-group">
                <h4>Correct Score (e.g., 1-0, 0-1)</h4>
                <label>1-0: <input type="number" step="0.01" class="odds-correct_score_1-0" min="1"></label>
                <label>0-1: <input type="number" step="0.01" class="odds-correct_score_0-1" min="1"></label>
                <label>1-1: <input type="number" step="0.01" class="odds-correct_score_1-1" min="1"></label>
            </div>
            <div class="market-group">
                <h4>Both Teams to Score</h4>
                <label>Yes: <input type="number" step="0.01" class="odds-btts_yes" min="1"></label>
                <label>No: <input type="number" step="0.01" class="odds-btts_no" min="1"></label>
            </div>
            <div class="market-group">
                <h4>Goalscorers (e.g., Player Name)</h4>
                <label>Player 1: <input type="number" step="0.01" class="odds-goalscorer_player1" min="1"></label>
            </div>
            <div class="market-group">
                <h4>Corners</h4>
                <label>Over 8: <input type="number" step="0.01" class="odds-corners_over_8" min="1"></label>
                <label>Under 8: <input type="number" step="0.01" class="odds-corners_under_8" min="1"></label>
            </div>
        </div>
    </div>
    <button onclick="addGame()">Add Another Game</button><br><br>
    <label>Total Capital ($): <input type="number" id="capital" min="0" value="500"></label><br><br>
    <button onclick="calculateBets()">Calculate Bets</button>
    <div id="results"></div>

    <script>
        function addGame() {
            const container = document.getElementById('game-container');
            const newGame = document.createElement('div');
            newGame.className = 'game-input';
            newGame.innerHTML = `
                <label>Teams: <input type="text" class="teams" placeholder="Team A vs. Team B"></label><br>
                <label>Date: <input type="date" class="date"></label>
                <label>Time: <input type="time" class="time"></label><br>
                <div class="market-group">
                    <h4>Match Result</h4>
                    <label>Home: <input type="number" step="0.01" class="odds-home" min="1"></label>
                    <label>Draw: <input type="number" step="0.01" class="odds-draw" min="1"></label>
                    <label>Away: <input type="number" step="0.01" class="odds-away" min="1"></label>
                </div>
                <div class="market-group">
                    <h4>Correct Score</h4>
                    <label>1-0: <input type="number" step="0.01" class="odds-correct_score_1-0" min="1"></label>
                    <label>0-1: <input type="number" step="0.01" class="odds-correct_score_0-1" min="1"></label>
                    <label>1-1: <input type="number" step="0.01" class="odds-correct_score_1-1" min="1"></label>
                </div>
                <div class="market-group">
                    <h4>Both Teams to Score</h4>
                    <label>Yes: <input type="number" step="0.01" class="odds-btts_yes" min="1"></label>
                    <label>No: <input type="number" step="0.01" class="odds-btts_no" min="1"></label>
                </div>
                <div class="market-group">
                    <h4>Goalscorers</h4>
                    <label>Player 1: <input type="number" step="0.01" class="odds-goalscorer_player1" min="1"></label>
                </div>
                <div class="market-group">
                    <h4>Corners</h4>
                    <label>Over 8: <input type="number" step="0.01" class="odds-corners_over_8" min="1"></label>
                    <label>Under 8: <input type="number" step="0.01" class="odds-corners_under_8" min="1"></label>
                </div>
            `;
            container.appendChild(newGame);
        }

        function loadDummyData() {
            fetch('/dummy_data')
                .then(response => response.json())
                .then(data => populateForm(data));
        }

        function loadBet365Data() {
            fetch('/bet365_data')
                .then(response => response.json())
                .then(data => populateForm(data));
        }

        function populateForm(data) {
            const container = document.getElementById('game-container');
            container.innerHTML = '';
            data.games.forEach(game => {
                const div = document.createElement('div');
                div.className = 'game-input';
                div.innerHTML = `
                    <label>Teams: <input type="text" class="teams" value="${game.teams}"></label><br>
                    <label>Date: <input type="date" class="date" value="${game.date}"></label>
                    <label>Time: <input type="time" class="time" value="${game.time}"></label><br>
                    <div class="market-group">
                        <h4>Match Result</h4>
                        <label>Home: <input type="number" step="0.01" class="odds-home" value="${game.odds.home || ''}"></label>
                        <label>Draw: <input type="number" step="0.01" class="odds-draw" value="${game.odds.draw || ''}"></label>
                        <label>Away: <input type="number" step="0.01" class="odds-away" value="${game.odds.away || ''}"></label>
                    </div>
                    <div class="market-group">
                        <h4>Correct Score</h4>
                        <label>1-0: <input type="number" step="0.01" class="odds-correct_score_1-0" value="${game.odds.correct_score_1_0 || ''}"></label>
                        <label>0-1: <input type="number" step="0.01" class="odds-correct_score_0-1" value="${game.odds.correct_score_0_1 || ''}"></label>
                        <label>1-1: <input type="number" step="0.01" class="odds-correct_score_1-1" value="${game.odds.correct_score_1_1 || ''}"></label>
                    </div>
                    <div class="market-group">
                        <h4>Both Teams to Score</h4>
                        <label>Yes: <input type="number" step="0.01" class="odds-btts_yes" value="${game.odds.btts_yes || ''}"></label>
                        <label>No: <input type="number" step="0.01" class="odds-btts_no" value="${game.odds.btts_no || ''}"></label>
                    </div>
                    <div class="market-group">
                        <h4>Goalscorers</h4>
                        <label>Player 1: <input type="number" step="0.01" class="odds-goalscorer_player1" value="${game.odds.goalscorer_player1 || ''}"></label>
                    </div>
                    <div class="market-group">
                        <h4>Corners</h4>
                        <label>Over 8: <input type="number" step="0.01" class="odds-corners_over_8" value="${game.odds.corners_over_8 || ''}"></label>
                        <label>Under 8: <input type="number" step="0.01" class="odds-corners_under_8" value="${game.odds.corners_under_8 || ''}"></label>
                    </div>
                `;
                container.appendChild(div);
            });
            document.getElementById('capital').value = data.capital;
        }

        function calculateBets() {
            const games = [];
            document.querySelectorAll('.game-input').forEach(div => {
                const game = {
                    teams: div.querySelector('.teams').value,
                    date: div.querySelector('.date').value,
                    time: div.querySelector('.time').value,
                    odds: {}
                };
                const oddsFields = {
                    'home': '.odds-home',
                    'draw': '.odds-draw',
                    'away': '.odds-away',
                    'correct_score_1-0': '.odds-correct_score_1-0',
                    'correct_score_0-1': '.odds-correct_score_0-1',
                    'correct_score_1-1': '.odds-correct_score_1-1',
                    'btts_yes': '.odds-btts_yes',
                    'btts_no': '.odds-btts_no',
                    'goalscorer_player1': '.odds-goalscorer_player1',
                    'corners_over_8': '.odds-corners_over_8',
                    'corners_under_8': '.odds-corners_under_8'
                };
                for (let [market, selector] of Object.entries(oddsFields)) {
                    const value = div.querySelector(selector).value;
                    if (value) game.odds[market] = parseFloat(value);
                }
                if (game.teams && game.date && game.time && Object.keys(game.odds).length > 0) {
                    games.push(game);
                }
            });
            const capital = parseFloat(document.getElementById('capital').value);

            fetch('/calculate_bets', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ games, capital })
            })
            .then(response => response.json())
            .then(result => {
                const resultsDiv = document.getElementById('results');
                if (result.error) {
                    resultsDiv.innerHTML = `<p>Error: ${result.error}</p>`;
                    return;
                }
                let html = `<h2>Recommended Bets</h2><p>${result.message}</p>`;
                if (result.bets.length > 0) {
                    html += `
                        <table>
                            <tr><th>Game</th><th>Market</th><th>Odds</th><th>Probability</th><th>Stake ($)</th><th>Return ($)</th></tr>
                    `;
                    result.bets.forEach(bet => {
                        html += `
                            <tr>
                                <td>${bet.game}</td>
                                <td>${bet.market}</td>
                                <td>${bet.odds}</td>
                                <td>${(bet.prob * 100).toFixed(1)}%</td>
                                <td>${bet.stake}</td>
                                <td>${bet.return}</td>
                            </tr>
                        `;
                    });
                    html += '</table>';
                }
                resultsDiv.innerHTML = html;
            });
        }
    </script>
</body>
</html>
"""


# Serve frontend
@app.route('/')
def index():
    return render_template_string(FRONTEND_HTML)


# API endpoint for calculations
@app.route('/calculate_bets', methods=['POST'])
def calculate_bets():
    data = request.get_json()
    games = data.get("games", [])
    capital = data.get("capital", 0)
    if not games or capital <= 0:
        return jsonify({"error": "Invalid input"}), 400

    result = optimize_bets(games, capital)
    return jsonify(result)


# Dummy data endpoint
@app.route('/dummy_data', methods=['GET'])
def get_dummy_data():
    dummy_data = {
        "games": [
            {"teams": "Manchester United vs. Liverpool", "date": "2025-03-10", "time": "15:00",
             "odds": {"home": 2.50, "draw": 3.40, "away": 1.90, "btts_yes": 1.80, "correct_score_1-0": 8.0}},
            {"teams": "Chelsea vs. Arsenal", "date": "2025-03-10", "time": "17:30",
             "odds": {"home": 2.20, "away": 2.30, "corners_over_8": 1.95}}
        ],
        "capital": 500
    }
    return jsonify(dummy_data)


# Bet365 data endpoint (mock transformation)
@app.route('/bet365_data', methods=['GET'])
def get_bet365_data():
    api_data = fetch_bet365_odds()
    if not api_data:
        return jsonify({"error": "Failed to fetch Bet365 data"}), 500

    # Mock transformation (adjust based on actual API response)
    games = [
        {"teams": "Man Utd vs. Liverpool", "date": "2025-03-10", "time": "15:00",
         "odds": {"home": 2.60, "draw": 3.50, "away": 1.85, "btts_yes": 1.75}},
        {"teams": "Chelsea vs. Arsenal", "date": "2025-03-10", "time": "17:30",
         "odds": {"home": 2.10, "away": 2.40, "corners_over_8": 2.00}}
    ]
    return jsonify({"games": games, "capital": 500})


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)