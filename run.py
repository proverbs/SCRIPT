import os
import subprocess
import json
import time
from argparse import ArgumentParser
from datetime import datetime
import paramiko
import pytz
import time

HOME_DIR = './'
VAR_FILE_PATH = './variables.env'
TF_DIR = './utils/aws/terraform'
TF_VAR_TEMPLATE_PATH = os.path.join(TF_DIR, 'variables.tf.template')
TF_VAR_FILE_PATH = os.path.join(TF_DIR, 'variables.tf')
POSTGRES_INFO_SETUP_PATH = './ec2setup/utils/postgres_info.json'
POSTGRES_INFO_AlGORITHM1_PATH = './ec2setup/algorithms/SmartCharging/postgres_info.json'
POSTGRES_INFO_AlGORITHM2_PATH = './ec2setup/algorithms/LoadForecasting/postgres_info.json'
POSTGRES_INFO_AlGORITHM3_PATH = './ec2setup/algorithms/CostBenefitAnalysis/cases/basecase/results/postgres_info.json'
SSL_KEY_PATH = os.path.join(TF_DIR, 'script.pem')
WEBSERVER_DIR = './webserver'
FRONTEND_DIR = './frontend'

EC2_IP = None
DB_HOST = None

parser = ArgumentParser()
parser.add_argument("-i", "--instance", dest="EC2_IP", default=None,
                    help="instance IP (all dependencies should be installed)")
parser.add_argument("-d", "--database", dest="DB_HOST", default=None,
                    help="postgres database host")
args = parser.parse_args()


def read_env_variables(file_path):
    """read environment variables for the whole project and return as a dict
        file_path: path for variables.env
    """
    with open(file_path, 'r') as f:
        content = f.readlines()
    var_dict = {}
    for line in content:
        if '=' in line:
            key, value = line.strip().split('=')
            var_dict[key] = value
    return var_dict


def generate_tf_variables(var_dict, in_path, out_path):
    """generate variables.tf for terraform
        var_dict: dict from variables.env for the whole project
        in_path: variables_template.tf
        out_path: variables.tf
    """
    with open(in_path, 'r') as f:
        content = f.readlines()
    template = [line for line in content]

    for key, value in var_dict.items():
        var_key = '$' + key
        for i in range(len(template)):
            if var_key in template[i]:
                template[i] = template[i].replace(var_key, value)
    
    with open(out_path, 'w') as f:
        for line in template:
            f.write(line)


def run_terraform(tf_dir):
    """run terraform to launch all resources required
        tf_dir: directory containing main.tf file
    """
    # terraform init
    result = subprocess.run(['terraform', 'init'], stdout=subprocess.PIPE, cwd=tf_dir)
    print(result.stdout.decode('utf-8'))

    # terraform apply
    process = subprocess.Popen(['terraform', 'apply', '-auto-approve'], stdout=subprocess.PIPE, cwd=tf_dir)
    while True:
        output = process.stdout.readline().decode('utf-8')
        if process.poll() is not None and output == '':
            break
        if output:
            print (output.strip())
    retval = process.poll()

    # get DB_HOST from output
    db_host = subprocess.run(['terraform', 'output', 'script_postgresql_db_host'], stdout=subprocess.PIPE, cwd=tf_dir)
    db_host, _ = db_host.stdout.decode('utf-8').strip().split(':')

    # get EC2 IP from output
    ec2_ip = subprocess.run(['terraform', 'output', 'script_algorithm_ins_ip'], stdout=subprocess.PIPE, cwd=tf_dir)
    ec2_ip = ec2_ip.stdout.decode('utf-8').strip()

    return db_host, ec2_ip


def upload_code():
    # compress source code for ec2 instance
    result = subprocess.run(['tar', 'czf', 'SCRIPT.tar.gz', 'ec2setup/', 's3watch/', 'utils/', 'run_algorithm.sh', 'variables.env'], stdout=subprocess.PIPE, cwd=HOME_DIR)
    print(result.stdout.decode('utf-8'))
    print("Compressed code!")

    # scp the compressed code to ec2
    key = paramiko.RSAKey.from_private_key_file(SSL_KEY_PATH)
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    client.connect(hostname=EC2_IP, username="ubuntu", pkey=key)

    destination = '/home/ubuntu/SCRIPT.tar.gz'
    sftp = client.open_sftp()
    sftp.put('SCRIPT.tar.gz', destination)
    sftp.close()
    
    # destination = 'ubuntu@' + EC2_IP + ':/home/ubuntu/SCRIPT.tar.gz'
    # result = subprocess.run(['scp', '-i', SSL_KEY_PATH, 'SCRIPT.tar.gz', destination], stdout=subprocess.PIPE, cwd=HOME_DIR)
    # print(result.stdout.decode('utf-8'))
    # print("Uploaded code!")


