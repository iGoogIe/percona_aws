# percona_aws
Three Node Percona DB Cluster in AWS

# Run book

1. Set up ENV Vars you'll need later (added to .bashrc)
    
    ```python
    export PERCONA_PASSWORD=xx
    export AWS_ACCESS_KEY_ID=xx
    export AWS_SECRET_ACCESS_KEY=xx
    ```
    
    - ensure PERCONA_PASSWORD is in vars file i.e below does a lookup of env var
    
    ```python
    percona_password: "{{ lookup('env', 'PERCONA_PASSWORD')}}"
    ```
    

---

# Percona Runbook

1. Run AWS Creation Scripts. 
    - No inventory required yet since we're localhost.
    - Run from ~/percona_aws/ansible (.venv preferred)
    
    ```python
    ansible-playbook driver.yml -e target_hosts='localhost' --tags "sg,ec2,inventory"
    ```
    
2. Run percona bootstrap
    - Downloads dependencies and gets ready for install of the xtradb cluster
    
    ```python
    ansible-playbook -i aws_inventory.yml driver.yml -e target_hosts='node*' --tags bootstrap
    ```
    
3. ⭐ **MANUAL STEP** Install XtraDB Cluster
    - Wait for installation to complete on all 3 servers
    
    ```python
    sudo apt install -y percona-xtradb-cluster
    ```
    
4. Run db_post_install.yml
    - Bootstraps node1 i.e so he knows he's master
    - Sets up mysqld.cnf config files for replication
    - Grabs certs from node1 ( /var/lib/mysql) and pushes to node2/node3
    
    ```python
    ansible-playbook -i aws_inventory.yml driver.yml -e target_hosts='node*' --tags "post_install"
    ```
    
5. Run bootstrap_node1.yml
    - Stops bootstrap svc on Node1,
    - add cluster ips
    - starts normal mysql service
    
    ```python
    ansible-playbook -i aws_inventory.yml driver.yml -e target_hosts='node1' --tags "bootstrap_n1"
    ```
    
6. ⭐ **MANUAL STEP login to DB and create automation user, grant priv.**
    
    ```python
    sudo mysql -u root -p
    ```
    
    ```python
    CREATE USER 'automation'@'%' IDENTIFIED WITH mysql_native_password BY 'percona123';
    ```
    
    ```python
    GRANT ALL PRIVILEGES ON *.* TO 'automation'@'%';
    ```
    
    ```python
    FLUSH PRIVILEGES;
    ```
    
7. Create DB / Tables / Inserts on ONLY node1
    
    ```python
    ansible-playbook -i aws_inventory.yml driver.yml -e target_hosts='node1' --tags "mysql_creds,create_db,table_data"
    ```
    
8.  (#2 Cloudwatch) Create + attach IAM Policy
    - Creates IAM policy necessary for sending metrics to cloudwatch
    - Attaches policy to IAM user you specify in your vars file
    
    ```python
    ansible-playbook -e target_hosts="localhost" driver.yml --tags iam
    ```
    
9.  (#2 Cloudwatch) Run setup for disk monitor dependencies + aws creds (node1)
    - Creates awscreds.conf reading in environment vars
    - Creates cron job for putting disk utilization metrics to cloudwatch every 5m
    
    ```python
    ansible-playbook -i aws_inventory.yml -e target_hosts="node1" driver.yml --tags disk
    ```
    
    - Go to Cloudwatch + Metrics and show metrics
10. (#3 Lambda) Manual as per instructions (similar code in percona_aws/python/lambda_test.py)
    1. Cloudwatch Alarms → show no alarms
        1. Grab EC2 Instance ID for node1 into clipboard
        2. Go to Lambda → Code → Test
        3. Set InstanceID + Action to Launched → run test → show alarm created
    2. Set Action to "terminated" → run test → show that nothing is done
    3. Run fallocate cmd on node1 to trigger alarm
        
        ```python
        fallocate -l 5G file
        
        ```
        
    - Show Cloudwatch Alarm is triggered

---

# Cleanup

### Stop Services + EC2s

```python
ansible-playbook -i aws_inventory.yml driver.yml -e target_hosts='node*' --tags "stop_mysql"
```

```python
ansible-playbook driver.yml -e target_hosts='localhost' --tags "stop_ec2s"
```

### Start EC2s + Services

```python
ansible-playbook driver.yml -e target_hosts='localhost' --tags "start_ec2s"
```

- NOTE: Manual Effort: Ensure you update public IPs in aws_inventory.yml!
    - This is done automatically on brand new cluster spinup , but not on stop/start (feature enhancement opportunity)
- Run below to ensure we bootstrap node1 again, add node2 + node3 to cluster , then add cluster ips to node1.

```python
ansible-playbook -i aws_inventory.yml driver.yml -e target_hosts='node*' --tags "post_install,bootstrap_n1"
```

## Cluster Teardown

- Run playbook for deleting local files + termination of EC2s
    
    ```python
    ansible-playbook driver.yml -e target_hosts='localhost' --tags cleanup
    ```