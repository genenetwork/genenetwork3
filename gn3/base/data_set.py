
import json
import requests
from redis import Redis
from flask import g
from gn3.correlation.correlation_utility import AttributeSetter
from gn3.utility.db_tools import escape
from gn3.db.calls import fetch1
from gn3.db.calls import fetchone
from gn3.db.webqtlDatabaseFunction import retrieve_species
from gn3.base.species import TheSpecies
r = Redis()

USE_REDIS =True
# move  this to configuration file
GN2_BASE_URL = "https://genenetwork.org/"

DS_NAME_MAP = {}


def create_dataset(dataset_name, dataset_type=None, get_samplelist=True, group_name=None):
    print("DS_NAME_MAP is >>>>>>>>>>>", DS_NAME_MAP)
    # DATASET NAME IS HC_M2_0606_P the dataset_type is None and group_name is None

    # add this valid data for testing

    dataset_type = None

    group_name = None

    # end

    if dataset_name == "Temp":
        dataset_type = "Temp"

    dataset_name = "HC_M2_0606_P"
    dataset_type = None

    if dataset_type is None:
        dataset_type = Dataset_Getter(dataset_name)
    dataset_ob = DS_NAME_MAP[dataset_type]
    dataset_class = globals()[dataset_ob]

    print(f"the class being waiting for is {dataset_class}")
    # results = None

    if dataset_type == "Temp":
        results = dataset_class(dataset_name, get_samplelist, group_name)

    else:
        results = dataset_class(dataset_name, get_samplelist)

    dataset = AttributeSetter({
        "group": AttributeSetter({
            "genofile": "",
            "samplelist": "S1",
            "parlist": "",
            "f1list": ""


        })
    })

    print("5555555555555555555555555555",results.group.name)

    # return dataset
    return results

    # return "hello"


class DatasetType:
    def __init__(self, redis_instance):
        self.redis_instance = redis_instance
        self.datasets = {}

        data = self.redis_instance.get("dataset_structure")
        if data:
            self.datasets = json.loads(data)

        else:

            try:

                data = json.loads(requests.get(
                    GN2_BASE_URL + "/api/v_pre1/gen_dropdown", timeout=5).content)

                # todo:Refactor code below n^4 loop

                for species in data["datasets"]:
                    for group in data["datasets"][species]:
                        for dataset_type in data['datasets'][species][group]:
                            for dataset in data['datasets'][species][group][dataset_type]:

                                short_dataset_name = dataset[1]
                                if dataset_type == "Phenotypes":
                                    new_type = "Publish"

                                elif dataset_type == "Genotypes":
                                    new_type = "Geno"
                                else:
                                    new_type = "ProbeSet"

                                self.datasets[short_dataset_name] = new_type

            except Exception as e:
                raise e

            self.redis_instance.set(
                "dataset_structure", json.dumps(self.datasets))

    def set_dataset_key(self, t, name):
        """If name is not in the object's dataset dictionary, set it, and update
    dataset_structure in Redis

    args:
      t: Type of dataset structure which can be: 'mrna_expr', 'pheno',
         'other_pheno', 'geno'
      name: The name of the key to inserted in the datasets dictionary

    """
        print("CALLING IN THIS FUNCTION HERE>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")

        sql_query_mapping = {
            'mrna_expr': ("""SELECT ProbeSetFreeze.Id FROM """ +
                          """ProbeSetFreeze WHERE ProbeSetFreeze.Name = "{}" """),
            'pheno': ("""SELECT InfoFiles.GN_AccesionId """ +
                      """FROM InfoFiles, PublishFreeze, InbredSet """ +
                      """WHERE InbredSet.Name = '{}' AND """ +
                      """PublishFreeze.InbredSetId = InbredSet.Id AND """ +
                      """InfoFiles.InfoPageName = PublishFreeze.Name"""),
            'other_pheno': ("""SELECT PublishFreeze.Name """ +
                            """FROM PublishFreeze, InbredSet """ +
                            """WHERE InbredSet.Name = '{}' AND """ +
                            """PublishFreeze.InbredSetId = InbredSet.Id"""),
            'geno':  ("""SELECT GenoFreeze.Id FROM GenoFreeze WHERE """ +
                      """GenoFreeze.Name = "{}" """)
        }

        dataset_name_mapping = {
            "mrna_expr": "ProbeSet",
            "pheno": "Publish",
            "other_pheno": "Publish",
            "geno": "Geno",
        }

        group_name = name
        if t in ['pheno', 'other_pheno']:
            group_name = name.replace("Publish", "")

        results = g.db.execute(
            sql_query_mapping[t].format(group_name)).fetchone()
        if results:
            self.datasets[name] = dataset_name_mapping[t]
            self.redis_instance.set(
                "dataset_structure", json.dumps(self.datasets))

            return True

        return None

    def __call__(self, name):
        if name not in self.datasets:
            for t in ["mrna_expr", "pheno", "other_pheno", "geno"]:

                if(self.set_dataset_key(t, name)):
                    # This has side-effects, with the end result being a truth-y value
                    break

        print(f"return values is &&&&&&&&&&&&&&&&& {self.datasets.get(name, None)}")

        return self.datasets.get(name, None)


        # Do the intensive work at  startup one time only
