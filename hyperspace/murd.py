from time import sleep

from murdaws import murd_ddb as mddb

mddb.ddb_murd_prefix = "musbb_murd_"
murd = mddb.DDBMurd("BountyBoard")
purchase_murd = mddb.DDBMurd("purchases")


def provision_murd_tables():
    mddb.DDBMurd.create_murd_table("BountyBoard")
    mddb.DDBMurd.create_murd_table("purchases")
    sleep(10)
    murd = mddb.DDBMurd("BountyBoard")
    purchase_murd = mddb.DDBMurd("purchases")
    return murd, purchase_murd
