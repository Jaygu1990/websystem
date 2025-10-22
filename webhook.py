import eventlet
eventlet.monkey_patch()
from flask import Flask 
from flask import request, jsonify, render_template,redirect, url_for,send_from_directory, render_template_string,flash
import random
from flask_socketio import SocketIO, emit
import logging
import sys
logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)
import time
import threading
from threading import Thread
from random import shuffle
from pathlib import Path
from werkzeug.utils import secure_filename
import secrets  # Add this import
app = Flask(__name__)
app.secret_key = secrets.token_hex(32)  # Add this line - it's REQUIRED for flash() to work
socketio = SocketIO(app, async_mode='eventlet', logger=True, engineio_logger=True)





queue = []
user_list = []
user_list_holder = []
game_queue = []
followers = set()
preorder = []
count=0
count2=0

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
    global count
    global count2
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
                if product_name.lower() != "shipping" and product_name != 'Pokemon Card Scarlet & Violet Heat Wave Arena Pack sv9a (Japanese) - OPEN LIVE / Battle' and product_name != 'Pokemon Card Scarlet & Violet Battle Partners Pack sv9 (Japanese) - OPEN LIVE / Battle' and product_name != 'Pokemon Card Scarlet & Violet The Glory of Team Rocket Pack sv10 (Japanese) - OPEN LIVE / Battle' and product_name != "Pokémon Champions (Japanese) - OPEN LIVE / Round 1" and product_name != "Pokémon Champions (Japanese) - OPEN LIVE / Round 2" and product_name != "Pokémon Champions (Japanese) - OPEN LIVE / Round 3" and product_name != "Pokémon Champions (Japanese) - OPEN LIVE / Round 4":
                    print_jobs.append(customer_data)
                if product_name == "Chinese 151 Surprise Slim Sealed Booster Pack V3 (Chinese) - OPEN LIVE":
                    count+=quantity   
                if product_name == "SV8a Terastal Festival Booster Sealed Pack(Japanese) - OPEN LIVE":
                    count2+=quantity    
            if product_name == 'Pokemon Card Scarlet & Violet Heat Wave Arena Pack sv9a (Japanese) - OPEN LIVE / Battle':
                user_list.append(first_name.split()[0])
            if product_name == "Pokemon Card TCG S-Chinese Horizons Gemstone Booster Box V2 (Chinese) - PRE ORDER":
                preorder.append(customer_data)

                          
            # Add to game_queue only if the product is "draw"
            # if product_name.lower() == "pokemon game":
            #     game_queue.append(customer_data)
        
    return jsonify({"status": "success"}), 200

