import os
import io
from dotenv import load_dotenv
import subprocess
# https://www.datacamp.com/tutorial/python-subprocess
import pandas as pd
from flask import Flask, request, render_template
import google.cloud.logging
from google.cloud import bigquery
from google.cloud import storage
from json2html import *
from tempfile import NamedTemporaryFile
import logging
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from zipfile import ZipFile, ZipInfo

clientCL = google.cloud.logging.Client()
clientCL.setup_logging()
clientBQ = bigquery.Client()
clientGCS = storage.Client()

to_emails = os.environ.get('TO_EMAILS')
sendgrid_api_key = os.environ.get('SENDGRID_API_KEY')
GS_DATALAKE=os.environ.get('GS_DATALAKE')
GS_ZIP=os.environ.get('GS_ZIP')

app = Flask(__name__)

def list_cs_files(bucket_name, start_with='', file_ext='csv'): 
    list_blobs = clientGCS.list_blobs(bucket_name)
    file_list = [file.name for file in list_blobs if ((file.name.startswith(start_with)) & (os.path.splitext(file.name)[1]=='.'+file_ext)  )]
    return file_list

# Load a GCS file into BigQuery
@app.route("/load", methods=['POST'])
def run_load():
    # Parse the request data, itt a seed_raw.json a -d body
    request_data = request.get_json()
    request_params = request_data.get("params", {})
    # project_id = request_params.get("project_id", None)
    # region = request_params.get("region", None)
    bucket_name = request_params.get("bucket_name", None)
    clean_blobs = request_params.get("clean_blobs", False)
    dataset_id = request_params.get("dataset_id", None)
    table_load_config = request_params.get("load_job_config", {})
    sources = request_data.get("sources", {})

    logging.info("Request data: {}".format(request_data))
    source_list = list(sources.keys()) 

    response={}
    response['request_data']=request_data
    check_sources={}
    both_files=True
    for source in source_list:
        list_files=list_cs_files(bucket_name,source)
        check_sources.update({source:list_files}) 
        both_files=both_files&(len(list_files)>0)

    if not both_files:
        response={"status": 1, "result":"not both files are present"}
        return response, 200
    
    # ha mindket cucc van, megyunk tovabb
    bucket = clientGCS.bucket(bucket_name)
    success=True
    response={"result":[]}
    for source in source_list:
        table_settings=sources[source]
        table_ref = clientBQ.dataset(dataset_id).table(table_settings['table_name'])
        table_columns = table_settings['table_columns']

        files_to_load=check_sources[source]

        job_config = bigquery.LoadJobConfig(**table_load_config)
        # Configure table schema
        _schema = []
        for c in table_columns:
            field = bigquery.SchemaField(c["name"], c.get("type", "string"), c.get("mode", "NULLABLE"))
            _schema.append(field)
        job_config.schema = _schema

        # most egyenkent a megfelelo fajlok feltoltese BQ-ba
        for blob_name in files_to_load:
            blob = bucket.blob(blob_name)
            # link = blob.path_helper(bucket_name, blob_name)
            source_file_uri = 'gs://' + bucket_name + '/' + blob_name
            try:
                job = clientBQ.load_table_from_uri(source_file_uri,table_ref, job_config=job_config)
                job.result()  # Wait for the table load to complete
                response["result"].append({"status": "ok", "blob": blob_name, "table": table_settings['table_name'] })
                logging.warning("siker: {}".format(response))
                # torcsi a cuccot
                if clean_blobs: 
                    blob.delete()
    
            except Exception as e:
                response["result"].append( {"status": "error", "message": e.message})
                logging.error("kudarc: {}".format(response))
                success=False
    
    # response["result"]=str(response["result"])
    if success:
        response["status"]=0
        return response, 200
    else:
        response["status"]=2
        return response, 550

# Execute a dbt command
@app.route("/dbt", methods=["POST"])
def run_dbt():

    request_data = request.get_json()
    request_params = request_data.get("params", {})
    project_id = request_params.get("project_id", None)

    logging.info("Request data: {}".format(request_data))

    # google_clients(project_id)   
    # logging.info("Started processing request on endpoint {}".format(request.base_url))

    command = ["dbt"]
    arguments = []


    if request_data:
        if "cli" in request_data.get("params", {}):
            arguments = request_data["params"]["cli"].split(" ")
            command.extend(arguments)

    # Add an argument for the project dir if not specified
    if not any("--project-dir" in c for c in command):
        project_dir = os.environ.get("DBT_PROJECT_DIR", None)
        if project_dir:
            command.extend(["--project-dir", project_dir])

    # Execute the dbt command
    result = subprocess.run(command,
                            text=True,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT)
    # Format the response
    response = {
        "status": result.returncode,
        "result": {
            # "status": "ok" if result.returncode == 0 else "error",
            "args": result.args,
            "return_code": result.returncode,
            "command_output": result.stdout,
        }
    }

    logging.info("Command output: {}".format(response["result"]["command_output"]))
    logging.info("Command status: {}".format(response["status"]))
    logging.info("Finished processing request on endpoint {}".format(request.base_url))
    
    # response["result"]=str(response["result"])
    return response, 200

