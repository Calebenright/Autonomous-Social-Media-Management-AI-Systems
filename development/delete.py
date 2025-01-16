import firebase_admin
from firebase_admin import auth, credentials, firestore

# Initialize Firebase app
cred = credentials.Certificate('firebase-adminsdk.json')
firebase_admin.initialize_app(cred)

db = firestore.client()

def delete_user_by_email_and_id(email, user_id):
    try:
        try:
            # Reference to the service collection
            db.collection('service').document(email).delete()
        except:
            print(f"No service document found.")



        try:
            # Delete the user document in the users collection
            db.collection('users').document(user_id).delete()
        except:
            print(f"No user document found.")

        
        auth.delete_user(user_id)
        
        print(f"User with email {email} and user ID {user_id} and their associated data have been deleted.")
            
    except Exception as e:
        print(f"An error occurred: {e}")

# Example usage
delete_user_by_email_and_id('enrighttube@gmail.com', 'xBtzXlbtMDfs1QO4iob8o6y2LGi2')