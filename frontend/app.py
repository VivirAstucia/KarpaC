import chess
import chess.svg
from flask import Flask, request, jsonify, render_template
from flask_socketio import SocketIO

app = Flask(__name__)
socketio = SocketIO(app)

current_board = chess.Board()
move_history = []

@app.route('/api/move', methods=['POST'])
def receiveMove():
    global current_board, move_history

    data = request.get_json()
    if not data or 'move' not in data:
        return jsonify({"error": "Missing 'move' in JSON payload"}), 400

    move_uci = data['move']

    try:
        move = chess.Move.from_uci(move_uci)
        if move in current_board.legal_moves:
            current_board.push(move)
            move_history.append(move_uci)
            
            new_svg = chess.svg.board(board=current_board, size=400)
            socketio.emit('board_update', {
                'svg': new_svg,
                'move': move_uci
            })
            
            return jsonify({
                "status": "success",
                "move_received": move_uci,
                "new_fen": current_board.fen()
            })
        else:
            return jsonify({"error": "Illegal move"}), 400
    except ValueError:
        return jsonify({"error": "Invalid UCI move format"}), 400


@app.route('/')
def index():
    board_svg = chess.svg.board(board=current_board, size=400)
    return render_template('index.html', key=board_svg, moves=move_history)

@app.route('/api/reset', methods=['POST'])
def reset_board():
    global current_board, move_history
    current_board = chess.Board()
    move_history = []

    new_svg = chess.svg.board(board=current_board, size=400)
    socketio.emit('board_update', {
        'svg': new_svg,
        'move': 'RESET'
    })
    
    return jsonify({"status": "game reset"})

if __name__ == '__main__':
    print("Starting flask server...")
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)