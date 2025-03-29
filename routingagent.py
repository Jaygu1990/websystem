import time
import requests
import win32print
import win32ui

FLASK_SERVER_URL = "https://websystem-kkmd.onrender.com/"
print_jobs = []  # Store processed jobs to avoid duplicates

def print_text(job):
    """ Prints the customer details except 'id' and 'completed'. """
    printer_name = "M220 Printer"  # Set your printer manually
    hprinter = win32print.OpenPrinter(printer_name)
    hprinter_dc = win32ui.CreateDC()
    hprinter_dc.CreatePrinterDC(printer_name)
    
    hprinter_dc.StartDoc("Cloud Print Job")
    hprinter_dc.StartPage()
    
    # Filter out 'id' and 'completed'
    filtered_data = {k: v for k, v in job.items() if k not in ["id", "completed"]}
    
    y_offset = 100  # Start position for printing
    for key, value in filtered_data.items():
        hprinter_dc.TextOut(100, y_offset, f"{key}: {value}")  # Print each field
        y_offset += 30  # Move down for next line
    
    hprinter_dc.EndPage()
    hprinter_dc.EndDoc()
    hprinter_dc.DeleteDC()

def main():
    """ Continuously checks for print jobs. """
    while True:
        try:
            response = requests.get(f"{FLASK_SERVER_URL}/get_print_jobs")
            
            if response.status_code == 200:
                jobs = response.json()
                
                # Find new jobs
                new_jobs = [job for job in jobs if job not in print_jobs]
                
                for job in new_jobs:
                    print_text(job)  # Print new job
                    print_jobs.append(job)  # Mark as printed

            # Wait before checking again (e.g., 10 seconds)
            time.sleep(10)

        except Exception as e:
            print(f"Error: {e}")
            time.sleep(30)  # Wait longer in case of errors

if __name__ == "__main__":
    main()

