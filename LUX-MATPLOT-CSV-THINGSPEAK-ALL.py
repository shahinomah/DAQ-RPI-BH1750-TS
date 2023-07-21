import smbus
import time
import csv
import matplotlib.pyplot as plt
import requests

# Define some constants from the datasheet
DEVICE = 0x23 # Default device I2C address

# Start measurement at 1lx resolution. Time typically 120ms
ONE_TIME_HIGH_RES_MODE_1 = 0x20

# ThingSpeak Configuration
channel_id = 2223821 # Replace with your ThingSpeak channel ID
write_key = '****************'  # Replace with your ThingSpeak write API key

#bus = smbus.SMBus(0) # Rev 1 Pi uses 0
bus = smbus.SMBus(1)  # Rev 2 Pi uses 1

def convertToNumber(data):
    # Simple function to convert 2 bytes of data
    # into a decimal number.
    result = (data[1] + (256 * data[0])) / 1.2
    return result

def readLight(addr=DEVICE):
    # Read data from I2C interface
    data = bus.read_i2c_block_data(addr, ONE_TIME_HIGH_RES_MODE_1)
    return convertToNumber(data)

# Set up lists for storing data
period_data = []
light_data = []

# Configure the plot
plt.ion()
fig, ax = plt.subplots()
line, = ax.plot(period_data, light_data)
ax.set_xlabel('Period (s)')
ax.set_ylabel('Light Level (lx)')

# Catch when script is interrupted, cleanup correctly
try:
    start_time = time.time()  # Start time for calculating the period
    point = 1  # Initial point counter

    # Get current date and time for the CSV file name
    current_datetime = time.strftime('%Y-%m-%d_%H-%M-%S', time.localtime())
    csv_filename = 'data_{}.csv'.format(current_datetime)

    # Main loop
    while True:
        light_level = readLight()
        current_time = time.time()
        period = current_time - start_time

        # Append data to lists
        period_data.append(period)
        light_data.append(light_level)

        # Limit data to display the last 100 points
        period_data = period_data[-100:]
        light_data = light_data[-100:]

        # Update the plot
        line.set_data(period_data, light_data)
        ax.relim()
        ax.autoscale_view()
        plt.draw()
        plt.pause(0.1)

        # Print the light level to the serial monitor
        print("Light Level: {:.2f} lx".format(light_level))

        # Save data to CSV file
        with open(csv_filename, 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([point, time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(current_time)), period, light_level])

        # Send data to ThingSpeak
        url = f"https://api.thingspeak.com/update?api_key={write_key}&field1={light_level}"
        response = requests.get(url)
        #if response.status_code == 200:
        #    print("Data sent to ThingSpeak successfully.")
        #else:
        #    print("Failed to send data to ThingSpeak.")

        # Increment the point counter
        point += 1

        time.sleep(0.5)

except KeyboardInterrupt:
    pass
finally:
    plt.ioff()
    plt.show()
