from time import sleep
from traceback import format_exc
from murdaws import murd_ddb as mddb

try:
    mddb.ddb_murd_prefix = "musbb_murd_"
    murd = mddb.DDBMurd("BountyBoard")
    purchase_murd = mddb.DDBMurd("purchases")
except Exception:
    print(f"Unable to initialize hyperspace murds: {format_exc()}")
finally:
    def provision_murd_tables():
        mddb.DDBMurd.create_murd_table("BountyBoard")
        mddb.DDBMurd.create_murd_table("purchases")
        for i in range(10):
            sleep(10)
            try:
                murd = mddb.DDBMurd("BountyBoard")
                purchase_murd = mddb.DDBMurd("purchases")
                break
            except:
                pass
        return murd, purchase_murd
