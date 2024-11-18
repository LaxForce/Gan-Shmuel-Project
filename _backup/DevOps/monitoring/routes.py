from flask import Blueprint, render_template, request, session, redirect, url_for, jsonify
from functools import wraps
import psutil
import os
import subprocess
from flask_sock import Sock
import socket
import http.client
import json
from datetime import datetime

# Get ports from environment variables or use default
HTOP_PORT = int(os.getenv('HTOP_PORT', 8085))
LAZY_PORT = int(os.getenv('LAZY_PORT', 8087))

monitor_bp = Blueprint('monitoring', __name__, template_folder='templates', static_folder='static', static_url_path='/monitoring/static')
sock = Sock()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('monitoring.login'))
        return f(*args, **kwargs)
    return decorated_function

@monitor_bp.route('/monitoring', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        session['logged_in'] = True
        return redirect(url_for('monitoring.menu'))
    return render_template('login.html')

@monitor_bp.route('/monitoring/menu')
@login_required
def menu():
    return render_template('menu.html')

@monitor_bp.route('/monitoring/machine')
@login_required
def machine():
    return render_template('machine.html')

@monitor_bp.route('/monitoring/containers')
@login_required
def containers():
    return render_template('containers.html')

@monitor_bp.route('/monitoring/machine/metrics')
@login_required
def machine_metrics():
    return jsonify({
        'cpu': psutil.cpu_percent(),
        'memory': psutil.virtual_memory().percent,
        'disk': psutil.disk_usage('/').percent
    })


@monitor_bp.route('/monitoring/containers/list')
@login_required
def container_list():
    print("Starting container list retrieval")
    try:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.connect('/var/run/docker.sock')
        
        connection = http.client.HTTPConnection('localhost')
        connection.sock = sock
        
        # Get containers with size information
        connection.request('GET', '/containers/json?all=1&size=1')  # Added size=1 parameter
        response = connection.getresponse()
        containers_data = json.loads(response.read().decode())
        
        containers = []
        for container in containers_data:
            connection.request('GET', f'/containers/{container["Id"]}/stats?stream=false')
            stats = json.loads(connection.getresponse().read().decode())
            
            # Use SizeRw + SizeRootFs for total size
            total_size = (container.get('SizeRw', 0) + container.get('SizeRootFs', 0)) / (1024 * 1024)
            
            containers.append({
                'name': container['Names'][0].lstrip('/'),
                'status': container['State'],
                'cpu': calculate_cpu_percent(stats),
                'memory': calculate_memory_usage(stats),
                'created': datetime.fromtimestamp(container['Created']).strftime('%Y-%m-%d %H:%M:%S'),
                'size': total_size
            })
            
        return jsonify({'containers': containers})
        
    except Exception as e:
        print(f"Error in container_list: {str(e)}")
        print(f"Exception type: {type(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        raise


@monitor_bp.route('/monitoring/machine/terminal')
@login_required
def launch_htop():
    # Start ttyd with full path and explicit arguments
    cmd = ['/usr/local/bin/ttyd', '-p', str(HTOP_PORT), '-i', '0.0.0.0', 'nsenter', '-t', '1', '-m', '-p', 'htop']
    print(f"Launching ttyd with command: {' '.join(cmd)}")
    
    process = subprocess.Popen(
        cmd,
        stdout=None, # subprocess.PIPE,
        stderr=None, # subprocess.PIPE,
        universal_newlines=True
    )
    
    # Check if process started successfully
    if process.poll() is None:
        print(f"ttyd started successfully with PID {process.pid}")
    else:
        stdout, stderr = process.communicate()
        print(f"ttyd failed to start. stdout: {stdout}, stderr: {stderr}")
    
    return render_template('terminal.html')

@monitor_bp.route('/monitoring/containers/terminal')
@login_required
def launch_lazydocker():
    # Start ttyd with full path and explicit arguments
    cmd = ['/usr/local/bin/ttyd', '-p', str(LAZY_PORT), '-i', '0.0.0.0', '/usr/local/bin/lazydocker']
    print(f"Launching ttyd with command: {' '.join(cmd)}")
    
    process = subprocess.Popen(
        cmd,
        stdout=None, # subprocess.PIPE,
        stderr=None, # subprocess.PIPE,
        universal_newlines=True
    )
    
    # Check if process started successfully
    if process.poll() is None:
        print(f"ttyd started successfully with PID {process.pid}")
    else:
        stdout, stderr = process.communicate()
        print(f"ttyd failed to start. stdout: {stdout}, stderr: {stderr}")
    
    return render_template('terminal.html')


def calculate_cpu_percent(stats):
    # Check if we have the required CPU stats
    if not all(key in stats.get('cpu_stats', {}) for key in ['cpu_usage', 'system_cpu_usage']):
        return 0.0
    
    cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - stats['precpu_stats']['cpu_usage']['total_usage']
    
    # Check if system CPU usage is available
    if 'system_cpu_usage' in stats['cpu_stats'] and 'system_cpu_usage' in stats['precpu_stats']:
        system_delta = stats['cpu_stats']['system_cpu_usage'] - stats['precpu_stats']['system_cpu_usage']
        online_cpus = stats['cpu_stats'].get('online_cpus', 1)
        if system_delta > 0:
            return round((cpu_delta / system_delta) * online_cpus * 100, 2)
    
    return 0.0



def calculate_memory_usage(stats):
    memory_stats = stats.get('memory_stats', {})
    if 'usage' not in memory_stats:
        return 0.0
        
    usage = memory_stats['usage']
    return round(usage / (1024 * 1024), 2)  # Convert to MB