@app.route('/add_dummy_order', methods=['POST'])
def add_order():
    global count
    # Create dummy order data
    dummy_order = {
        "id": random.randint(1000, 9999),  # Generate a random order ID
        "completed": False,
        "product_name": "Pokemon Card Chinese 151 Surprise Slim Sealed Booster Pack V3 (Chinese) - OPEN LIVE",
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
    preorder.append(dummy_order)
    count+=dummy_order['quantity']
    
    return jsonify({"message": "Dummy order added", "order": dummy_order})


@app.route('/queue', methods=['GET'])
def get_queue():
    return render_template('queue.html', queue=queue)


@app.route('/queueforviewers', methods=['GET'])
def get_queueforviewers():
    return render_template('queueforviewers.html', queue=queue)

@app.route('/count', methods=['GET'])
def get_count():
    return render_template('count.html', queue=queue)

@app.route('/count2', methods=['GET'])
def get_count2():
    return render_template('count2.html', queue=queue)

@app.route('/queue_data', methods=['GET'])
def queue_data():
    # Return the current count of customers in the game queue
    game_queue_count = len(game_queue)
    
    # You can return the full game queue or any data you need from it
    return jsonify({
        "game_queue_count": game_queue_count,  # For the number of customers paid for "draw"
        "queue": queue,  # If you still want to send the `queue` data as well
    })

@app.route('/preorder', methods=['GET'])
def preorderqueue():
    return jsonify({
        "preorder":preorder
    })

@app.route('/pull_count', methods=['GET'])
def pull_count():
    return jsonify({
        "count":count
    })

@app.route('/pull_count2', methods=['GET'])
def pull_count2():
    return jsonify({
        "count":count2
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

@app.route('/clear_preorderqueue', methods=['POST'])
def preorderclear_queue():
    preorder.clear()
    return '', 204  

@app.route('/minus_count', methods=['POST'])
def minus_count():
    global count
    count-=1
    return '', 204  


@app.route('/add_count', methods=['POST'])
def add_count():
    global count
    count+=1
    return '', 204  

@app.route('/minus_count2', methods=['POST'])
def minus_count2():
    global count2
    count2-=1
    return '', 204  


@app.route('/add_count2', methods=['POST'])
def add_count2():
    global count2
    count2+=1
    return '', 204  



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
            <h1>TCG Cards Flow Internal Control System</h1>
          
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
                <button class="button" onclick="window.location.href='/music'">Go to Sound</button>
                <button class="button" onclick="window.location.href='/flipgame'">Go to Flip</button>
                <button class="button" onclick="window.location.href='/count'">Go to Count</button>
                <button class="button" onclick="window.location.href='/count2'">Go to Count 2</button>
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

@app.route('/gacha', methods=['GET'])
def gacha():
    return render_template('gacha.html')



@app.route('/music')
def music_player():
    return render_template('music.html')


flip_state = {
    'numbers': [i+1 for i in range(30)],  # Fixed order 1-30
    'images': [],                         # Will be initialized when needed
    'flipped': [False]*30                 # All start face down
}

def initialize_state():
    """Initialize the game state with shuffled images"""
    image_indices = list(range(30))  # Changed to 30
    shuffle(image_indices)
    
    flip_state['images'] = image_indices
    flip_state['flipped'] = [False]*30  # Changed to 30
    return flip_state

def flip_load_state():
    """Load current state, initializing if needed"""
    if not flip_state['images']:
        initialize_state()
    return flip_state

@app.route('/flipgame')
def flip_game():
    """Serve the game page"""
    return render_template('flip.html')

@app.route('/flipgame2')
def flip_game2():
    """Serve the game page"""
    return render_template('flip2.html')

@app.route('/flipgame3')
def flip_game3():
    """Serve the game page"""
    return render_template('flip3.html')

@app.route('/flipgame4')
def flip_game4():
    """Serve the game page"""
    return render_template('flip4.html')



# ==================================== Card Show Game
@app.route('/flipgame5')
def flip_game5():
    """Serve the game page"""
    return render_template('flip5.html')

POKEBALL_STATE_FILE = Path("pokeball_prizes.json")
POKEBALL_CONFIG_FILE = Path("pokeball_config.json")

# ---- Config with a "trigger" to gate id=1 until last 10 non-bonus draws ----
DEFAULT_CONFIG = {
    # When True: id=1 is excluded from draws until non-bonus remaining <= 10
    "gate_id1_last10": True
}

def config_load():
    if POKEBALL_CONFIG_FILE.exists():
        return json.loads(POKEBALL_CONFIG_FILE.read_text(encoding="utf-8"))
    POKEBALL_CONFIG_FILE.write_text(json.dumps(DEFAULT_CONFIG, indent=2), encoding="utf-8")
    return DEFAULT_CONFIG.copy()

def config_save(cfg):
    POKEBALL_CONFIG_FILE.write_text(json.dumps(cfg, indent=2), encoding="utf-8")

# Optional: endpoints to view/update the trigger
@app.route("/api/pokeball_config", methods=["GET", "POST"])
def pokeball_config():
    if request.method == "GET":
        return jsonify(config_load())
    # POST: accept {"gate_id1_last10": true/false}
    try:
        body = request.get_json(force=True, silent=True) or {}
        cfg = config_load()
        if "gate_id1_last10" in body:
            cfg["gate_id1_last10"] = bool(body["gate_id1_last10"])
        config_save(cfg)
        return jsonify(cfg)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# ---- Prize state ----
DEFAULT_PRIZES = [
    {"id": 1,  "name": "Prize 1",  "img": "cardshow/pokeball_p1.png",  "count": 1},
    {"id": 2,  "name": "Prize 2",  "img": "cardshow/pokeball_p2.png",  "count": 1},
    {"id": 3,  "name": "Prize 3",  "img": "cardshow/pokeball_p3.png",  "count": 1},
    {"id": 4,  "name": "Prize 4",  "img": "cardshow/pokeball_p4.png",  "count": 1},
    {"id": 5,  "name": "Prize 5",  "img": "cardshow/pokeball_p5.png",  "count": 1},
    {"id": 6,  "name": "Prize 6",  "img": "cardshow/pokeball_p6.png",  "count": 15},
    {"id": 7,  "name": "Prize 7",  "img": "cardshow/pokeball_p7.png",  "count": 6},
    {"id": 8,  "name": "Prize 8",  "img": "cardshow/pokeball_p8.png",  "count": 6},
    {"id": 9,  "name": "Prize 9",  "img": "cardshow/pokeball_p9.png",  "count": 4},
    {"id": 10, "name": "Prize 10", "img": "cardshow/pokeball_p10.png", "count": 4},
    {"id": 11, "name": "Prize 11", "img": "cardshow/pokeball_p11.png", "count": 4},
    {"id": 12, "name": "Prize 12", "img": "cardshow/pokeball_p12.png", "count": 4},
    {"id": 13, "name": "Prize 13", "img": "cardshow/pokeball_p13.png", "count": 2},
    {"id": 14, "name": "BONUS!",   "img": "cardshow/bonus.png",        "count": 30},
]

def pokeball_load():
    if POKEBALL_STATE_FILE.exists():
        return json.loads(POKEBALL_STATE_FILE.read_text(encoding="utf-8"))
    data = {"prizes": DEFAULT_PRIZES}
    POKEBALL_STATE_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return data

def pokeball_save(data):
    POKEBALL_STATE_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")

def pokeball_total(prizes):
    return sum(p["count"] for p in prizes)

def non_bonus_total(prizes):
    """Total remaining draws excluding BONUS (id 14)."""
    return sum(p["count"] for p in prizes if p["id"] != 14)

@app.route("/api/pokeball_state")
def pokeball_state():
    data = pokeball_load()
    return jsonify({"prizes": data["prizes"], "total": pokeball_total(data["prizes"])})

@app.route("/api/pokeball_draw", methods=["POST"])
def pokeball_draw():
    data = pokeball_load()
    prizes = data["prizes"]
    cfg = config_load()

    pool = pokeball_total(prizes)
    if pool <= 0:
        return jsonify({"error": "Pool is empty"}), 400

    # Determine if id=1 should be gated
    nb_left = non_bonus_total(prizes)  # non-bonus remaining
    gate_id1 = bool(cfg.get("gate_id1_last10", True)) and (nb_left > 10)

    # Build the bag with optional gate for id=1
    bag = []
    for p in prizes:
        count = p["count"]
        if count <= 0:
            continue
        # If gating is active AND this is id=1 AND we are NOT in last 10 non-bonus, exclude it
        if gate_id1 and p["id"] == 1:
            continue
        bag.extend([p["id"]] * count)

    # Safety check: if gating accidentally removed all non-zero entries (shouldn't happen often),
    # fall back to all available prizes to avoid an empty bag edge case.
    if not bag:
        for p in prizes:
            bag.extend([p["id"]] * max(0, p["count"]))

        if not bag:
            return jsonify({"error": "Pool is empty"}), 400

    chosen_id = random.choice(bag)

    # Decrement the chosen prize
    chosen = None
    for p in prizes:
        if p["id"] == chosen_id:
            p["count"] -= 1
            chosen = p
            break

    pokeball_save(data)
    return jsonify({"chosen": chosen, "prizes": prizes, "total": pokeball_total(prizes)})

@app.route("/api/pokeball_reset", methods=["POST"])
def pokeball_reset():
    POKEBALL_STATE_FILE.unlink(missing_ok=True)
    pokeball_save({"prizes": DEFAULT_PRIZES})
    return jsonify({"ok": True})


# ====================================

@app.route('/get-state')
def flip_get_state():
    """Get current game state"""
    return jsonify(flip_load_state())

@app.route('/reset', methods=['POST'])
def flip_reset():
    """Reset the game state"""
    return jsonify(initialize_state())

@app.route('/flip-card', methods=['POST'])
def flip_card():
    """Handle card flip action"""
    card_index = request.json.get('index')
    
    # Changed the validation to check for 30 cards instead of 27
    if card_index is None or not 0 <= card_index < 30:
        return jsonify({'success': False, 'error': 'Invalid card index'}), 400
    
    state = flip_load_state()
    state['flipped'][card_index] = not state['flipped'][card_index]
    
    return jsonify({'success': True, 'state': state})  # Fixed the return statement

# Configuration
UPLOAD_FOLDER = 'static/images'
ALLOWED_EXTENSIONS = {'png'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/cards', methods=['GET', 'POST'])
def manage_cards():
    if request.method == 'POST':
        try:
            card_number = request.form.get('card_number')
            
            if not card_number or not card_number.isdigit():
                flash('Invalid card number', 'error')
                return redirect(url_for('manage_cards'))
            
            card_number = int(card_number)
            if card_number < 1 or card_number > 30:
                flash('Card number must be between 1 and 30', 'error')
                return redirect(url_for('manage_cards'))
            
            if 'card_image' not in request.files:
                flash('No file selected', 'error')
                return redirect(url_for('manage_cards'))
            
            file = request.files['card_image']
            
            if file.filename == '':
                flash('No file selected', 'error')
                return redirect(url_for('manage_cards'))
            
            if file and allowed_file(file.filename):
                filename = f'card{card_number}.png'
                filename = secure_filename(filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                
                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                file.save(file_path)
                flash(f'Successfully replaced card{card_number}.png', 'success')
            else:
                flash('Only PNG files are allowed', 'error')
                
        except Exception as e:
            flash(f'Error replacing image: {str(e)}', 'error')
        
        return redirect(url_for('manage_cards'))
    
    return render_template('cards.html')



if __name__ == '__main__':
 
    import eventlet
    import eventlet.wsgi
    eventlet.monkey_patch()  # Critical for eventlet to handle concurrency properly
    
    # Use `socketio.run()` with `eventlet` explicitly specified
    socketio.run(app, host='0.0.0.0', port=5000)

