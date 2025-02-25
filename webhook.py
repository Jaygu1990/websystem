import eventlet
eventlet.monkey_patch()
from flask import Flask 
from flask import request, jsonify, render_template
import random
from flask_socketio import SocketIO, emit

app = Flask(__name__)

queue = []
user_list = []
user_list_holder = []
game_queue = []
# List of Pokémon names (you can add more to the list)
# pokemon_list = ['pikachu', 'bulbasaur', 'charmander', 'squirtle', 'meowth', 'snorlax', 'psyduck', 'eevee', 'mew', 'lapras','Caterpie','Grimer']

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
            if product_name == 'Pokemon Card Scarlet & Violet Battle Partners Pack sv9 (Japanese) - OPEN LIVE / Battle':
                user_list.append(first_name.split()[0])
            # Add to game_queue only if the product is "draw"
            # if product_name.lower() == "pokemon game":
            #     game_queue.append(customer_data)
        
    return jsonify({"status": "success"}), 200

@app.route('/queue', methods=['GET'])
def get_queue():
    return render_template('queue.html', queue=queue)

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
    queue.clear()  # Clear the game queue
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



socketio = SocketIO(app, async_mode='eventlet') 
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
    while len(user_list_holder) < 3 and user_list:
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
    emit('update_response', {'images': user_list_holder, 'finished': len(user_list_holder) > 3})


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
    
    user_index = 0 # Reset index when clearing
    used_images.clear()  # Reset used images
    user_list_holder = []
    
    # Emit an event to clear the images on the front end
    socketio.emit('clear_images')
    
    return jsonify({"message": "All users cleared.", "user_list": user_list_holder}), 200


@app.route('/show', methods=['POST'])
def show():    
    return jsonify({"user_list_hold": user_list_holder, "user_list": user_list}), 200



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
            <h1>Today's New Products: English 151, Chinese 151, and Chinese Gemstone box.</h1>
            <h1>35 CAD OPEN battle partners packs until AR or better is still on.</h1>

            <div class="image-container">
                <img src="/static/images/ash.png" alt="Ash" class="ash-image">
            </div>
            <div class="button-container">
                <button class="button" onclick="window.location.href='/queue'">Go to Queue</button>
                <button class="button" onclick="window.location.href='/game'">Go to Game</button>
                <button class="button" onclick="window.location.href='/battle'">Go to Battle</button>
            </div>
        </body>
    </html>
    '''





if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)

