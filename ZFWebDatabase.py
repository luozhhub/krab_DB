#!/usr/bin/python
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, func, Float
from sqlalchemy import create_engine, Table
from sqlalchemy import ForeignKey
from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session

Base = declarative_base()

_schemaname_ = "public"


# table 1
class Znf(Base):
    __tablename__ = 'znf'
    # __table_args__ = {'schema': _schemaname_}

    id = Column(Integer, primary_key=True)

    ensembl = Column(String, index=True)
    entrez_id = Column(String)
    gene_symbol = Column(String, unique=True, index=True)
    species = Column(String)
    family = Column(String)
    proteins = Column(String)
    gene_synonym = Column(String)
    unipro_feature = Column(String)
    protein_names = Column(String)
    zinc_finger = Column(String)
    date_created = Column(DateTime, default=func.now())
    date_updated = Column(DateTime)

    UniqueConstraint('ensemble', name='znf_ensemble')

    # for table 2
    chip_data = relationship("Chip_data", backref="znf", cascade='all,delete,delete-orphan')
    # for table 3
    repeat = relationship('Repeat', secondary='znf_repeat', backref='znf')
    # for table 6
    repeat_region = relationship("Repeat_region", backref="znf", secondary='znf_repeatRegion')
    # for peaks
    peaks = relationship("Peaks", backref="znf", cascade='all,delete,delete-orphan')

    def __repr__(self):
        return "<Znf(id=%s, entrez_id='%s', gene_ensembl='%s')>" % \
               (self.id, self.entrez_id, self.gene_ensembl)


# table 2
class Chip_data(Base):
    __tablename__ = 'chip_data'
    # __table_args__ = {'schema': _schemaname_}

    id = Column(Integer, primary_key=True)
    data_name = Column(String, unique=True)
    data_source = Column(String)
    repeat_number = Column(Integer)
    peak_number = Column(Integer)

    date_created = Column(DateTime, default=func.now())
    date_updated = Column(DateTime)
    znf_gene_symbol = Column(String, ForeignKey('znf.gene_symbol'))

    UniqueConstraint('data_name', name='data_name')

    # for repeat table 3
    repeat = relationship('Repeat', secondary='chip_data_repeat', backref='chip_data')

    # for table 5
    peaks = relationship('Peaks', backref='chip_data', cascade='all,delete,delete-orphan')
    # for table 7
    motif = relationship("Motif", backref="chip_data", cascade='all,delete,delete-orphan', uselist=False)
    #repeat_region
    repeat_region = relationship("Repeat_region", backref="chip_data", secondary='chipData_repeatRegion')

    def __repr__(self):
        return "<Chip_data(id=%s, data_name='%s', data_source='%s', peaks='%s')>" % \
               (self.id, self.data_name, self.data_source, self.peaks)


# table 1 many-to-many table 3
Znf_repeat = Table(
    'znf_repeat', Base.metadata,
    Column('znf_id', Integer, ForeignKey('znf.id')),
    Column('repeat_id', Integer, ForeignKey('repeat.id'))
    # schema='public'
)

Chip_data_repeat = Table(
    'chip_data_repeat', Base.metadata,
    Column('chip_data_id', Integer, ForeignKey('chip_data.id')),
    Column('repeat_id', Integer, ForeignKey('repeat.id'))
    # schema='public'
)


# table 3
class Repeat(Base):
    __tablename__ = 'repeat'
    # __table_args__ = {'schema': _schemaname_}

    id = Column(Integer, primary_key=True)
    repeat_name = Column(String, unique=True)
    sub_family = Column(String)
    main_family = Column(String)
    znf_number = Column(Integer)
    date_created = Column(DateTime, default=func.now())
    date_updated = Column(DateTime)

    UniqueConstraint('repeat_name', name='repeat_name')

    # for table 4
    repeat_family = relationship("Repeat_family", backref="repeat", cascade='all,delete,delete-orphan', uselist=False)
    # for table 6
    repeat_region = relationship('Repeat_region', backref='repeat')
    # for table 1
    # znf = relationship('ZNF', secondary='znf_repeat', backref='Repeat')
    peaks = relationship("Peaks", backref="repeat", cascade='all,delete,delete-orphan')

    def __repr__(self):
        return "<Repeat(id=%s, repeat_name='%s')>" % \
               (self.id, self.repeat_name)


