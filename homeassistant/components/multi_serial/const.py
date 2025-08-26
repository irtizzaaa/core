"""Constants for the Multi Serial integration."""

DOMAIN = "multi_serial"

# Configuration keys
CONF_PORTS = "ports"
CONF_PORT_NAME = "port_name"
CONF_BAUDRATE = "baudrate"
CONF_BYTESIZE = "bytesize"
CONF_PARITY = "parity"
CONF_STOPBITS = "stopbits"
CONF_XONXOFF = "xonxoff"
CONF_RTSCTS = "rtscts"
CONF_DSRDTR = "dsrdtr"
CONF_TIMEOUT = "timeout"
CONF_SCAN_INTERVAL = "scan_interval"

# Default values
DEFAULT_BAUDRATE = 9600
DEFAULT_BYTESIZE = 8
DEFAULT_PARITY = "N"
DEFAULT_STOPBITS = 1
DEFAULT_XONXOFF = False
DEFAULT_RTSCTS = False
DEFAULT_DSRDTR = False
DEFAULT_TIMEOUT = 1.0
DEFAULT_SCAN_INTERVAL = 1.0

# Maximum number of ports that can be scanned simultaneously
MAX_SIMULTANEOUS_PORTS = 50  # Conservative limit for most systems

# Serial port attributes
ATTR_PORT = "port"
ATTR_LAST_READ = "last_read"
ATTR_READ_COUNT = "read_count"
ATTR_ERROR_COUNT = "error_count"
ATTR_CONNECTION_STATUS = "connection_status"