Dataset_Getter = DatasetType(r)


class DatasetGroup:
    """
    Each group has multiple datasets; each species has multiple groups.

    For example, Mouse has multiple groups (BXD, BXA, etc), and each group
    has multiple datasets associated with it.

    """

    def __init__(self, dataset, name=None):
        """This sets self.group and self.group_id"""
        if name == None:
            self.name, self.id, self.genetic_type = fetchone(
                dataset.query_for_group)

        else:
            self.name, self.id, self.genetic_type = fetchone(
                "SELECT InbredSet.Name, InbredSet.Id, InbredSet.GeneticType FROM InbredSet where Name='%s'" % name)

        if self.name == 'BXD300':
            self.name = "BXD"

        self.f1list = None

        self.parlist = None

        self.get_f1_parent_strains()

        # not sure whether is used in correlation

        self.mapping_id, self.mapping_names = self.get_mapping_methods()

        self.species = retrieve_species(self.name)

    def get_f1_parent_strains(self):
        try:
            # should import ParInfo
            raise e
            # NL, 07/27/2010. ParInfo has been moved from webqtlForm.py to webqtlUtil.py;
            f1, f12, maternal, paternal = webqtlUtil.ParInfo[self.name]
        except Exception as e:
            f1 = f12 = maternal = paternal = None

        if f1 and f12:
            self.f1list = [f1, f12]

        if maternal and paternal:
            self.parlist = [maternal, paternal]

    def get_mapping_methods(self):
        mapping_id = g.db.execute(
            "select MappingMethodId from InbredSet where Name= '%s'" % self.name).fetchone()[0]

        if mapping_id == "1":
            mapping_names = ["GEMMA", "QTLReaper", "R/qtl"]
        elif mapping_id == "2":
            mapping_names = ["GEMMA"]

        elif mapping_id == "3":
            mapping_names = ["R/qtl"]

        elif mapping_id == "4":
            mapping_names = ["GEMMA", "PLINK"]

        else:
            mapping_names = []

        return mapping_id, mapping_names

    def get_samplelist(self):
        result = None
        key = "samplelist:v3:" + self.name
        if USE_REDIS:
            result = r.get(key)

        if result is not None:

            self.samplelist = json.loads(result)

        else:
            # logger.debug("Cache not hit")
            # should enable logger

            def locate_ignore_error(name, subdir=None):
                # work on this
                return None
            genotype_fn = locate_ignore_error(self.name+".geno", 'genotype')
            if genotype_fn:
                self.samplelist = get_group_samplelists.get_samplelist(
                    "geno", genotype_fn)

            else:
                self.samplelist = None


            if USE_REDIS:
                r.set(key, json.dumps(self.samplelist))
                r.expire(key, 60*5)