# table 4
class Repeat_family(Base):
    __tablename__ = 'repeat_family'
    # __table_args__ = {'schema': _schemaname_}

    id = Column(Integer, primary_key=True)
    repeat_name = Column(String)
    sub_family = Column(String)
    main_family = Column(String)
    date_created = Column(DateTime, default=func.now())
    date_updated = Column(DateTime)
    repeat_id = Column(Integer, ForeignKey('repeat.id'))

    def __repr__(self):
        return "<Repeat_family(id=%s, repeat_name='%s', sub_family='%s', main_family='%s')>" % \
               (self.id, self.repeat_name, self.sub_family, self.main_family)


"""
#table 2 and table 5
ChipData_peak = Table(
    'chipData_peak', Base.metadata,
    Column('chipData_id', Integer, ForeignKey('chip_data.id')),
    Column('peak_id', Integer, ForeignKey('peaks.id'))
    #schema='public'
)
"""


# table 5
class Peaks(Base):
    __tablename__ = 'peaks'
    # __table_args__ = {'schema': _schemaname_}

    id = Column(Integer, primary_key=True)
    chr = Column(String)
    start = Column(Integer)
    end = Column(Integer)
    strand = Column(String)
    enrichment = Column(Float)
    ensembl = Column(String, index=True)

    # repeat_name = Column(String, index=True)
    repeat_repeat_name = Column(String, ForeignKey('repeat.repeat_name'), index=True)
    znf_gene_symbol = Column(String, ForeignKey('znf.gene_symbol'))
    chip_data_data_name = Column(String, ForeignKey('chip_data.data_name'))

    date_created = Column(DateTime, default=func.now())
    date_updated = Column(DateTime)

    UniqueConstraint('chr', 'start', 'end', 'strand', 'enrichment', name='peaks_all_data')

    def __repr__(self):
        return "<Peaks(id=%s, chr='%s', start='%s', end='%s')>" % \
               (self.id, self.chr, self.start, self.end)

"""
# for table 3 and table 6
Repeat_repeatRegion = Table(
    'repeat_repeatRegion', Base.metadata,
    Column('repeat_id', Integer, ForeignKey('repeat.id')),
    Column('repeatRegion_id', Integer, ForeignKey('repeat_region.id'))
    # schema='public'
)
"""

# table 1 and table 6
Znf_repeatRegion = Table(
    'znf_repeatRegion', Base.metadata,
    Column('znf_id', Integer, ForeignKey('znf.id')),
    Column('repeatRegion_id', Integer, ForeignKey('repeat_region.id'))
    # schema='public'
)

ChipData_repeatRegion = Table(
    'chipData_repeatRegion', Base.metadata,
    Column('chip_data_id', Integer, ForeignKey('chip_data.id')),
    Column('repeatRegion_id', Integer, ForeignKey('repeat_region.id'))
    # schema='public'
)


# table 6
class Repeat_region(Base):
    __tablename__ = 'repeat_region'
    # __table_args__ = {'schema': _schemaname_}

    id = Column(Integer, primary_key=True)
    chr = Column(String)
    start = Column(Integer)
    end = Column(Integer)
    strand = Column(String)
    date_created = Column(DateTime, default=func.now())
    date_updated = Column(DateTime)

    repeat_repeat_name = Column(String, ForeignKey('repeat.repeat_name'))
    #znf_id = Column(Integer, ForeignKey('znf.id'))


    #

    def __repr__(self):
        return "<Repeat_region(id=%s, chr='%s', start='%s', end='%s')>" % \
               (self.id, self.chr, self.start, self.end)


# table 7
class Motif(Base):
    __tablename__ = 'motif'
    # __table_args__ = {'schema': _schemaname_}

    id = Column(Integer, primary_key=True)
    znf_all_motif_img_path = Column(String)
    znf_all_motif_matrix_path = Column(String)
    znf_full_motif_img_path = Column(String)
    znf_full_motif_matrix_path = Column(String)
    znf_part_motif_img_path = Column(String)
    znf_part_motif_matrix_path = Column(String)
    znf_None_motif_img_path = Column(String)
    znf_None_motif_matrix_path = Column(String)
    date_created = Column(DateTime, default=func.now())
    date_updated = Column(DateTime)
    chip_data_id = Column(Integer, ForeignKey('chip_data.id'))

    def __repr__(self):
        return "<Motif(id=%s)>" % \
               (self.id)


