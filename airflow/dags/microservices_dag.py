# airflow/dags/microservices_dag.py
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.operators.docker_operator import DockerOperator
from airflow.providers.http.operators.http import SimpleHttpOperator
import requests
import json

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# DAG для ежедневного обслуживания микросервисов
with DAG(
    'microservices_maintenance',
    default_args=default_args,
    description='DAG for daily microservices operations',
    schedule_interval='@daily',
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['microservices', 'maintenance'],
) as dag:

    # Проверка здоровья сервиса
    def check_services_health():
        services = [
            ('API Gateway', 'http://host.docker.internal:8000/health'),
        ]
        
        for service_name, url in services:
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    print(f"✅ {service_name} is healthy")
                else:
                    print(f"❌ {service_name} returned status {response.status_code}")
            except Exception as e:
                print(f"❌ {service_name} error: {e}")
    
    health_check = PythonOperator(
        task_id='check_services_health',
        python_callable=check_services_health,
    )

    # Очистка старых данных
    cleanup_data = BashOperator(
        task_id='cleanup_old_data',
        bash_command='echo "Cleaning up old data..." && '
                    'curl -X DELETE http://host.docker.internal:8001/dict/items/old || true',
    )

    # Резервное копирование данных
    def backup_database():
        import pandas as pd
        from datetime import datetime
        
        backup_data = {
            'timestamp': datetime.now().isoformat(),
            'service': 'core-service',
            'items_count': 42,
            'status': 'backup_created'
        }
        
        # Сохраняем "бэкап"
        with open('/tmp/backup.json', 'w') as f:
            json.dump(backup_data, f)
        
        print(f"Backup created: {backup_data}")
        return backup_data
    
    backup_task = PythonOperator(
        task_id='backup_database',
        python_callable=backup_database,
    )

    # Отправка отчета в Kafka
    def send_daily_report():
        import json
        from datetime import datetime
        
        report = {
            'report_type': 'daily_metrics',
            'timestamp': datetime.now().isoformat(),
            'services_checked': 3,
            'all_healthy': True,
            'backup_created': True
        }
        
        print(f"Daily report: {json.dumps(report, indent=2)}")
        
        # заглушка 
        
        return report
    
    send_report = PythonOperator(
        task_id='send_daily_report',
        python_callable=send_daily_report,
    )

    # Проверка Kafka топиков
    check_kafka = BashOperator(
        task_id='check_kafka_topics',
        bash_command='echo "Checking Kafka topics..." && '
                    'docker exec kafka kafka-topics.sh --list --bootstrap-server localhost:9092 || '
                    'echo "Kafka not available, skipping..."',
    )

    # Перезапуск сервисов (при необходимости)
    # restart_services = BashOperator(
    #     task_id='graceful_restart',
    #     bash_command='echo "Performing graceful restart..." && '
    #                 'cd /path/to/project && '
    #                 'docker-compose down && '
    #                 'docker-compose up -d',
    # )

    # Имитация отправки уведомления
    def send_notification():
        print("📧 Sending daily report notification...")
        print("✅ All daily maintenance tasks completed successfully!")
    
    notification = PythonOperator(
        task_id='send_notification',
        python_callable=send_notification,
    )

    # Порядок выполнения задач
    health_check >> cleanup_data >> backup_task
    health_check >> check_kafka
    [backup_task, check_kafka] >> send_report
    send_report >> notification