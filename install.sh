#!/bin/bash
# MODAX Installation Script
# Installs all layers and sets up the environment

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PYTHON_MIN_VERSION="3.8"
DOTNET_VERSION="8.0"
MQTT_BROKER="mosquitto"

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Header
echo "=========================================="
echo "  MODAX Installation Script"
echo "  Version: 1.0.0"
echo "=========================================="
echo ""

# Check if running as root (not recommended)
if [ "$EUID" -eq 0 ]; then 
    log_warning "Running as root. It's recommended to run this script as a regular user."
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Detect OS
log_info "Detecting operating system..."
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
    log_success "Detected Linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
    log_success "Detected macOS"
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
    OS="windows"
    log_success "Detected Windows (Git Bash/Cygwin)"
else
    log_error "Unsupported operating system: $OSTYPE"
    exit 1
fi

# Function to check command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check Python version
check_python_version() {
    if command_exists python3; then
        PYTHON_CMD="python3"
    elif command_exists python; then
        PYTHON_CMD="python"
    else
        return 1
    fi
    
    PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
    REQUIRED_VERSION=$PYTHON_MIN_VERSION
    
    if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" = "$REQUIRED_VERSION" ]; then
        return 0
    else
        return 1
    fi
}

# Check prerequisites
log_info "Checking prerequisites..."

# Check Python
if check_python_version; then
    log_success "Python ${PYTHON_VERSION} found (minimum ${PYTHON_MIN_VERSION} required)"
else
    log_error "Python ${PYTHON_MIN_VERSION}+ not found. Please install Python first."
    exit 1
fi

# Check pip
if command_exists pip3; then
    PIP_CMD="pip3"
elif command_exists pip; then
    PIP_CMD="pip"
else
    log_error "pip not found. Please install pip first."
    exit 1
fi
log_success "pip found"

# Check .NET SDK (optional, only for HMI)
if command_exists dotnet; then
    DOTNET_VER=$(dotnet --version 2>&1)
    log_success ".NET SDK ${DOTNET_VER} found"
    DOTNET_INSTALLED=true
else
    log_warning ".NET SDK not found. HMI layer will not be available."
    log_warning "To install .NET SDK, visit: https://dotnet.microsoft.com/download"
    DOTNET_INSTALLED=false
fi

# Check/Install MQTT Broker
log_info "Checking MQTT broker..."
if command_exists mosquitto; then
    log_success "Mosquitto MQTT broker found"
    MQTT_INSTALLED=true
elif command_exists docker; then
    log_warning "Mosquitto not installed, but Docker is available."
    log_info "You can run MQTT broker with: docker run -d -p 1883:1883 eclipse-mosquitto"
    MQTT_INSTALLED=false
else
    log_warning "MQTT broker (Mosquitto) not found."
    if [ "$OS" = "linux" ]; then
        log_info "Install with: sudo apt-get install mosquitto mosquitto-clients"
    elif [ "$OS" = "macos" ]; then
        log_info "Install with: brew install mosquitto"
    fi
    MQTT_INSTALLED=false
fi

# Create directory structure
log_info "Setting up directory structure..."
mkdir -p logs
mkdir -p data
mkdir -p config
log_success "Directory structure created"

# Install Python Control Layer
echo ""
log_info "=== Installing Control Layer ==="
cd python-control-layer

if [ ! -d "venv" ]; then
    log_info "Creating virtual environment..."
    $PYTHON_CMD -m venv venv
    log_success "Virtual environment created"
fi

log_info "Activating virtual environment..."
source venv/bin/activate || . venv/Scripts/activate

log_info "Installing dependencies..."
$PIP_CMD install --upgrade pip
$PIP_CMD install -r requirements.txt

if [ -f "dev-requirements.txt" ]; then
    read -p "Install development dependencies (mypy, pytest, flake8, etc.)? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        $PIP_CMD install -r dev-requirements.txt
        log_success "Development dependencies installed"
    fi
fi

log_success "Control Layer dependencies installed"
deactivate
cd ..

# Install Python AI Layer
echo ""
log_info "=== Installing AI Layer ==="
cd python-ai-layer

if [ ! -d "venv" ]; then
    log_info "Creating virtual environment..."
    $PYTHON_CMD -m venv venv
    log_success "Virtual environment created"
fi

log_info "Activating virtual environment..."
source venv/bin/activate || . venv/Scripts/activate

log_info "Installing dependencies..."
$PIP_CMD install --upgrade pip
$PIP_CMD install -r requirements.txt

if [ -f "dev-requirements.txt" ]; then
    read -p "Install development dependencies? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        $PIP_CMD install -r dev-requirements.txt
        log_success "Development dependencies installed"
    fi
fi

log_success "AI Layer dependencies installed"
deactivate
cd ..

# Setup .NET HMI Layer
if [ "$DOTNET_INSTALLED" = true ]; then
    echo ""
    log_info "=== Setting up HMI Layer ==="
    cd csharp-hmi-layer
    
    log_info "Restoring .NET packages..."
    dotnet restore
    log_success "HMI Layer packages restored"
    cd ..
else
    log_warning "Skipping HMI Layer setup (requires .NET SDK)"
fi

# Create configuration files
echo ""
log_info "=== Creating configuration files ==="

