import sys
import sqlite3



def build_hierarchy(filename):
    db = sqlite3.connect(filename)

    parent_map = {i: p for i, p in db.execute('select id, parent_id from fma')}
    
    db.execute('drop table if exists hierarchy')
    db.execute("""create table if not exists hierarchy 
                   (id integer,
                   ancestor_id integer,
                   hierarchy_level integer,
                   foreign key(id) references fma(id))""")


    hierarchy_map = {}
    for i in parent_map.iterkeys():
        h = []
        p = parent_map[i]
        while parent_map.has_key(p):
            h.append(p)
            p = parent_map[p]
        hierarchy_map[i] = h

    for i, h in hierarchy_map.iteritems():
        db.executemany("""insert or ignore into hierarchy
                       (id, ancestor_id, hierarchy_level) values (?,?,?)""",
                       ((i, x, lev) for lev, x in enumerate(h, 1)))

    db.commit()

if __name__ == '__main__':
    dbfilename = sys.argv[1]
    build_hierarchy(dbfilename)
