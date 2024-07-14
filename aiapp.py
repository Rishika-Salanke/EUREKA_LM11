import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import OneHotEncoder
from twilio.rest import Client

# Data preparation
data = pd.DataFrame({
    "Customer Phone Number":["","",""]
    "Order Status": ["","",""],
    "Order ID": ["","",""],
    "Order Date": ["","",""],
    "Order Time": ["","",""]
})

data['timestamp'] = data['Order Date'] + ' ' + data['Order Time']
data['timestamp'] = pd.to_datetime(data['timestamp'], format='%Y-%m-%d %I:%M %p')
data = data.drop(columns=['Order Date', 'Order Time'])
data = data[['Order ID', 'Customer Phone Number', 'Order Status', 'timestamp']].dropna()
data['timestamp'] = pd.to_datetime(data['timestamp'])
data['order_hour'] = data['timestamp'].dt.hour
data['order_day'] = data['timestamp'].dt.dayofweek
data['send_notification'] = data['Order Status'].apply(lambda x: 1 if x == 'Shipped' else 0)

# Prepare features and labels
X = data[['order_hour', 'order_day']]
y = data['send_notification']

# One-hot encode the categorical feature
encoder = OneHotEncoder()
X_encoded = encoder.fit_transform(X).toarray()

# Split the data
X_train, X_test, y_train, y_test = train_test_split(X_encoded, y, test_size=0.2, random_state=42)

# Train the model
model = LogisticRegression()
model.fit(X_train, y_train)

# Evaluate the model (optional)
accuracy = model.score(X_test, y_test)
print(f'Model accuracy: {accuracy}')

# Twilio configuration
account_sid = 'ACfd67d965f8446c166c89cbc263ced2b0'
auth_token = 'e2903de22de36b060c3072efe49f88d1'
twilio_phone_number = '+17624222411'
client = Client(account_sid, auth_token)

def send_sms(to, message):
    try:
        message = client.messages.create(
            body=message,
            from_=twilio_phone_number,
            to=to
        )
        print(f"Message sent to {to}: {message.sid}")
    except Exception as e:
        print(f"Failed to send message to {to}: {e}")

# Sending messages based on order status
for index, row in data.iterrows():
    try:
        order_hour = row['order_hour']
        order_day = row['order_day']
        order_status = row['Order Status']
        order_id = row['Order ID']
        phone_number = row['Customer Phone Number']

        print(f"Processing order with hour: {order_hour}, day: {order_day}")

        if order_status == 'Shipped':
            send_sms(phone_number, f"Your order {order_id} has been shipped!")
        elif order_status == 'Delivered':
            send_sms(phone_number, f"Your order {order_id} has been delivered!")
        elif order_status == 'Pending':
            send_sms(phone_number, f"Your order {order_id} is pending!")
        elif order_status == 'Cancelled':
            send_sms(phone_number, f"Your order {order_id} has been cancelled!")
    except KeyError as e:
        print(f"Missing key in row {index}: {e}")
    except Exception as e:
        print(f"Error processing row {index}: {e}")