# Create .env file for control layer if it doesn't exist
if [ ! -f "python-control-layer/.env" ]; then
    log_info "Creating Control Layer .env file..."
    cat > python-control-layer/.env << 'EOF'
# MODAX Control Layer Configuration
MQTT_BROKER_HOST=localhost
MQTT_BROKER_PORT=1883
API_HOST=0.0.0.0
API_PORT=8000
AI_LAYER_URL=http://localhost:8001/analyze
AI_ENABLED=true
USE_JSON_LOGS=false
RATE_LIMIT_ENABLED=true
RATE_LIMIT_DEFAULT=100/minute
CORS_ORIGINS=*
EOF
    log_success "Control Layer .env created"
fi

# Create .env file for AI layer if it doesn't exist
if [ ! -f "python-ai-layer/.env" ]; then
    log_info "Creating AI Layer .env file..."
    cat > python-ai-layer/.env << 'EOF'
# MODAX AI Layer Configuration
AI_HOST=0.0.0.0
AI_PORT=8001
USE_JSON_LOGS=false
RATE_LIMIT_ENABLED=true
RATE_LIMIT_DEFAULT=100/minute
CORS_ORIGINS=*
EOF
    log_success "AI Layer .env created"
fi

# Create startup scripts
echo ""
log_info "=== Creating startup scripts ==="

# Create start-all script
cat > start-all.sh << 'EOF'
#!/bin/bash
# Start all MODAX services
# Services are fault-tolerant and will attempt to start independently

echo "Starting MODAX services..."

# Start MQTT broker if not running
if ! pgrep -x mosquitto > /dev/null; then
    echo "Starting MQTT broker..."
    if command -v mosquitto &> /dev/null; then
        mosquitto -d
    else
        echo "MQTT broker not found. Start manually or use Docker."
    fi
fi

# Start Control Layer
echo "Starting Control Layer..."
cd python-control-layer
source venv/bin/activate || . venv/Scripts/activate
nohup python main.py > ../logs/control-layer.log 2>&1 &
echo $! > ../logs/control-layer.pid
deactivate
cd ..

# Give control layer time to start
sleep 2

# Start AI Layer
echo "Starting AI Layer..."
cd python-ai-layer
source venv/bin/activate || . venv/Scripts/activate
nohup python main.py > ../logs/ai-layer.log 2>&1 &
echo $! > ../logs/ai-layer.pid
deactivate
cd ..

echo "Services started!"
echo "Control Layer: http://localhost:8000"
echo "AI Layer: http://localhost:8001"
echo ""
echo "Logs:"
echo "  Control Layer: logs/control-layer.log"
echo "  AI Layer: logs/ai-layer.log"
echo ""
echo "To stop services, run: ./stop-all.sh"
EOF
chmod +x start-all.sh
log_success "Created start-all.sh"

# Create stop-all script
cat > stop-all.sh << 'EOF'
#!/bin/bash
# Stop all MODAX services

echo "Stopping MODAX services..."

# Stop Control Layer
if [ -f logs/control-layer.pid ]; then
    PID=$(cat logs/control-layer.pid)
    if ps -p $PID > /dev/null 2>&1; then
        kill $PID
        echo "Stopped Control Layer (PID: $PID)"
        rm logs/control-layer.pid
    fi
fi

# Stop AI Layer
if [ -f logs/ai-layer.pid ]; then
    PID=$(cat logs/ai-layer.pid)
    if ps -p $PID > /dev/null 2>&1; then
        kill $PID
        echo "Stopped AI Layer (PID: $PID)"
        rm logs/ai-layer.pid
    fi
fi

echo "Services stopped!"
EOF
chmod +x stop-all.sh
log_success "Created stop-all.sh"

# Run validation
echo ""
log_info "=== Running validation ==="

# Validate Control Layer
log_info "Validating Control Layer..."
cd python-control-layer
source venv/bin/activate || . venv/Scripts/activate
$PYTHON_CMD -c "import control_layer; import control_api; print('Control Layer imports OK')"
deactivate
cd ..
log_success "Control Layer validated"

# Validate AI Layer
log_info "Validating AI Layer..."
cd python-ai-layer
source venv/bin/activate || . venv/Scripts/activate
$PYTHON_CMD -c "import ai_service; import anomaly_detector; import wear_predictor; print('AI Layer imports OK')"
deactivate
cd ..
log_success "AI Layer validated"

# Final summary
echo ""
echo "=========================================="
echo -e "${GREEN}Installation Complete!${NC}"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Ensure MQTT broker is running"
if [ "$MQTT_INSTALLED" = false ]; then
    echo "     - Install Mosquitto or use Docker: docker run -d -p 1883:1883 eclipse-mosquitto"
fi
echo "  2. Start all services: ./start-all.sh"
echo "  3. Access Control Layer API: http://localhost:8000"
echo "  4. Access AI Layer API: http://localhost:8001"
if [ "$DOTNET_INSTALLED" = true ]; then
    echo "  5. Start HMI: cd csharp-hmi-layer && dotnet run"
fi
echo ""
echo "Documentation: docs/SETUP.md"
echo "Configuration: python-control-layer/.env and python-ai-layer/.env"
echo ""
echo "For help, see: README.md or open an issue on GitHub"
echo ""
