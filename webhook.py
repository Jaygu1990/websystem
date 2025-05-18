import eventlet
eventlet.monkey_patch()
from flask import Flask 
from flask import request, jsonify, render_template,redirect, url_for
import random
from flask_socketio import SocketIO, emit
import logging
import sys
logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)
import time
import threading
from threading import Thread


app = Flask(__name__)
socketio = SocketIO(app, async_mode='eventlet', logger=True, engineio_logger=True)

queue = []
user_list = []
user_list_holder = []
game_queue = []
followers = set()
# client = TikTokLiveClient(unique_id="@tcgcardsflowcanada")
# List of Pokémon names (you can add more to the list)
# pokemon_list = ['pikachu', 'bulbasaur', 'charmander', 'squirtle', 'meowth', 'snorlax', 'psyduck', 'eevee', 'mew', 'lapras','Caterpie','Grimer']

latest_state = {
    'energy1': 0,
    'energy2': 0,
    'energy3': 0,
    'energy4': 0,
    'energy5': 0
}


print_jobs = []

pokemon_list = ['pikachu', 'bulbasaur', 'charmander', 'squirtle',    'eevee', 'mew']
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    print("Received Webhook:", data)
    
    nums = len(data['line_items'])
    
    for num in range(nums):
        if data:
            # Extract necessary information
            product_name = data['line_items'][num]['name']
            quantity = data['line_items'][num]['quantity']
            # shipping = data['shipping_lines'][num]['code'] if data['shipping_lines'] else None
            # if shipping != '[HOLD ORDER] SHIPPING NOT FREE(LIVE ONLY)':
            #     shippingoption = "Yes"
            # else:
            #     shippingoption = "No"
                
            if data['shipping_address']:
                first_name = data['shipping_address']['first_name']  # or shipping_address['first_name']
            else:
                first_name = "NA"
                
            if data['shipping_address']:
                last_name = data['shipping_address']['last_name']  # or shipping_address['last_name']
            else:
                last_name = "NA"
                
            if data['shipping_address']:
                city = data['shipping_address']['city']
            else:
                city= "NA"
                
            if data['shipping_address']:
                state = data['shipping_address']['province'] 
            else:
                state = "NA"

            customer_data = {
                "id": data["id"],
                "completed": False,
                "product_name": product_name,
                "quantity": quantity,
                "first_name": first_name,
                "last_name": last_name,
                "city": city,
                "state": state
                # "shipping": shippingoption
            }

            if product_name.lower() != "pokemon game":
                queue.append(customer_data)
                game_queue.append(customer_data)
                if product_name.lower() != "shipping" and product_name != 'Pokemon Card Scarlet & Violet Heat Wave Arena Pack sv9a (Japanese) - OPEN LIVE / Battle' and product_name != 'Pokemon Card Scarlet & Violet Battle Partners Pack sv9 (Japanese) - OPEN LIVE / Battle' and product_name != 'Pokemon Card Scarlet & Violet The Glory of Team Rocket Pack sv10 (Japanese) - OPEN LIVE / Battle':
                    print_jobs.append(customer_data)
            if product_name == 'Pokemon Card Scarlet & Violet Heat Wave Arena Pack sv9a (Japanese) - OPEN LIVE / Battle':
                user_list.append(first_name.split()[0])
            # Add to game_queue only if the product is "draw"
            # if product_name.lower() == "pokemon game":
            #     game_queue.append(customer_data)
        
    return jsonify({"status": "success"}), 200

@app.route('/add_dummy_order', methods=['POST'])
def add_order():
    # Create dummy order data
    dummy_order = {
        "id": random.randint(1000, 9999),  # Generate a random order ID
        "completed": False,
        "product_name": "Pokemon Card Scarlet & Violet Heat Wave Arena Pack sv9a (Japanese) - OPEN LIVE / Battle",
        "quantity": random.randint(1, 5),  # Random quantity between 1 and 5
        "first_name": "John",
        "last_name": "Doe",
        "city": "Vancouver",
        "state": "BC"
    }
    first_name = dummy_order['first_name']
    print_jobs.append(dummy_order)
    queue.append(dummy_order)
    game_queue.append(dummy_order)
    user_list.append(first_name.split()[0])
    
    return jsonify({"message": "Dummy order added", "order": dummy_order})


