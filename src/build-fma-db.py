import sys
import csv
import apsw as sqlite3


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
    'Class ID': None,
    'Preferred Label': 'preferred_label',  # 0
    'Synonyms': 'synonyms',  # 1
    'Definitions': 'definitions',  # 2
    'Obsolete': None,
    'Parents': 'parent_id',  # 3
    'AAL': 'aal',  # 4
    'CMA label': 'cma_label',  # 5
    'definition': None,
    'DK  Freesurfer': 'dk_freesurfer',  # 6
    'Eponym': None,
    'FMAID': 'id',  # 7
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


def filterColumns(c):
    return (c[7], c[0], c[3], c[4], c[5], c[6], c[8], c[9], c[10], c[12], c[13])


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
            outRow = []
            for i, r in enumerate(row):
                if accum[i] and newHeaders[i] != None:
                    outRow.append(transformElement(newHeaders[i], r))
            outputRows.append(outRow)
    outputHeaders = [x for x in newHeaders if x != None]
    return outputHeaders, outputRows


def writedb(dbfile, headers, rows):
    db = sqlite3.Connection(dbfile)
    cur = db.cursor()
    cur.execute('''create table if not exists fma
        (id text NOT NULL PRIMARY KEY,
         preferred_label text,
         parent_id text,
         aal text,
         cma_label text,
         dk_freesurfer text,
         jhu_dti_81 text,
         jhu_wmta text,
         neurolex text,
         radlex_id text,
         talairach text)''')
    cur.execute('''create table if not exists synonyms
        (id text,
        preferred_label text,
        synonym text,
        synonym_type text,
        lang text)''')
    cur.execute('''create table if not exists definitions
        (id text,
        preferred_label text,
        definition text,
        lang text)''')

    # cur.execute('''create virtual table syn_fts
    #            using fts5(preferred_label, synonyms, id unindexed,
    #            prefix=2, prefix=3)''')

    cur.executemany(u'''insert or ignore into fma (
            id, preferred_label, parent_id, aal, cma_label, dk_freesurfer, 
            jhu_dti_81, jhu_wmta, neurolex, radlex_id, talairach) values
            (?,?,?,?,?,?,?,?,?,?,?)''', (filterColumns(r) for r in rows))

    for r in rows:
        fmaid = r[7]

        syntable = [(fmaid, r[0].strip(), u'preferred_label', 'en')]
        synonyms = r[1].decode('latin-1')
        if synonyms:
            syntable += [(fmaid, s.strip(), u'synonym', None) for s in
                         synonyms.split(u'|')]

        nee = r[11].decode('latin-1')
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

        defs = r[2].decode('latin-1')
        if defs:
            defstable = [(fmaid, r[0], d.strip()) for d in defs.split(u'|')]
            cur.executemany(u'''insert or ignore into definitions
                (id, preferred_label, definition) values (?,?,?)''', defstable)
    cur.close()


if __name__ == '__main__':
    headers, rows = extractData(sys.argv[1])
    writedb(sys.argv[2], headers, rows)
