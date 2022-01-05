#!/usr/bin/python3
# oc_database.py
# Read polls directly from own/nextcloud database
#
# (c) Kurt Garloff <kurt@garloff.de>, 1/2022
# SPDX-License-Identifier: AGPL-3.0

import sys

from sqlalchemy.ext.automap import automap_base
from sqlalchemy import create_engine
#from sqlalchemy.sql import select
from sqlalchemy.orm import Session

OC_PREFIX='oc_'

Base = automap_base()
session = None

def connect(conn):
    global Base, session
    engine = create_engine(conn)
    session = Session(engine)
    Base.prepare(engine, reflect=True)

def get_votes(conn_str, poll_id):
    if not session:
        connect(conn_str)
    pv_tbl = Base.classes[OC_PREFIX+'polls_votes']
    return list(filter(lambda x: x.poll_id == poll_id, session.query(pv_tbl)))

def main(argv):
    connect(argv[0])
    pp_tbl = Base.classes[OC_PREFIX+'polls_polls']
    for row in session.query(pp_tbl):
        print("%3i\t%s\t(%s, %s)" % (row.id, row.title, row.type, row.owner))

if __name__ == "__main__":
    main(sys.argv[1:])
