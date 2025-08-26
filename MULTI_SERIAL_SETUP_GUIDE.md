# Multi Serial Port Scanner - Setup Guide

## Overview

The Multi Serial Port Scanner is a custom Home Assistant integration that allows you to scan and monitor multiple serial ports simultaneously. This integration provides real-time data from multiple serial devices and displays them as sensors in your Home Assistant dashboard.

## Key Features

- **Simultaneous Port Scanning**: Monitor up to 50 serial ports at the same time
- **Real-time Data**: Continuous reading from all configured ports
- **Automatic Reconnection**: Handles connection drops and reconnects automatically
- **JSON Support**: Automatically parses JSON data for structured attributes
- **Error Handling**: Tracks connection status and error counts
- **Easy Configuration**: User-friendly setup through Home Assistant UI

## Maximum Ports Limitation

**Answer to your client's question**: The maximum number of ports that can be scanned simultaneously is **50 ports**. This is a conservative limit that should work well on most systems. The actual limit depends on:

- System resources (CPU, memory)
- Serial port hardware capabilities
- Network bandwidth (if using network serial adapters)
- Operating system limitations

For most practical applications, 10-20 ports should be more than sufficient.

## Installation

### Method 1: Manual Installation (Recommended)

1. **Copy the component files** to your Home Assistant custom_components directory:
   ```
   /config/custom_components/multi_serial/
   ├── __init__.py
   ├── config_flow.py
   ├── const.py
   ├── coordinator.py
   ├── manifest.json
   └── sensor.py
   ```

2. **Restart Home Assistant** to load the new integration.

### Method 2: Using HACS (Home Assistant Community Store)

1. Install HACS if you haven't already
2. Add this repository to HACS
3. Install the Multi Serial integration
4. Restart Home Assistant

## Configuration

### Step 1: Add Integration

1. Go to **Settings** → **Devices & Services**
2. Click **Add Integration**
3. Search for **"Multi Serial Port Scanner"**
4. Click on it to start the setup

### Step 2: Basic Configuration

1. **Name**: Enter a name for your multi-serial scanner (e.g., "Factory Sensors")
2. **Scan Interval**: Set how often to check for new data (default: 1 second)

### Step 3: Add Serial Ports

For each serial port you want to monitor:

1. **Port Name**: Select from available serial ports (COM1, COM2, /dev/ttyUSB0, etc.)
2. **Baudrate**: Set the communication speed (default: 9600)
3. **Data Bits**: Number of data bits (5, 6, 7, or 8)
4. **Parity**: Parity checking (None, Even, Odd, Mark, Space)
5. **Stop Bits**: Number of stop bits (1, 1.5, or 2)
6. **Flow Control**: XON/XOFF, RTS/CTS, or DSR/DTR settings
7. **Timeout**: Read timeout in seconds

### Step 4: Add More Ports

- Click **"Add More Ports"** to configure additional serial ports
- You can add up to 50 ports total
- Each port can have different settings

## Viewing Data in Home Assistant

### Dashboard Cards

After setup, you'll see several new sensors:

1. **Summary Sensor**: Shows overall status (e.g., "5/8 connected")
2. **Individual Port Sensors**: One sensor per configured port

### Adding to Dashboard

1. Go to **Overview** → **Edit Dashboard**
2. Click **Add Card**
3. Choose **Entities** card
4. Add your Multi Serial sensors:
   - `sensor.serial_port_com1` (or your port name)
   - `sensor.multi_serial_scanner_summary`

### Sensor Attributes

Each port sensor includes these attributes:
- **Port**: The serial port name
- **Connection Status**: connected/error/disconnected
- **Last Read**: Timestamp of last data received
- **Read Count**: Total number of successful reads
- **Error Count**: Number of connection errors
- **Raw Data**: The actual data received
- **Custom Attributes**: Any JSON data parsed from the serial stream

## Example Configuration

### YAML Configuration (Alternative)

You can also configure via `configuration.yaml`:

```yaml
multi_serial:
  name: "Factory Monitoring"
  scan_interval: 1.0
  ports:
    - port_name: "COM1"
      baudrate: 9600
      bytesize: 8
      parity: "N"
      stopbits: 1
      xonxoff: false
      rtscts: false
      dsrdtr: false
      timeout: 1.0
    - port_name: "COM2"
      baudrate: 115200
      bytesize: 8
      parity: "N"
      stopbits: 1
      xonxoff: false
      rtscts: false
      dsrdtr: false
      timeout: 1.0
```

## Troubleshooting

### Common Issues

1. **Port Not Found**
   - Check if the device is connected
   - Verify the port name (COM1, /dev/ttyUSB0, etc.)
   - Try different USB ports

2. **Connection Errors**
   - Verify baudrate and other settings match your device
   - Check if another application is using the port
   - Ensure proper permissions (Linux/Mac)

3. **No Data Received**
   - Check device is sending data
   - Verify correct baudrate
   - Check cable connections

### Logs

Check Home Assistant logs for detailed error information:
- Go to **Settings** → **System** → **Logs**
- Look for entries from `multi_serial`

## Performance Tips

1. **Optimize Scan Interval**: Use longer intervals (2-5 seconds) for less critical data
2. **Limit Ports**: Only monitor ports you actually need
3. **System Resources**: Monitor CPU and memory usage with many ports
4. **Network Serial**: Consider network serial adapters for remote devices

## Advanced Usage

### JSON Data Parsing

If your serial device sends JSON data, it will be automatically parsed:

```json
{"temperature": 25.5, "humidity": 60, "pressure": 1013.25}
```

This creates attributes:
- `temperature`: 25.5
- `humidity`: 60
- `pressure`: 1013.25

### Automation Examples

```yaml
# Alert when a port goes offline
automation:
  - alias: "Serial Port Offline Alert"
    trigger:
      - platform: state
        entity_id: sensor.serial_port_com1
        to: "unavailable"
    action:
      - service: notify.mobile_app_your_phone
        data:
          message: "Serial port COM1 is offline!"

# Process temperature data from serial
automation:
  - alias: "High Temperature Alert"
    trigger:
      - platform: numeric_state
        entity_id: sensor.serial_port_com1
        attribute: temperature
        above: 30
    action:
      - service: notify.mobile_app_your_phone
        data:
          message: "High temperature detected: {{ state_attr('sensor.serial_port_com1', 'temperature') }}°C"
```

## Support

For issues or questions:
1. Check the Home Assistant logs
2. Verify your serial port settings
3. Test with a simple serial terminal first
4. Check the integration's GitHub repository for updates

## Technical Details

- **Dependencies**: pyserial-asyncio
- **Platform**: Works on Windows, Linux, and macOS
- **Architecture**: Uses asyncio for non-blocking I/O
- **Memory Usage**: Approximately 1-2MB per active port
- **CPU Usage**: Minimal when ports are idle, increases with data frequency
