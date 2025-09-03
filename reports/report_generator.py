def generate_report(business_name, analysis):
    report = f"{business_name} - Online Presence Report\n"
    for k, v in analysis.items():
        report += f"{k}: {v}\n"
    filepath = f"./data/{business_name.replace(' ', '_')}_report.txt"
    with open(filepath, 'w') as f:
        f.write(report)
    return filepath
