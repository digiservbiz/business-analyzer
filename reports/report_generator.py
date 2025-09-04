import csv

def generate_report(businesses):
    """Generates a CSV report of businesses."""
    filepath = "./business_report.csv"
    with open(filepath, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["Name", "Address", "Website"])
        writer.writerows(businesses)
    return filepath