@app.route('/queue', methods=['GET'])
def get_queue():
    return render_template('queue.html', queue=queue)


@app.route('/queueforviewers', methods=['GET'])
def get_queueforviewers():
    return render_template('queueforviewers.html', queue=queue)

@app.route('/queue_data', methods=['GET'])
def queue_data():
    # Return the current count of customers in the game queue
    game_queue_count = len(game_queue)
    
    # You can return the full game queue or any data you need from it
    return jsonify({
        "game_queue_count": game_queue_count,  # For the number of customers paid for "draw"
        "queue": queue  # If you still want to send the `queue` data as well
    })



@app.route('/complete/<int:index>', methods=['POST'])
def complete_order(index):
    if 0 <= index < len(queue):
        queue[index]["completed"] = True  # Mark as completed
    return '', 204  # No content response

@app.route('/game')
def index():
    return render_template('index.html', pokemon_list=pokemon_list)




@app.route('/clear_game_queue', methods=['POST'])
def clear_game_queue():
    game_queue.clear()  # Clear the game queue
    return '', 204  # No content response


@app.route('/clear_queue', methods=['POST'])
def clear_queue():
    queue.clear()
    print_jobs.clear()
    return '', 204  # No content response


@app.route('/select_random_customers', methods=['POST'])
def select_random_customers():
    # Check if there are at least 12 customers in the game queue
    num_customers = len(game_queue)
    
    if num_customers < 6:
        # If there are fewer than 12 customers, sample as many as there are
        selected_customers = random.sample(game_queue, num_customers)
    else:
        # If there are at least 12 customers, sample 12
        selected_customers = random.sample(game_queue, 6)
    
    # Return the selected customers
    return jsonify([{
        "first_name": customer["first_name"],
        "last_name": customer["last_name"]
    } for customer in selected_customers])




# Define available Pokémon Trainer images
Trainers = [
    "/static/Pokemon_images/ash.png",
    "/static/Pokemon_images/Brock.png",
    "/static/Pokemon_images/Dawn.png",
    "/static/Pokemon_images/Gary.png",
    "/static/Pokemon_images/James.png",
    "/static/Pokemon_images/Jesse.png",
    "/static/Pokemon_images/lillie.png",
    "/static/Pokemon_images/Misty.png",
    "/static/Pokemon_images/Professor.png",
    "/static/Pokemon_images/Giovanni.png",
    "/static/Pokemon_images/Cynthia.png",
    
]

# Image paths
QUESTION_MARK_IMAGE = "/static/Pokemon_images/question.png"
POKEBALL_IMAGE = "/static/Pokemon_images/pokeball.png"
BATTLE_GROUND_IMAGE = "/static/Pokemon_images/background.png"
INITIAL_BACKGROUND = "/static/Pokemon_images/firstbackground.png"


used_images = set() 
user_index = 0

@app.route('/battle')  # Serve the battle page at this route
def battle():
    return render_template('battle.html')  # Render battle.html

@socketio.on('join_queue')
def handle_join_queue():
    global user_index  

    current_images = []
    
    # Ensure we only process if we have space in user_list_holder
    while len(user_list_holder) < 5 and user_list:
        new_text = user_list.pop(0)  # Get the next user name
        available_images = [img for img in Trainers if img not in used_images]

        if available_images:
            new_image = random.choice(available_images)  # Select a random unused image
            used_images.add(new_image)  # Mark this image as used
            
            # Assign a persistent index and increment it
            new_entry = {'index': user_index, 'name': new_text, 'image': new_image}
            user_list_holder.append(new_entry)  # Add to holder
            current_images.append(new_entry)
            user_index += 1  # Move to the next index
        else:
            break  # Stop if no available images

    # Send the updated images to the frontend
    emit('update_response', {'images': user_list_holder, 'finished': len(user_list_holder) > 5})


