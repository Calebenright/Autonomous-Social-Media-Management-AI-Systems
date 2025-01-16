import csv
from google.cloud import firestore

# Initialize Firestore client
db = firestore.Client(project='feed-ai-c379d')


def create_csv():
    # Get user emails from Firestore collection
    users_ref = db.collection(u'users')
    lead_ref = db.collection(u'service')
    lead_docs = lead_ref.stream()
    users_docs = users_ref.stream()

    csv_data = []

    for lead in lead_docs:
        lead_data = lead.to_dict()
        email = lead_data.get('email')
        business_name = lead_data.get('business_name') or lead_data.get('businessName')
        business_description = lead_data.get('business_description') or lead_data.get('message')

        # If business_description is None, check in users collection
        if not business_description or business_description=='':
            for user in users_docs:
                user_data = user.to_dict()
                if user_data.get('email') == email:
                    business_description = user_data.get('business_description')
                    if not business_name:
                        business_name = user_data.get('business_name')

        # Append to CSV data if email exists
        if email and business_name and business_description:
            csv_data.append([email, business_name, business_description])

    # Write data to a CSV file
    with open('business_data.csv', mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['Email', 'Business Name', 'Business Description'])  # CSV header
        writer.writerows(csv_data)

    print("CSV file created successfully!")

if __name__ == '__main__':
    create_csv()