class DataSet:
    """
    DataSet class defines a dataset in webqtl, can be either Microarray,
    Published phenotype, genotype, or user input dataset(temp)

    """

    def __init__(self, name, get_samplelist=True, group_name=None):

        assert name, "Need a name"
        self.name = name
        self.id = None
        self.shortname = None
        self.fullname = None
        self.type = None
        self.data_scale = None  # ZS: For example log2

        self.setup()

        if self.type == "Temp":  # Need to supply group name as input if temp trait
            # sets self.group and self.group_id and gets genotype
            self.group = DatasetGroup(self, name=group_name)
        else:
            self.check_confidentiality()
            self.retrieve_other_names()
            # sets self.group and self.group_id and gets genotype
            self.group = DatasetGroup(self)
            self.accession_id = self.get_accession_id()
        if get_samplelist == True:
            self.group.get_samplelist()
        self.species = TheSpecies(self)

    def get_desc(self):
        """Gets overridden later, at least for Temp...used by trait's get_given_name"""
        return None

    # Delete this eventually
    @property
    def riset():
        Weve_Renamed_This_As_Group

    def get_accession_id(self):
        if self.type == "Publish":
            results = g.db.execute("""select InfoFiles.GN_AccesionId from InfoFiles, PublishFreeze, InbredSet where
                        InbredSet.Name = %s and
                        PublishFreeze.InbredSetId = InbredSet.Id and
                        InfoFiles.InfoPageName = PublishFreeze.Name and
                        PublishFreeze.public > 0 and
                        PublishFreeze.confidentiality < 1 order by
                        PublishFreeze.CreateTime desc""", (self.group.name)).fetchone()
        elif self.type == "Geno":
            results = g.db.execute("""select InfoFiles.GN_AccesionId from InfoFiles, GenoFreeze, InbredSet where
                        InbredSet.Name = %s and
                        GenoFreeze.InbredSetId = InbredSet.Id and
                        InfoFiles.InfoPageName = GenoFreeze.ShortName and
                        GenoFreeze.public > 0 and
                        GenoFreeze.confidentiality < 1 order by
                        GenoFreeze.CreateTime desc""", (self.group.name)).fetchone()
        else:
            results = None

        if results != None:
            return str(results[0])
        else:
            return "None"

    def retrieve_other_names(self):
        """This method fetches the the dataset names in search_result.

        If the data set name parameter is not found in the 'Name' field of
        the data set table, check if it is actually the FullName or
        ShortName instead.

        This is not meant to retrieve the data set info if no name at
        all is passed.

        """

        try:
            if self.type == "ProbeSet":
                query_args = tuple(escape(x) for x in (
                    self.name,
                    self.name,
                    self.name))

                self.id, self.name, self.fullname, self.shortname, self.data_scale, self.tissue = fetch1("""
    SELECT ProbeSetFreeze.Id, ProbeSetFreeze.Name, ProbeSetFreeze.FullName, ProbeSetFreeze.ShortName, ProbeSetFreeze.DataScale, Tissue.Name
    FROM ProbeSetFreeze, ProbeFreeze, Tissue
    WHERE ProbeSetFreeze.ProbeFreezeId = ProbeFreeze.Id
    AND ProbeFreeze.TissueId = Tissue.Id
    AND (ProbeSetFreeze.Name = '%s' OR ProbeSetFreeze.FullName = '%s' OR ProbeSetFreeze.ShortName = '%s')
                """ % (query_args), "/dataset/"+self.name+".json",
                    lambda r: (r["id"], r["name"], r["full_name"],
                               r["short_name"], r["data_scale"], r["tissue"])
                )
            else:
                query_args = tuple(escape(x) for x in (
                    (self.type + "Freeze"),
                    self.name,
                    self.name,
                    self.name))

                self.tissue = "N/A"
                self.id, self.name, self.fullname, self.shortname = fetchone("""
                        SELECT Id, Name, FullName, ShortName
                        FROM %s
                        WHERE (Name = '%s' OR FullName = '%s' OR ShortName = '%s')
                    """ % (query_args))

        except TypeError as e:
            logger.debug(
                "Dataset {} is not yet available in GeneNetwork.".format(self.name))
            pass

    def get_trait_data(self, sample_list=None):
        if sample_list:
            self.samplelist = sample_list
        else:
            self.samplelist = self.group.samplelist

        if self.group.parlist != None and self.group.f1list != None:
            if (self.group.parlist + self.group.f1list) in self.samplelist:
                self.samplelist += self.group.parlist + self.group.f1list

        query = """
            SELECT Strain.Name, Strain.Id FROM Strain, Species
            WHERE Strain.Name IN {}
            and Strain.SpeciesId=Species.Id
            and Species.name = '{}'
            """.format(create_in_clause(self.samplelist), *mescape(self.group.species))
        logger.sql(query)
        results = dict(g.db.execute(query).fetchall())
        sample_ids = [results[item] for item in self.samplelist]

        # MySQL limits the number of tables that can be used in a join to 61,
        # so we break the sample ids into smaller chunks
        # Postgres doesn't have that limit, so we can get rid of this after we transition
        chunk_size = 50
        number_chunks = int(math.ceil(len(sample_ids) / chunk_size))
        trait_sample_data = []
        for sample_ids_step in chunks.divide_into_chunks(sample_ids, number_chunks):
            if self.type == "Publish":
                dataset_type = "Phenotype"
            else:
                dataset_type = self.type
            temp = ['T%s.value' % item for item in sample_ids_step]
            if self.type == "Publish":
                query = "SELECT {}XRef.Id,".format(escape(self.type))
            else:
                query = "SELECT {}.Name,".format(escape(dataset_type))
            data_start_pos = 1
            query += ', '.join(temp)
            query += ' FROM ({}, {}XRef, {}Freeze) '.format(*mescape(dataset_type,
                                                                     self.type,
                                                                     self.type))

            for item in sample_ids_step:
                query += """
                        left join {}Data as T{} on T{}.Id = {}XRef.DataId
                        and T{}.StrainId={}\n
                        """.format(*mescape(self.type, item, item, self.type, item, item))

            if self.type == "Publish":
                query += """
                        WHERE {}XRef.InbredSetId = {}Freeze.InbredSetId
                        and {}Freeze.Name = '{}'
                        and {}.Id = {}XRef.{}Id
                        order by {}.Id
                        """.format(*mescape(self.type, self.type, self.type, self.name,
                                            dataset_type, self.type, dataset_type, dataset_type))
            else:
                query += """
                        WHERE {}XRef.{}FreezeId = {}Freeze.Id
                        and {}Freeze.Name = '{}'
                        and {}.Id = {}XRef.{}Id
                        order by {}.Id
                        """.format(*mescape(self.type, self.type, self.type, self.type,
                                            self.name, dataset_type, self.type, self.type, dataset_type))

            results = g.db.execute(query).fetchall()
            trait_sample_data.append(results)

        trait_count = len(trait_sample_data[0])
        self.trait_data = collections.defaultdict(list)

        # put all of the separate data together into a dictionary where the keys are
        # trait names and values are lists of sample values
        for trait_counter in range(trait_count):
            trait_name = trait_sample_data[0][trait_counter][0]
            for chunk_counter in range(int(number_chunks)):
                self.trait_data[trait_name] += (
                    trait_sample_data[chunk_counter][trait_counter][data_start_pos:])