@app.route('/adduser', methods=['POST'])
def add_user():
    global user_list

    # Generate a random username between 1 and 100, ensuring uniqueness
    username = random.randint(1, 100)
    while username in user_list:  # Ensure uniqueness
        username = random.randint(1, 100)
    
    user_list.append(username)  # Add username to the list

    return jsonify({"message": "User added successfully.", "user_list": user_list}), 200


@app.route('/clear_battle', methods=['POST'])
def clear_battle():
    global user_index
    global user_list_holder
    global user_index
    global used_images
    global latest_state
    
    user_index = 0 # Reset index when clearing
    used_images.clear()  # Reset used images
    user_list_holder = []
    latest_state = {
        'energy1': 0,
        'energy2': 0,
        'energy3': 0,
        'energy4': 0,
        'energy5': 0
    }    
    # Emit an event to clear the images on the front end
    socketio.emit('clear_images')
    
    return jsonify({"message": "All users cleared.", "user_list": user_list_holder}), 200


@app.route('/show', methods=['POST'])
def show():    
    return jsonify({"user_list_hold": user_list_holder, "user_list": user_list}), 200


energy1 = [1, 2, 3, 4, 5] * 10
energy2 = [2, 3, 4, 5, 1] * 10
energy3 = [3, 4, 5, 1, 2] * 10
energy4 = [4, 5, 1, 2, 3] * 10
energy5 = [5, 1, 2, 3, 4] * 10


@app.route('/get-latest-state', methods=['GET'])
def get_latest_state():
    return jsonify(latest_state)

def send_numbers():
    index = 0
    while index < len(energy1):
        latest_state.update({
            'energy1': energy1[index],
            'energy2': energy2[index],
            'energy3': energy3[index],
            'energy4': energy4[index],
            'energy5': energy5[index]
        })
        socketio.emit('update_slot_machine', latest_state)
        time.sleep(0.1)  # Emit every 0.1 seconds
        index += 1
        
    energy_numbers = [1, 2, 3, 4, 5]
    random.shuffle(energy_numbers)
    # After finishing the updates, emit the final random result
    final_state = {
        'energy1': energy_numbers[0],
        'energy2': energy_numbers[1],
        'energy3': energy_numbers[2],
        'energy4': energy_numbers[3],
        'energy5': energy_numbers[4],
        'final': True
    }
    latest_state.update(final_state)

    socketio.emit('final_slot_machine', latest_state)

    
@app.route('/test', methods=['POST'])
def test():
    print(latest_state)
    return 'Slot machine triggered!', 200

@app.route('/start-slot-machine', methods=['POST'])
def start_slot_machine():
    socketio.emit('trigger_page_refresh', {'refresh': True})
    time.sleep(0.1) 
    threading.Thread(target=send_numbers).start()
    return 'Slot machine triggered!', 200




