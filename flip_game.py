import os
import json
import random
from flask import Blueprint, jsonify, request, render_template, abort
from functools import wraps

# Initialize Blueprint
flip_bp = Blueprint('flip', __name__, template_folder='templates')

# Configuration
FLIP_STATE_FILE = os.path.join(os.path.dirname(__file__), 'game_state.json')
CARD_COUNT = 27  # Makes it easy to change card count later

# Error Handling Decorator
def handle_errors(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except FileNotFoundError:
            return jsonify({'error': 'State file not found'}), 404
        except json.JSONDecodeError:
            return jsonify({'error': 'Invalid state file'}), 500
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    return wrapper

# State Management Functions
def initialize_state():
    """Create a fresh game state with shuffled cards"""
    image_indices = list(range(CARD_COUNT))
    random.shuffle(image_indices)
    return {
        'numbers': [i+1 for i in range(CARD_COUNT)],
        'images': image_indices,
        'flipped': [False] * CARD_COUNT,
        'version': 1.0  # For future compatibility
    }

@handle_errors
def flip_load_state():
    """Load game state from file, create new if missing"""
    if os.path.exists(FLIP_STATE_FILE):
        with open(FLIP_STATE_FILE, 'r') as f:
            state = json.load(f)
            # Validate loaded state
            if all(key in state for key in ['numbers', 'images', 'flipped']):
                return state
    return initialize_state()

@handle_errors
def flip_save_state(state):
    """Save game state to file"""
    with open(FLIP_STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

# Routes
@flip_bp.route('/')
def flip_game():
    """Render the main flip game interface"""
    return render_template('flip.html')

@flip_bp.route('/state', methods=['GET'])
@handle_errors
def get_state():
    """Get current game state (API endpoint)"""
    return jsonify(flip_load_state())

@flip_bp.route('/reset', methods=['POST'])
@handle_errors
def reset_game():
    """Reset game to initial state (API endpoint)"""
    new_state = initialize_state()
    flip_save_state(new_state)
    return jsonify({
        'success': True,
        'state': new_state
    })

@flip_bp.route('/card/<int:card_id>', methods=['POST'])
@handle_errors
def flip_card(card_id):
    """Flip a specific card (API endpoint)"""
    if card_id < 0 or card_id >= CARD_COUNT:
        abort(400, description="Invalid card ID")
    
    state = flip_load_state()
    state['flipped'][card_id] = not state['flipped'][card_id]
    flip_save_state(state)
    
    return jsonify({
        'success': True,
        'card_id': card_id,
        'is_flipped': state['flipped'][card_id]
    })

@flip_bp.route('/stats', methods=['GET'])
@handle_errors
def game_stats():
    """Get game statistics (API endpoint)"""
    state = flip_load_state()
    flipped_count = sum(state['flipped'])
    return jsonify({
        'total_cards': CARD_COUNT,
        'flipped_cards': flipped_count,
        'remaining_cards': CARD_COUNT - flipped_count
    })