# append data
"""
class C2H2(Base):
    __tablename__ = 'c2h2'
    #__table_args__ = {'schema': _schemaname_}
    #Species Symbol  Ensembl Family  Protein Entrez ID

    id = Column(Integer, primary_key=True)
    species = Column(String)
    gene_symbol = Column(String)
    ensembl = Column(String)
    entrez = Column(Integer)

    date_created = Column(DateTime, default=func.now())
    date_updated = Column(DateTime)

    # for table C2H2
    znf = relationship('Znf', backref="c2h2", cascade='all,delete,delete-orphan')


    def __repr__(self):
        return "<Motif(id=%s, species=%s, gene_symbol=%s, ensembl=%s, entrez=%s)>" % \
               (self.id, self.species, self.gene_symbol, self.ensembl, self.entrez)
"""


class Expression(Base):
    __tablename__ = 'expression'

    id = Column(Integer, primary_key=True)
    ensembl = Column(String, index=True)
    project = Column(String)
    expression = Column(String)
    date_created = Column(DateTime, default=func.now())
    date_updated = Column(DateTime)

    def __repr__(self):
        return "<Expression(id=%s, ensembl='%s', project='%s')>" % \
               (self.id, self.ensembl, self.project)


class Gene_structure(Base):
    __tablename__ = 'gene_structure'

    id = Column(Integer, primary_key=True)
    ensembl = Column(String, index=True)
    structure = Column(String)
    date_created = Column(DateTime, default=func.now())
    date_updated = Column(DateTime)

    def __repr__(self):
        return "<Gene_structure(id=%s, ensembl='%s', structure='%s')>" % \
               (self.id, self.ensembl, self.structure)


class Cell_line(Base):
    __tablename__ = 'cell_line'

    id = Column(Integer, primary_key=True)
    project = Column(String)
    cell = Column(String)
    date_created = Column(DateTime, default=func.now())
    date_updated = Column(DateTime)

    def __repr__(self):
        return "<Cell_line(id=%s, cell='%s', project='%s')>" % \
               (self.id, self.cell, self.project)


class Orthologs(Base):
    __tablename__ = 'orthologs'

    id = Column(Integer, primary_key=True)
    ensembl = Column(String, index=True)
    Scientific_name = Column(String)
    ortholog_external_gene_name = Column(String)
    ortholog = Column(String)
    homolog_perc_id = Column(String)
    homolog_perc_id_r1 = Column(String)
    homolog_wga_coverage = Column(String)
    homolog_orthology_confidence = Column(String)

    date_created = Column(DateTime, default=func.now())
    date_updated = Column(DateTime)

    def __repr__(self):
        return "<Orthologs(id=%s, ensembl='%s', ortholog='%s')>" % \
               (self.id, self.ensembl, self.ortholog)

    def returnDict(self):
        return {"Ensembl": self.ensembl, "Scientific_name": self.Scientific_name,
                "ortholog_external_gene_name": self.ortholog_external_gene_name, \
                "ortholog": self.ortholog, "homolog_perc_id": self.homolog_perc_id,
                "homolog_perc_id_r1": self.homolog_perc_id_r1,
                "homolog_wga_coverage": self.homolog_wga_coverage,
                "homolog_orthology_confidence": self.homolog_orthology_confidence
                }


