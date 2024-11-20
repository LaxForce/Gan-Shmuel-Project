from sqlalchemy import update
from billing_sql import Providers, session


def test2():
    stmt = update(Providers).where(Providers.id == 10007).values(name='123')
    session.execute(stmt)
    session.commit()
    prov = session.query(Providers).filter(Providers.id == 10007).first()
    print(prov.__dict__)
    # session.execute(insert(Providers),
    #                 [
    #                     {"name": "hatzil"}
    #                 ])
    prov_last = session.query(Providers).filter(Providers.id == 10023).one()
    print(f"last {prov_last.__dict__}")

if __name__ == '__main__':
    test2()
