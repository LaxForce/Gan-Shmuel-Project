import pandas as pd
from sqlalchemy import update, and_, insert
from sql.billing_sql import Rates, session
from flask import jsonify

execl_data = []

#get the data from the execl file and proces it to object for storing in the BD
def getting_execl_data(file):
    file_path = f"/app/in/{file}"
    try:
        df = pd.read_excel(file_path)
    except Exception as e:
        log = f"error: no file found {str(e)}"
        return {"error": log} , 400

    for i in df.index:
        execl_data.append({
            'product' : df.Product[i],
            'rate' : df.Rate[i],
            'scope' : df.Scope[i],
        })

    # print(f"execl_data = {execl_data}")
    rates_update = update_rate_db()
    return rates_update

#update the reates in the DB
def update_rate_db():
    for prod in execl_data:
        # print(f"prod = {prod}")
        product_element = session.query(Rates).filter(
            and_(Rates.product_id == prod['product'],
                 Rates.scope == prod['scope']
                 )
        ).all()
        if (product_element):
            for element in product_element:
                # print(f"true {element.__dict__}")
                stmt = update(Rates).where(
                    and_(Rates.product_id == prod['product'], Rates.scope == f"{prod['scope']}")
                ).values(rate = prod['rate'])
                session.execute(stmt)
                session.commit()
        else:
            # print(f"{prod['product']} not exist")
            stmt = insert(Rates).values(product_id = prod['product'], rate = prod['rate'], scope = f"{prod['scope']}")
            session.execute(stmt)
            session.commit()
            # print(f"create {stmt}")
    return jsonify("All the rates are updated"), 200

if __name__ == '__main__':
    getting_execl_data(file)