import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import OneHotEncoder
from twilio.rest import Client

# Data preparation
data = pd.DataFrame({
    "Customer Phone Number": ["+917676510631", "+919108417317", "+919113522364", "+918088132695", "+918951829180",
                              "+918197875306", "+918310676403", "+919019825033", "+919844204229", "+9740129274",
                              "+919901945975", "+917204748709", "+919113522364", "+916362416754", "+918088132695",
                              "+919481585385", "+91973980545", "+918088113211", "+917019022393", "+919739280545",
                              "+916366140884", "+919880063587", "+916360290545", "+918277636778", "+918453014728",
                              "+919483025105", "+916360496194", "+919164200431", "+8217697722", "+919535009898", "+917899666129"],
    "Order Status": ["Shipped", "Delivered", "Pending", "Cancelled", "Shipped",
                     "Delivered", "Pending", "Cancelled", "Shipped", "Delivered",
                     "Pending", "Cancelled", "Shipped", "Delivered", "Pending",
                     "Cancelled", "Shipped", "Delivered", "Pending", "Cancelled",
                     "Shipped", "Delivered", "Pending", "Cancelled", "Shipped",
                     "Delivered", "Pending", "Cancelled", "Shipped", "Delivered","Shipped"],
    "Order ID": ["01", "02", "03", "04", "05", "06", "07",
                 "08", "09", "10", "11", "12", "13", "14",
                 "15", "16", "17", "18", "19", "20", "21",
                 "22", "23", "24", "25", "26", "27", "28",
                 "29", "30","31"],
    "Order Date": ["2024-07-13", "2024-07-12", "2024-07-11", "2024-07-10", "2024-07-09",
                   "2024-07-08", "2024-07-07", "2024-07-06", "2024-07-05", "2024-07-04",
                   "2024-07-03", "2024-07-02", "2024-07-01", "2024-06-30", "2024-06-29",
                   "2024-06-28", "2024-06-27", "2024-06-26", "2024-06-25", "2024-06-24",
                   "2024-06-23", "2024-06-22", "2024-06-21", "2024-06-20", "2024-06-19",
                   "2024-06-18", "2024-06-17", "2024-06-16", "2024-06-15", "2024-06-14","2024-07-12"],
    "Order Time": ["10:00 AM", "09:30 AM", "03:45 PM", "11:15 AM", "02:00 PM",
                   "08:45 AM", "01:20 PM", "04:30 PM", "10:10 AM", "11:00 AM",
                   "02:45 PM", "05:20 PM", "09:30 AM", "01:15 PM", "11:45 AM",
                   "03:00 PM", "10:20 AM", "02:30 PM", "08:45 AM", "12:00 PM",
                   "11:15 AM", "09:30 AM", "04:00 PM", "10:45 AM", "03:20 PM",
                   "01:00 PM", "02:30 PM", "09:15 AM", "11:45 AM", "08:00 AM","9:00 AM"]
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