class AccurityWebDB():
    def __init__(self, user, password, database, driver="postgresql", hostname=None, port=5432):
        self.user = user
        self.password = password
        self.host = hostname
        self.port = port
        self.database = database
        self.driver = driver
        self.session = None

    def Connect(self):
        url = "%s://%s:%s@%s:%s/%s" % (self.driver, self.user, self.password, self.host, self.port, self.database)
        self.engine = create_engine(url, pool_recycle=3600, echo=False)
        return self.engine

    def CreateAllTable(self):
        Base.metadata.create_all(self.engine)

    # @property
    def SessionUp(self):
        if self.session is None:
            Session = scoped_session(sessionmaker(autoflush=False, autocommit=False, bind=self.engine))
            self.session = Session()
        return self.session

    def SessionDown(self):
        self.session.close()

    def getZnf(self, ensembl=None, gene_symbol=None, entrez_id=None, species=None, family=None, \
               proteins=None, gene_synonym=None, unipro_feature=None):

        znf_item = self.session.query(Znf).filter_by(ensembl=ensembl).first()
        if znf_item is None:
            return Znf(ensembl=ensembl, gene_symbol=gene_symbol, entrez_id=entrez_id, species=species, family=family, \
                       proteins=proteins, gene_synonym=gene_synonym, unipro_feature=unipro_feature)
        else:
            return znf_item

    def getChip_data(self, data_name=None, data_source=None, repeat_number=None, peak_number=None):
        chip_data_item = self.session.query(Chip_data).filter_by(data_name=data_name).first()
        # if no_duplicate is True and chip_data_item is not None:
        #    return None
        if chip_data_item is None:
            return Chip_data(data_name=data_name, data_source=data_source, repeat_number=repeat_number, \
                             peak_number=peak_number)
        else:
            return chip_data_item

    def getRepeat(self, repeat_name=None, sub_family=None, main_family=None):
        repeat_item = self.session.query(Repeat).filter_by(repeat_name=repeat_name).first()
        # print(repeat_item)
        # if no_duplicate is True and repeat_item is not None:
        #    return None
        if repeat_item is None:
            return Repeat(repeat_name=repeat_name, sub_family=sub_family, main_family=main_family)
        else:
            return repeat_item

    def getPeaks(self, chr=None, start=None, end=None, strand=None, enrichment=None, ensembl=None):
        peaks_item = self.session.query(Peaks).filter_by(chr=chr, start=start, end=end, strand=strand,
                                                         enrichment=enrichment, ensembl=ensembl).first()
        # if no_duplicate is True and peaks_item is not None:
        #    return None
        if peaks_item is None:
            return Peaks(chr=chr, start=start, end=end, strand=strand, enrichment=enrichment, ensembl=ensembl)
        else:
            return peaks_item

    def getRepeat_family(self, repeat_name=None, sub_family=None, main_family=None, no_duplicate=True):
        repeat_family_item = self.session.query(Repeat_family).filter_by(repeat_name=repeat_name, sub_family=sub_family,
                                                                         main_family=main_family).first()
        # if no_duplicate is True and repeat_family_item is not None:
        #    return None
        if repeat_family_item is None:
            return Repeat_family(repeat_name=repeat_name, sub_family=sub_family, main_family=main_family)
        else:
            return repeat_family_item

    def getRepeat_region(self, chr=None, start=None, end=None, strand=None, no_duplicate=True):
        repeat_region_item = self.session.query(Repeat_region).filter_by(chr=chr, start=start, end=end,
                                                                         strand=strand).first()
        if repeat_region_item is None:
            return Repeat_region(chr=chr, start=start, end=end, strand=strand)
        else:
            return repeat_region_item

    def getC2H2(self, species=None, gene_symbol=None, ensembl=None, entrez=None):
        c2h2_item = self.session.query(C2H2).filter_by(gene_symbol=gene_symbol, species=species, ensembl=ensembl,
                                                       entrez=entrez).first()
        # if no_duplicate is True and znf_item is not None:
        #    return None
        if c2h2_item is None:
            return C2H2(gene_symbol=gene_symbol, species=species, ensembl=ensembl, entrez=entrez)
        else:
            return c2h2_item

    def dropAll(self):
        Base.metadata.drop_all(self.engine)


if __name__ == '__main__':
    """
    import argparse


    parser = argparse.ArgumentParser()
    parser.add_argument('-u','--user',help='name of user')
    parser.add_argument('-t','--host',default='localhost',help='host name of database. Default: localhost')
    parser.add_argument('-d','--database',help='name of database')
    parser.add_argument('-s','--schema',help='name of schema')
    parser.add_argument('-p','--password',help='password of user')
    parser.add_argument('-v','--driver',default='postgresql',help='driver used by database. Default: postgresql')

    args = parser.parse_args()
    db = AccurityWebDB(user=args.user, password=args.password, database=args.database, driver=args.driver, hostname=args.host)
    """
    db = AccurityWebDB(user="luozh", password="luozh123", database="ZNFdb", hostname="localhost")
    db.Connect()
    db.CreateAllTable()
# db.SessionUp()
