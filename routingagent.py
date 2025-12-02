import time
import requests
import win32print
import win32ui

FLASK_SERVER_URL = "http://websystem-kkmd.onrender.com//"
print_jobs = []  # Store processed jobs to avoid duplicates

def print_text(customer_data):
    """ Prints the selected customer details: 'first_name', 'last_name', 'quantity', 'product_name', 'city', 'state', wrapping long text. """
    printer_name = "M220 Printer"  # Set your printer manually
    hprinter = win32print.OpenPrinter(printer_name)
    hprinter_dc = win32ui.CreateDC()
    hprinter_dc.CreatePrinterDC(printer_name)
    
    hprinter_dc.StartDoc("Cloud Print Job")
    hprinter_dc.StartPage()
    
    # Extract selected fields from the customer data
    order_id     = str(customer_data.get("id", "N/A"))
    first_name   = str(customer_data.get("first_name", "N/A"))
    last_name    = str(customer_data.get("last_name", "N/A"))
    quantity     = str(customer_data.get("quantity", "N/A"))
    product_name = str(customer_data.get("product_name", "N/A"))
    city         = str(customer_data.get("city", "N/A"))
    state        = str(customer_data.get("state", "N/A"))
    
    # Prepare the order details to print
    order_details = [
        f"Order ID: {order_id}",
        f"First Name: {first_name}",
        f"Last Name: {last_name}",
        f"Quantity: {quantity}",
        f"Product: {product_name}",
        f"City: {city}",
        f"State: {state}",
    ]
    
    y_offset = 100  # Start position for printing
    max_line_length = 20  # Maximum number of characters per line before wrapping
    
    def wrap_text(text, max_length):
        """ Wraps the text to fit the specified max length. """
        words = text.split(" ")
        lines = []
        current_line = ""
        
        for word in words:
            # Check if adding the word exceeds max length
            if len(current_line + " " + word) <= max_length:
                current_line += " " + word if current_line else word
            else:
                lines.append(current_line)
                current_line = word
        
        # Add any remaining line
        if current_line:
            lines.append(current_line)
        
        return lines
    
    # Print each detail, wrapping long lines
    for detail in order_details:
        
        # ✅ If it's the first line (Order ID), reset y
        if detail.startswith("Order ID:"):
            y_offset = 100
        
        # Wrap the text if it's too long
        wrapped_lines = wrap_text(detail, max_line_length)
        
        # Print each wrapped line
        for line in wrapped_lines:
            hprinter_dc.TextOut(40, y_offset, line)
            y_offset += 30  # Move down for next line
    
    hprinter_dc.EndPage()
    hprinter_dc.EndDoc()
    hprinter_dc.DeleteDC()

def main():
    """ Continuously checks for print jobs. """
    while True:
        try:
            response = requests.get(f"{FLASK_SERVER_URL}/get_print_jobs")
            print("get response",response)
            if response.status_code == 200:
                jobs = response.json()
                print("positive response")
                # Find new jobs
                new_jobs = [job for job in jobs if job not in print_jobs]
                print(new_jobs)
                for job in new_jobs:
                    completed = job["completed"]
                    if completed == False:
                        print_text(job)  
                        print_jobs.append(job)  # Mark as printed

            # Wait before checking again (e.g., 10 seconds)
            time.sleep(10)

        except Exception as e:
            print(f"Error: {e}")
            time.sleep(30)  # Wait longer in case of errors

if __name__ == "__main__":
    main()

