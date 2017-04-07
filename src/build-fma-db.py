import sys
import csv
import sqlite3


def countEls(x, y):
    if x == None:
        x = 0
    return x + 1 if y != '' else x


def transformHeaders(headers):
    return [HeaderMapping.get(h, None) for h in headers]


def transformElement(h, v):
    v = v.replace('http://purl.org/sig/ont/fma/fma', '')
    if h in ('id', 'parent_id'):
        v = '%s' % (v,)
    return v

HeaderMapping = {
    'Class ID': 'id',  # 0
    'Preferred Label': 'preferred_label',  # 1
    'Synonyms': 'synonyms',  # 2
    'Definitions': 'definitions',  # 3
    'Obsolete': None,
    'Parents': 'parent_id',  # 4
    'AAL': 'aal',  # 5
    'CMA label': 'cma_label',  # 6
    'definition': None,
    'DK  Freesurfer': 'dk_freesurfer',  # 7
    'Eponym': None,
    'FMAID': None,
    'homonym for': None,
    'http://data.bioontology.org/metadata/prefixIRI': None,
    'JHU DTI-81': 'jhu_dti_81',  # 8
    'JHU White-Matter Tractography Atlas': 'jhu_wmta',  # 9
    'Neurolex': 'neurolex',  # 10
    'non-English equivalent': 'non_english_equivalent',  # 11
    'PI-RADS v1 16 ID 16': None,
    'PI-RADS v1 27 ID 24': None,
    'PI-RADS v2 ID 34': None,
    'preferred name': None,
    'RadLex ID': 'radlex_id',  # 12
    'slot synonym': None,
    'synonym': None,
    'Talairach': 'talairach'  # 13
}


def intMaybe(i):
    if not i:
        return None
    try:
        inti = int(i)
    except ValueError:
        return None
    return inti

def filterColumns(c):
    v = (int(c[0]), c[1], intMaybe(c[4]), intMaybe(c[5]))
    return v


def extractData(csvfile):
    with open(csvfile, 'rU') as fp:
        reader = csv.reader(fp)
        headers = reader.next()
        accum = []
        for row in reader:
            accum = map(countEls, accum, row)

    outputRows = []
    newHeaders = transformHeaders(headers)
    with open(csvfile, 'rU') as fp:
        reader = csv.reader(fp)
        writer = csv.writer(sys.stdout)
        reader.next()
        for row in reader:
            if not row[0].startswith('http://purl.org/sig/ont/fma/fma'):
                continue
            outRow = []
            for i, r in enumerate(row):
                if accum[i] and newHeaders[i] != None:
                    outRow.append(transformElement(newHeaders[i], r))
            outputRows.append(outRow)
    outputHeaders = [x for x in newHeaders if x != None]
    return outputHeaders, outputRows


def writedb(dbfile, headers, rows):
    db = sqlite3.connect(dbfile)
    cur = db.cursor()
    cur.execute('''create table if not exists fma
        (id integer NOT NULL PRIMARY KEY,
         name text,
         parent_id integer,
         aal integer)''')
    cur.execute('''create table if not exists synonyms
        (id integer NOT NULL,
        name text,
        synonym text,
        synonym_type text,
        lang text,
        foreign key(id) references fma(id))''')
    cur.execute('''create table if not exists definitions
        (id integer NOT NULL,
        name text,
        definition text,
        lang text)''')
    cur.execute("""create table if not exists fma_dk_freesurfer
        (id integer NOT NULL,
        dk_freesurfer integer NOT NULL,
        foreign key(id) references fma(id))""")
    cur.execute("""create table if not exists fma_talairach
        (id integer NOT NULL,
        talairach integer NOT NULL,
        foreign key(id) references fma(id))""")

    # cur.execute('''create virtual table syn_fts
    #            using fts5(preferred_label, synonyms, id unindexed,
    #            prefix=2, prefix=3)''')

    cur.executemany(u'''insert or ignore into fma (
            id, name, parent_id, aal) values
            (?,?,?,?)''', (filterColumns(r) for r in rows))
    db.commit()

    for r in rows:
        fmaid = int(r[0])

        syntable = [(fmaid, r[0].strip(), u'preferred_label', 'en')]
        synonyms = r[2].decode('latin-1')
        defs = r[3].decode('latin-1')
        nee = r[11].decode('latin-1')
        dk_freesurfer = r[7].decode('latin-1')
        talairach = r[13].decode('latin-1')

        if synonyms:
            syntable += [(fmaid, s.strip(), u'synonym', None) for s in
                         synonyms.split(u'|')]

        if nee:
            syntable += [(fmaid, r[0], n.strip(), u'non_english_equivalent') for n in
                         nee.split(u'|')]

        cur.executemany(u'''insert or ignore into synonyms
            (id, synonym, synonym_type, lang) values (?,?, ?,?)''', syntable)

        synstring = '%s %s' % (nee.replace(u'|', u' '),
                               synonyms.replace(u'|', ' '))
        # cur.execute(u'''insert into syn_fts
        #                   (preferred_label, synonyms, id)
        #                    values (?,?,?)''', (r[0], synstring, fmaid))

        if defs:
            defstable = [(fmaid, r[0], d.strip()) for d in defs.split(u'|')]
            cur.executemany(u'''insert or ignore into definitions
                (id, name, definition) values (?,?,?)''', defstable)

        if dk_freesurfer:
            fstable = [(fmaid, int(d.strip()))
                       for d in dk_freesurfer.split(u'|')]
            cur.executemany(u'''insert or ignore into fma_dk_freesurfer
                (id, dk_freesurfer) values (?,?)''', fstable)

        if talairach:
            ttable = [(fmaid, int(t.strip())) for t in talairach.split(u'|')]
            cur.executemany(u'''insert or ignore into fma_talairach
                (id, talairach) values (?,?)''', ttable)
    cur.close()
    db.commit()

if __name__ == '__main__':
    headers, rows = extractData(sys.argv[1])
    writedb(sys.argv[2], headers, rows)