@app.route('/')
def home():
    return '''
    <html>
        <head>
            <title>TCG Cards Flow</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    text-align: center;
                    background-color: #f8f9fa;
                    padding: 50px;
                }
                h1 {
                    color: #333;
                    margin-bottom: 20px;
                }
                .image-container {
                    margin: 20px 0;
                }
                .ash-image {
                    width: 250px; /* Adjust size as needed */
                    height: auto;
                    border-radius: 10px;
                    box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.2);
                }
                .button-container {
                    margin-top: 20px;
                }
                .button {
                    background-color: #007bff;
                    color: white;
                    border: none;
                    padding: 12px 24px;
                    font-size: 18px;
                    margin: 10px;
                    cursor: pointer;
                    border-radius: 5px;
                    transition: background 0.3s;
                }
                .button:hover {
                    background-color: #0056b3;
                }
            </style>
        </head>
        <body>
            <h1>Located in Vancouver, Ship to USA & Canada</h1>
            <h1>Free pack give away every 10 mins for new followers and buyers.</h1>
            <div class="image-container">
                <img src="/static/images/ash.png" alt="Ash" class="ash-image">
            </div>
            <div class="button-container">
                <button class="button" onclick="window.location.href='/queue'">Go to Queue</button>
                <button class="button" onclick="window.location.href='/queueforviewers'">Go to Queue for viewers</button>
                <button class="button" onclick="window.location.href='/game'">Go to Game</button>
                <button class="button" onclick="window.location.href='/battle'">Go to Battle</button>
                <button class="button" onclick="window.location.href='/coupon'">Go to Coupon</button>
                <button class="button" onclick="window.location.href='/follow'">Go to Followers</button>
                <button class="button" onclick="window.location.href='/display'">Go to Display</button>
                <button class="button" onclick="window.location.href='/control'">Go to Control</button>
                <button class="button" onclick="window.location.href='/OBSqueue'">Go to OBSQueue</button>
            </div>
        </body>
    </html>
    '''

# ----------------------------------------------------
import os
import requests
import smtplib
import random
import string
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from dotenv import load_dotenv  # Import dotenv

# Load environment variables from .env file
load_dotenv()

# Shopify credentials
SHOPIFY_STORE_URL = os.getenv("SHOPIFY_STORE_URL")
API_ACCESS_TOKEN = os.getenv("API_ACCESS_TOKEN")

# Email SMTP configuration
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))  # Default to 587 if not set
EMAIL_USERNAME = os.getenv("EMAIL_USERNAME")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")



