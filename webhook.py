from flask import Flask, request, jsonify, render_template
import random


app = Flask(__name__)

queue = []

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
            # Add to game_queue only if the product is "draw"
            if product_name.lower() == "pokemon game":
                game_queue.append(customer_data)
        
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
            <h1>Free pack give away every 10 mins for new followers and buyers</h1>
            <h1>Free Iono's Kilowattrel AR 104/100 give away to one buyer in the end of stream</h1>
            <div class="image-container">
                <img src="/static/images/ash.png" alt="Ash" class="ash-image">
            </div>
            <div class="button-container">
                <button class="button" onclick="window.location.href='/queue'">Go to Queue</button>
                <button class="button" onclick="window.location.href='/game'">Go to Game</button>
            </div>
        </body>
    </html>
    '''





if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)