class MrnaAssayDataSet(DataSet):
    '''
    An mRNA Assay is a quantitative assessment (assay) associated with an mRNA trait

    This used to be called ProbeSet, but that term only refers specifically to the Affymetrix
    platform and is far too specific.

    '''
    DS_NAME_MAP['ProbeSet'] = 'MrnaAssayDataSet'

    def setup(self):
        # Fields in the database table
        self.search_fields = ['Name',
                              'Description',
                              'Probe_Target_Description',
                              'Symbol',
                              'Alias',
                              'GenbankId',
                              'UniGeneId',
                              'RefSeq_TranscriptId']

        # Find out what display_fields is
        self.display_fields = ['name', 'symbol',
                               'description', 'probe_target_description',
                               'chr', 'mb',
                               'alias', 'geneid',
                               'genbankid', 'unigeneid',
                               'omim', 'refseq_transcriptid',
                               'blatseq', 'targetseq',
                               'chipid', 'comments',
                               'strand_probe', 'strand_gene',
                               'proteinid', 'uniprotid',
                               'probe_set_target_region',
                               'probe_set_specificity',
                               'probe_set_blat_score',
                               'probe_set_blat_mb_start',
                               'probe_set_blat_mb_end',
                               'probe_set_strand',
                               'probe_set_note_by_rw',
                               'flag']

        # Fields displayed in the search results table header
        self.header_fields = ['Index',
                              'Record',
                              'Symbol',
                              'Description',
                              'Location',
                              'Mean',
                              'Max LRS',
                              'Max LRS Location',
                              'Additive Effect']

        # Todo: Obsolete or rename this field
        self.type = 'ProbeSet'

        self.query_for_group = '''
                        SELECT
                                InbredSet.Name, InbredSet.Id, InbredSet.GeneticType
                        FROM
                                InbredSet, ProbeSetFreeze, ProbeFreeze
                        WHERE
                                ProbeFreeze.InbredSetId = InbredSet.Id AND
                                ProbeFreeze.Id = ProbeSetFreeze.ProbeFreezeId AND
                                ProbeSetFreeze.Name = "%s"
                ''' % escape(self.name)

    def check_confidentiality(self):
        return geno_mrna_confidentiality(self)

    def get_trait_info(self, trait_list=None, species=''):

        #  Note: setting trait_list to [] is probably not a great idea.
        if not trait_list:
            trait_list = []

        for this_trait in trait_list:

            if not this_trait.haveinfo:
                this_trait.retrieveInfo(QTL=1)

            if not this_trait.symbol:
                this_trait.symbol = "N/A"

            # XZ, 12/08/2008: description
            # XZ, 06/05/2009: Rob asked to add probe target description
            description_string = str(
                str(this_trait.description).strip(codecs.BOM_UTF8), 'utf-8')
            target_string = str(
                str(this_trait.probe_target_description).strip(codecs.BOM_UTF8), 'utf-8')

            if len(description_string) > 1 and description_string != 'None':
                description_display = description_string
            else:
                description_display = this_trait.symbol

            if (len(description_display) > 1 and description_display != 'N/A' and
                    len(target_string) > 1 and target_string != 'None'):
                description_display = description_display + '; ' + target_string.strip()

            # Save it for the jinja2 template
            this_trait.description_display = description_display

            if this_trait.chr and this_trait.mb:
                this_trait.location_repr = 'Chr%s: %.6f' % (
                    this_trait.chr, float(this_trait.mb))

            # Get mean expression value
            query = (
                """select ProbeSetXRef.mean from ProbeSetXRef, ProbeSet
                where ProbeSetXRef.ProbeSetFreezeId = %s and
                ProbeSet.Id = ProbeSetXRef.ProbeSetId and
                ProbeSet.Name = '%s'
            """ % (escape(str(this_trait.dataset.id)),
                   escape(this_trait.name)))

            #logger.debug("query is:", pf(query))
            logger.sql(query)
            result = g.db.execute(query).fetchone()

            mean = result[0] if result else 0

            if mean:
                this_trait.mean = "%2.3f" % mean

            # LRS and its location
            this_trait.LRS_score_repr = 'N/A'
            this_trait.LRS_location_repr = 'N/A'

            # Max LRS and its Locus location
            if this_trait.lrs and this_trait.locus:
                query = """
                    select Geno.Chr, Geno.Mb from Geno, Species
                    where Species.Name = '{}' and
                        Geno.Name = '{}' and
                        Geno.SpeciesId = Species.Id
                """.format(species, this_trait.locus)
                logger.sql(query)
                result = g.db.execute(query).fetchone()

                if result:
                    lrs_chr, lrs_mb = result
                    this_trait.LRS_score_repr = '%3.1f' % this_trait.lrs
                    this_trait.LRS_location_repr = 'Chr%s: %.6f' % (
                        lrs_chr, float(lrs_mb))

        return trait_list

    def retrieve_sample_data(self, trait):
        query = """
                    SELECT
                            Strain.Name, ProbeSetData.value, ProbeSetSE.error, NStrain.count, Strain.Name2
                    FROM
                            (ProbeSetData, ProbeSetFreeze, Strain, ProbeSet, ProbeSetXRef)
                    left join ProbeSetSE on
                            (ProbeSetSE.DataId = ProbeSetData.Id AND ProbeSetSE.StrainId = ProbeSetData.StrainId)
                    left join NStrain on
                            (NStrain.DataId = ProbeSetData.Id AND
                            NStrain.StrainId = ProbeSetData.StrainId)
                    WHERE
                            ProbeSet.Name = '%s' AND ProbeSetXRef.ProbeSetId = ProbeSet.Id AND
                            ProbeSetXRef.ProbeSetFreezeId = ProbeSetFreeze.Id AND
                            ProbeSetFreeze.Name = '%s' AND
                            ProbeSetXRef.DataId = ProbeSetData.Id AND
                            ProbeSetData.StrainId = Strain.Id
                    Order BY
                            Strain.Name
                    """ % (escape(trait), escape(self.name))
        # logger.sql(query)
        results = g.db.execute(query).fetchall()
        #logger.debug("RETRIEVED RESULTS HERE:", results)
        return results

    def retrieve_genes(self, column_name):
        query = """
                    select ProbeSet.Name, ProbeSet.%s
                    from ProbeSet,ProbeSetXRef
                    where ProbeSetXRef.ProbeSetFreezeId = %s and
                    ProbeSetXRef.ProbeSetId=ProbeSet.Id;
                """ % (column_name, escape(str(self.id)))
        # logger.sql(query)
        results = g.db.execute(query).fetchall()

        return dict(results)


def geno_mrna_confidentiality(ob):
    dataset_table = ob.type + "Freeze"
    #logger.debug("dataset_table [%s]: %s" % (type(dataset_table), dataset_table))

    query = '''SELECT Id, Name, FullName, confidentiality,
                        AuthorisedUsers FROM %s WHERE Name = "%s"''' % (dataset_table, ob.name)
    # logger.sql(query)
    result = g.db.execute(query)

    (dataset_id,
     name,
     full_name,
     confidential,
     authorized_users) = result.fetchall()[0]

    if confidential:
        return True