def generate_discount_code():
    """Generate a random discount code"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))




def create_shopify_discount(variant_ids):
    """Create a Shopify discount code and link it to specific product variants."""
    code = generate_discount_code()  # Generate unique discount code
    starts_at = (datetime.utcnow() + timedelta(seconds=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
    ends_at = (datetime.utcnow() + timedelta(weeks=2)).strftime("%Y-%m-%dT%H:%M:%SZ")

    headers = {
        "Content-Type": "application/json",
        "X-Shopify-Access-Token": API_ACCESS_TOKEN
    }

    # Step 1: Create Price Rule
    price_rule_data = {
        "price_rule": {
            "title": f"Discount for {code}",  # Internal name
            "value_type": "fixed_amount",
            "value": "-5.00",  # Discount amount
            "customer_selection": "all",
            "target_type": "line_item",
            "target_selection": "entitled",  # Only for entitled products
            "allocation_method": "each",
            "starts_at": starts_at,
            "ends_at": ends_at, 
            "usage_limit": 1,
            "once_per_customer": True,
            "combinable": False,
            "entitled_variant_ids": variant_ids  # Restrict to specific product variants
        }
    }

    price_rule_url = f"{SHOPIFY_STORE_URL}/admin/api/2023-10/price_rules.json"
    price_rule_response = requests.post(price_rule_url, json=price_rule_data, headers=headers)

    if price_rule_response.status_code != 201:
        print(f"❌ Failed to create price rule: {price_rule_response.status_code} {price_rule_response.text}")
        return None

    price_rule_id = price_rule_response.json()["price_rule"]["id"]

    # Step 2: Create Discount Code
    discount_code_data = {
        "discount_code": {
            "code": code,  # Actual discount code customers will use
            "price_rule_id": price_rule_id
        }
    }

    discount_code_url = f"{SHOPIFY_STORE_URL}/admin/api/2023-10/price_rules/{price_rule_id}/discount_codes.json"
    discount_code_response = requests.post(discount_code_url, json=discount_code_data, headers=headers)

    if discount_code_response.status_code == 201:
        print(f"✅ Discount code created successfully: {code}")
        return code
    else:
        print(f"❌ Failed to create discount code: {discount_code_response.status_code} {discount_code_response.text}")
        return None


def send_email(recipient, code):
    """Send the coupon code via email"""
    subject = "Your Shopify Discount Code"
    body = f"Here is your discount code: {code}\n\nUse it at checkout!"

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL_USERNAME
    msg["To"] = recipient

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_USERNAME, EMAIL_PASSWORD)
        server.sendmail(EMAIL_USERNAME, recipient, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print("Email error:", e)
        return False

@app.route("/coupon", methods=["GET", "POST"])
def generate_coupon():
    if request.method == "GET":
        return render_template("coupon.html")  # Return the form page

    email = request.form.get("email")
    if not email:
        return jsonify({"error": "Email is required"}), 400

    code = generate_discount_code()
    variant_ids = [51808417612148,51808408764788, 51808185483636, 51746827305332, 51753653207412,51806220714356,51728814866804,51728819716468,51806536827252,
                   51728820404596,51728818602356,51728815817076,51728819782004, 51728820240756, 51728821027188,51728820797812,51728819487092,51728819847540,51806224875892 ]  

    discount_id = create_shopify_discount(variant_ids)
    if not discount_id:
        return jsonify({"error": "Failed to create discount"}), 500

    if send_email(email, discount_id):
        return jsonify({"success": f"Discount code {discount_id} sent to {email}!"})
    else:
        return jsonify({"error": "Failed to send email"}), 500

# ----------------------------------------------------

# Pokémon list with probabilities
POKEMON_PROBABILITIES = {
    "pikachu.png": 0.3,    # 30%
    "charizard.png": 0.2,  # 20%
    "bulbasaur.png": 0.15, # 15%
    "squirtle.png": 0.15,  # 15%
    "gengar.png": 0.1,     # 10%
    "mewtwo.png": 0.05,    # 5%
    "eevee.png": 0.05      # 5%
}

def spin_slot():
    """Selects 3 Pokémon images based on their probabilities."""
    pokemon, weights = zip(*POKEMON_PROBABILITIES.items())
    return random.choices(pokemon, weights=weights, k=3)

@app.route("/spin", methods=["GET"])
def spin():
    results = spin_slot()
    return jsonify(result=["images/" + img for img in results])  # Return JSON, not a rendered template




@app.route("/get_print_jobs", methods=["GET"])
def get_print_jobs():
    return jsonify(print_jobs), 200



# @client.on(ConnectEvent)
# async def on_connect(_: ConnectEvent):
#     print("Connected to TikTok LIVE")

# async def on_social(event: SocialEvent) -> None:
#     if "followed" in event.base_message.display_text.default_pattern.lower():
#         user_id = event.user.id
#         nickname = event.user.nickname
        
#         if user_id not in followers:
#             followers.add(user_id)
#             print(f"\nNew follower: {nickname} (ID: {user_id})")
#             print(f"Total followers: {len(followers)}\n")

# client.add_listener(SocialEvent, on_social)


# @app.route('/follow')
# def tiktok_ui():
#     return render_template('tiktok.html')

# @app.route('/api/followers')
# def get_followers():
#     return jsonify(list(followers))

# @app.route('/api/clear', methods=['POST'])
# def clear_followers():
#     followers.clear()
#     return jsonify({'status': 'cleared'})


# names = ["Alice", "Bob", "Charlie"]

# @app.route("/wheel")
# def wheel():
#     return render_template("wheel.html", options=names)

# @app.route("/add", methods=["POST"])
# def add_name():
#     name = request.form.get("name")
#     if name and name not in names:
#         names.append(name)
#     return redirect(url_for("wheel"))

# @app.route("/edit/<old_name>", methods=["POST"])
# def edit_name(old_name):
#     new_name = request.form.get("new_name")
#     if new_name and old_name in names:
#         index = names.index(old_name)
#         names[index] = new_name
#     return redirect(url_for("wheel"))

# @app.route("/delete/<name>")
# def delete_name(name):
#     if name in names:
#         names.remove(name)
#     return redirect(url_for("wheel"))

import json

STATE_FILE = 'state.json'

DEFAULT_STATE = {
    "rounds": [
        ["1.png", "2.png", "3.png", "4.png", "5.png", "6.png", "7.png", "8.png"],
        ["question.png"] * 4,
        ["question.png"] * 2,
        ["question.png"] * 1
    ],
    "names": {
        "1.png": "Espeon",
        "2.png": "Flareon",
        "3.png": "Glaceon",
        "4.png": "Jolteon",
        "5.png": "Leafeon",
        "6.png": "Sylveon",
        "7.png": "Umbreon",
        "8.png": "Vaporeon"
    }
}


def init_state():
    randomized_round1 = DEFAULT_STATE['rounds'][0][:]
    random.shuffle(randomized_round1)
    return {
        "rounds": [
            randomized_round1,
            ["question.png"] * 4,
            ["question.png"] * 2,
            ["question.png"]
        ],
        "names": DEFAULT_STATE['names']
    }


# Initialize the state file if missing
if not os.path.exists(STATE_FILE):
    state = init_state()
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f)

def load_state():
    with open(STATE_FILE, 'r') as f:
        return json.load(f)

def save_state(state):
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f)

@app.route('/display')
def display():
    state = load_state()
    return render_template('display.html', rounds=state['rounds'], names=state['names'])


@app.route('/control', methods=['GET', 'POST'])
def control():
    state = load_state()

    if request.method == 'POST':
        if 'reset' in request.form:
            # Reset everything to default: rounds AND names
            state = DEFAULT_STATE.copy()
            save_state(state)
            return redirect(url_for('control'))

        if 'randomize' in request.form:
            # Load existing state to keep names
            old_state = load_state()
            # Create new rounds with randomized round 1 but keep old names
            randomized_round1 = old_state['rounds'][0][:]
            random.shuffle(randomized_round1)
            new_state = {
                "rounds": [
                    randomized_round1,
                    ["question.png"] * 4,
                    ["question.png"] * 2,
                    ["question.png"]
                ],
                "names": old_state.get('names', DEFAULT_STATE['names'])
            }
            save_state(new_state)
            return redirect(url_for('control'))

        # Check if the form is for updating names
        if 'update_names' in request.form:
            for img in state['names'].keys():
                new_name = request.form.get(img, "").strip()
                if new_name:
                    state['names'][img] = new_name
            save_state(state)
            return redirect(url_for('control'))

        # Normal update winner logic (your existing code)
        try:
            round_index = int(request.form['round'])
            match_index = int(request.form['match'])
            winner_raw = request.form['winner'].strip()
        except (KeyError, ValueError):
            return redirect(url_for('control'))

        winner = winner_raw if winner_raw.endswith('.png') else f"{winner_raw}.png"

        if round_index + 1 < len(state['rounds']):
            if 0 <= match_index < len(state['rounds'][round_index + 1]):
                state['rounds'][round_index + 1][match_index] = winner
                save_state(state)

        return redirect(url_for('control'))

    return render_template('control.html', rounds=state['rounds'], names=state['names'])

@app.route('/display-data')
def display_data():
    state = load_state()
    return jsonify({
        'rounds': state['rounds'],
        'names': state['names']
    })


@app.route('/OBSqueue')
def obs_queue():
    return render_template('OBSqueue.html', queue=queue)

if __name__ == '__main__':
 
    import eventlet
    import eventlet.wsgi
    eventlet.monkey_patch()  # Critical for eventlet to handle concurrency properly
    
    # Use `socketio.run()` with `eventlet` explicitly specified
    socketio.run(app, host='0.0.0.0', port=5000)

