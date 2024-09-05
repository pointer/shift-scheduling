import yaml
import smtplib
import logging
from os.path import basename
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

with open('config.yaml', encoding='utf-8') as f:
    config = yaml.safe_load(f)


def send_report():
    msg = MIMEMultipart()
    msg["From"] = config["reporting_sender"]
    msg["To"] = config["reporting_receiver"]
    msg["Subject"] = f"Отчет о тестировании от {datetime.utcnow()}"

    with open(config["reporting_file_path"], "rb") as f:
        part = MIMEApplication(f.read(), Name=basename(config["reporting_file_path"]))
        part['Content-Disposition'] = f"attachment; filename=\"{basename(config['reporting_file_path'])}\""
        msg.attach(part)

    server = smtplib.SMTP(config["reporting_smtp_host"], config["reporting_smtp_port"])
    try:
        server.starttls()
        server.login(config["reporting_sender"], config["reporting_password"])
        server.sendmail(config["reporting_sender"], config["reporting_receiver"], msg.as_string())
    except:
        logging.exception("Exception while send test report.")
    finally:
        server.quit()
