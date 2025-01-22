# ETL Pipeline

1. **Read from SQS Queue**: Retrieve user login behavior data from an SQS Queue.
2. **Transform Data**: Mask sensitive fields (`device_id` and `ip`) while ensuring masked values allow for duplicate identification.
3. **Load to PostgreSQL**: Store the transformed data into a PostgreSQL database.

### Target Table Schema
```sql
-- Creation of user_logins table
CREATE TABLE IF NOT EXISTS user_logins (
    user_id VARCHAR(128),
    device_type VARCHAR(32),
    masked_ip VARCHAR(256),
    masked_device_id VARCHAR(256),
    locale VARCHAR(32),
    app_version INTEGER,
    create_date DATE
);
```

## Getting Started

### Running the Application
 **Clone the Repository**:
   ```bash
   git clone https://github.com/yamsani-raviteja/Take-Home-ETL.git
   ```
**Changing the working directory**:
```
cd Take-Home-ETL
```

### Prerequisites
Ensure the following are installed on your local machine:
- Docker
- docker-compose
- awscli-local (`pip install awscli-local`)
- PostgreSQL client (`psql`) (MAC OS users can use brew for installing the psql) 
- Ensure your enivronment have all the requirements to run the project
```
pip install -r requirements.txt
```
###  Configure AWS CLI for local usage
Use the provided `aws-configuration.sh` file to set up:

To start the AWS CLI:
```bash
bash aws_configuration.sh
```

  
### Setup Docker Environment
Use the provided `docker-compose.yml` to spin up local versions of PostgreSQL and Localstack (emulating AWS services):

**1) To start the environment**:
```bash
docker-compose up -d
```

**2) Execute the Application**:
   Use the following command with your desired options:
```bash
python Code_ETL.py --endpoint-url http://localhost:4566 --queue-name login-queue --max-messages 50
```

   **3) Arguments**:
   - `-e`, `--endpoint-url`: SQS Endpoint URL (mandatory)
   - `-q`, `--queue-name`: SQS Queue name (mandatory)
   - `-t`, `--wait-time`: Wait time in seconds (default: 10)
   - `-m`, `--max-messages`: Maximum messages to process (default: 10)

 **4) Verify Data**:
   - Check if data has been loaded into PostgreSQL:
```bash
psql -d postgres -U postgres -h localhost -p 5432 -W
```
**5) To display the table columns, enter the password "postgres" and use the following command to verify the columns:**:
```
# postgres = select * from user_logins;
```

**6) Decrypting Masked PIIs**:
The `ip` and `device_id` fields are masked using base64 encoding. To recover the original values, you can use the following command:
```bash
echo -n "<sample_base64_encoded_string>" | base64 --decode
```

**7) Stop the Docker**:
   - Check if data has been loaded into PostgreSQL:
```bash
docker-compose down 
```

## Next Steps
If more time were available, the following enhancements could be considered:
- Error handling and logging for better fault tolerance.
- Implementing unit tests to ensure reliability.
- Scaling the application to handle larger datasets efficiently.
- Integrating with AWS services in a real AWS environment.
