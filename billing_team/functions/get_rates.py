import io
import os
import pandas as pd
from flask import send_file, make_response, jsonify
from sql.billing_sql import Rates, session
from datetime import datetime

SAVE_DIR = "/app/out"

#getting the rates from the DB
def get_rates_db():
    execl_data = []
    rates = session.query(Rates).all()
    for r in rates:
        data = {'Product' : r.product_id, 'Rate' : r.rate, 'Scope' : r.scope}
        execl_data.append(data)
    data_formated = pd.DataFrame(execl_data)
    print(data_formated)
    execl_file = create_execl(data_formated)
    return execl_file

#create an execl file from the data we get from the  DB
def create_execl(data_formated):
    # execl_file = io.BytesIO()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = f"rates_{timestamp}.xlsx"
    file_path = os.path.join(SAVE_DIR, file_name)
    with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
        data_formated.to_excel(writer, index=False)
    # execl_file.seek(0)

    with open(file_path, 'rb') as f:
        file_content = f.read()
        response = make_response(file_content)
        response.headers['Content-Disposition'] = 'attachment; filename=Rates.xlsx'
        response.headers['Content-type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'

    return jsonify({"success": "file sent to the output directory"}), 200


if __name__ == '__main__':
    get_rates_db()