@app.route("/cities")
def bq_info():

    query = f"""
        SELECT distinct city_name
        FROM `dott_datamart_layer.rides_datamart` ;
    """
    clientBQ = bigquery.Client()
    try:
        query_job = clientBQ.query(query)
        # TODO BQ to DF
        
        city_names = []
        for row in query_job:
            city_names.append(row["city_name"])
        
        results = dict(zip( ["City"] * len(city_names) , city_names))
        
        results = {'cities': list(set(city_names))}
        return json2html.convert(json=results)
        # return render_template("resultats.html", table_source=results)
    except:
        return render_template("index.html", chapitre="Data marts are not ready yet, <br>wait for mail to access")    
    # return render_template('dott_res.html', results=results)


@app.route("/rides/<city_name>")
def bq_data(city_name):
    query = f"""
            SELECT vehicle_type,
            COUNT(ride_id) number_of_rides, 
            SUM(amount_ride) revenue_from_rides, 
            SUM(amount_pass) revenue_from_pass_purchases,
            ROUND(SUM(amount_ride+amount_pass)/COUNT(ride_id))  avg_total_revenue_per_ride,
            ROUND(AVG(ride_mins)) avg_ride_duration_mins,
            MAX(peak_hour) peak_hour
            FROM `dott_datamart_layer.rides_datamart` t1
            LEFT JOIN 
            (SELECT COUNT(ride_id) rides, ride_hour peak_hour,city_name, vehicle_type  FROM `dott_datamart_layer.rides_datamart` GROUP BY 2,3,4 ORDER BY 1 DESC LIMIT 1) t2 USING (city_name, vehicle_type)
            WHERE city_name='{city_name}' AND amount_pass is not null
            GROUP BY 1;
        """
    clientBQ = bigquery.Client()
    query_job = clientBQ.query(query)
    # TODO BQ to DF
    data=[]
    for row in query_job:
        data.append({k:v for k,v in zip(row.keys(),row.values())})
    
    data={}
    for row in query_job:
        res = {k:v for k,v in zip(row.keys(),row.values())}
        key = res['vehicle_type']
        del res['vehicle_type']
        data[key]=res

    return json2html.convert(json=data) 
    # return render_template("resultats.html", table_source=data)


@app.route("/")
def main_route():
    # logging.warning('megy ez magatuul is!!')
    # return "to upload a file, please add to url: /upload"
    return render_template("index.html", chapitre="WELCOME to Rides and Purchases insights")   


# @app.route("/fgy", methods=['POST'])
# def run_fgy():
#     # Parse the request data, itt a seed_raw.json a -d body
#     request_data = request.get_json()
#     # logging.warning('rovidre zarva')   
#     return request_data.get("params", {}), 200

@app.route('/upload')   
def main(): 
    return render_template("index.html", chapitre="WELCOME to Rides and Purchases insights")   
  
@app.route('/success', methods = ['POST'])   
def success():   
    if request.method == 'POST':   
        fichier = request.files['file']    
        # project_id="gfeledi-dott"
        # region="europe-central2"
        bucket_name=GS_DATALAKE
        # google_clients(project_id, region, bucket_name)
        bucket = clientGCS.bucket(bucket_name)
        blob = bucket.blob(fichier.filename)

        contents = fichier.read()
        tempfile = NamedTemporaryFile(delete=False)
        try:
            with tempfile as f:
                f.write(contents)
            blob.upload_from_filename(tempfile.name)
        except Exception:
            return {"message": "There was an error uploading the file"}
        finally:
            os.remove(tempfile.name)

        logging.info('fichier telechargee sur GCS: ' + fichier.filename)

        return render_template("acknowledgement.html", name = fichier.filename)

@app.route('/run_achevee') 
def notify():
    content="datamart tables are ready"
    if to_emails is None or sendgrid_api_key is None:
        app.logger.info("Email notification skipped as TO_EMAILS or SENDGRID_API_KEY is not set")
        return

    app.logger.info(f"Sending email to {to_emails}")

    message = Mail(
        from_email='gfeledi@icloud.com',
        # from_email='noreply@bigquery-usage-notifier.com',
        to_emails=to_emails,
        subject='An expensive BigQuery job just completed',
        html_content=f'<html><pre>{content}</pre></html>')
    try:
        app.logger.info(f"Email content {message}")
        sg = SendGridAPIClient(sendgrid_api_key)
        response = sg.send(message)
        app.logger.info(f"Email status code {response.status_code}")
    except Exception     as e:
        print(e)


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=8080)