def run_algorithm(db_host, ssl_key_path):
    # save information into a file for reading
    postgres_info = {
        'DB_HOST': db_host,
        'CLEANED_DATA_BUCKET_NAME': env_var_dict['CLEANED_DATA_BUCKET_NAME'],
        'POSTGRES_USER': env_var_dict['POSTGRES_USER'],
        'POSTGRES_PASSWORD': env_var_dict['POSTGRES_PASSWORD'],
        'POSTGRES_DB': env_var_dict['POSTGRES_DB']
    }
    with open(POSTGRES_INFO_SETUP_PATH, 'w') as outfile:
        json.dump(postgres_info, outfile)
    
    with open(POSTGRES_INFO_AlGORITHM1_PATH, 'w') as outfile:
        json.dump(postgres_info, outfile)

    with open(POSTGRES_INFO_AlGORITHM2_PATH, 'w') as outfile:
        json.dump(postgres_info, outfile)

    with open(POSTGRES_INFO_AlGORITHM3_PATH, 'w') as outfile:
        json.dump(postgres_info, outfile)
    
    key = paramiko.RSAKey.from_private_key_file(ssl_key_path)
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    # Connect/ssh to an instance
    try:
        # Here 'ubuntu' is user name and 'instance_ip' is public IP of EC2
        client.connect(hostname=EC2_IP, username="ubuntu", pkey=key)

        print('Connect succeed...')
        # Execute a command(cmd) after connecting/ssh to an instance
        stdin, stdout, stderr = client.exec_command(
            'mkdir /home/ubuntu/SCRIPT && cd /home/ubuntu/SCRIPT && mv /home/ubuntu/SCRIPT.tar.gz ./ && tar xzf SCRIPT.tar.gz'
        )

        time.sleep(20)

        stdin, stdout, stderr = client.exec_command(
            'sudo chmod 777 /home/ubuntu/SCRIPT/run_algorithm.sh'
        )

        tz_NY = pytz.timezone('America/New_York') 
        datetime_NY = datetime.now(tz_NY)
        print("us-east-1 time:", datetime_NY.strftime("%H:%M:%S"))

        stdin, stdout, stderr = client.exec_command(
            '/home/ubuntu/SCRIPT/run_algorithm.sh'
        )
        print(stdout.read())
        print('error message:')
        print(stderr.read())
        # close the client connection once the job is done
        client.close()

    except Exception as e:
        print(e)


def check_args(tf_dir):
    """check args: specify EC2_IP and DB_HOST both or neither"""
    if args.EC2_IP is None and args.DB_HOST is None:
        db_host, ec2_ip = run_terraform(tf_dir)
    else:
        db_host, ec2_ip = args.EC2_IP, args.DB_HOST

    if db_host is None or ec2_ip is None:
        print('Please specify EC2_IP and DB_HOST both or neither.')
        exit(1)
    else:
        print('Instance IP: %s' % ec2_ip)
        print('Database Host: %s' % db_host)

    return db_host, ec2_ip


def start_local(db_host):

    # copy variables.env
    print('copying variables.env ...')
    _ = subprocess.run(['cp', './variables.env', './webserver/'], stdout=subprocess.PIPE, cwd=HOME_DIR)

    # docker-compose up (detached)
    print('running docker-compose up -d --build ...')

    env = {
        **os.environ,
        "DB_HOST": db_host,
    }
    process = subprocess.Popen(['docker-compose', 'up', '-d', '--build'], env=env, stdout=subprocess.PIPE)
    while True:
        output = process.stdout.readline().decode('utf-8')
        if process.poll() is not None and output == '':
            break
        if output:
            print (output.strip())
    retval = process.poll()


env_var_dict = read_env_variables(VAR_FILE_PATH)
generate_tf_variables(env_var_dict, TF_VAR_TEMPLATE_PATH, TF_VAR_FILE_PATH)
DB_HOST, EC2_IP = check_args(TF_DIR)
upload_code()
start_local(DB_HOST)
run_algorithm(DB_HOST, SSL_KEY_PATH)
