
from flask import g
from redis import Redis
from gn3.utility.db_tools import escape
from gn3.base.webqtlCaseData import webqtlCaseData


def check_resource_availability(dataset, name=None):
    # should probably work on this has to do with authentication
    return {'data': ['no-access', 'view'], 'metadata': ['no-access', 'view'], 'admin': ['not-admin']}


def create_trait(**kw):
    # work on check resource availability deals with authentication
    assert bool(kw.get("dataset")) != bool(
        kw.get('dataset_name')), "Needs dataset ob. or name"

    assert bool(kw.get("name")), "Need trait name"

    if kw.get('dataset_name'):
        if kw.get('dataset_name') != "Temp":
            dataset = create_dataset(kw.get('dataset_name'))
    else:
        dataset = kw.get('dataset')

    if dataset.type == 'Publish':
        permissions = check_resource_availability(
            dataset, kw.get('name'))
    else:
        permissions = check_resource_availability(dataset)

    if "view" in permissions['data']:
        the_trait = GeneralTrait(**kw)
        print(f"the general trait is {the_trait}")
        if the_trait.dataset.type != "Temp":
            the_trait = retrieve_trait_info(
                the_trait,
                the_trait.dataset,
                get_qtl_info=kw.get('get_qtl_info'))


            return the_trait

    return None


class GeneralTrait:
    def __init__(self, get_qtl_info=False, get_sample_info=True, **kw):
        assert bool(kw.get('dataset')) != bool(
            kw.get('dataset_name')), "Needs dataset ob. or name"
        # Trait ID, ProbeSet ID, Published ID, etc.
        self.name = kw.get('name')
        if kw.get('dataset_name'):
            if kw.get('dataset_name') == "Temp":
                temp_group = self.name.split("_")[2]
                self.dataset = create_dataset(
                    dataset_name="Temp",
                    dataset_type="Temp",
                    group_name=temp_group)

            else:
                self.dataset = create_dataset(kw.get('dataset_name'))

        else:
            print("the dataset is described below here")
            self.dataset = kw.get("dataset")

        self.cellid = kw.get('cellid')
        self.identification = kw.get('identification', 'un-named trait')
        self.haveinfo = kw.get('haveinfo', False)
        self.sequence = kw.get('sequence')
        self.data = kw.get('data', {})
        self.view = True

        # Sets defaults
        self.locus = None
        self.lrs = None
        self.pvalue = None
        self.mean = None
        self.additive = None
        self.num_overlap = None
        self.strand_probe = None
        self.symbol = None
        self.display_name = self.name
        self.LRS_score_repr = "N/A"
        self.LRS_location_repr = "N/A"

        if kw.get('fullname'):
            name2 = value.split("::")
            if len(name2) == 2:
                self.dataset, self.name = name2

            elif len(name2) == 3:
                self.dataset, self.name, self.cellid = name2

        # Todo: These two lines are necessary most of the time, but
        # perhaps not all of the time So we could add a simple if
        # statement to short-circuit this if necessary
        if get_sample_info is not False:
            self = retrieve_sample_data(self, self.dataset)


def retrieve_sample_data(trait, dataset, samplelist=None):
    if samplelist is None:
        samplelist = []

    if dataset.type == "Temp":
        results = Redis.get(trait.name).split()

    else:
        results = dataset.retrieve_sample_data(trait.name)

    # Todo: is this necessary? If not remove
    trait.data.clear()

    if results:
        if dataset.type == "Temp":
            all_samples_ordered = dataset.group.all_samples_ordered()
            for i, item in enumerate(results):
                try:
                    trait.data[all_samples_ordered[i]] = webqtlCaseData(
                        all_samples_ordered[i], float(item))

                except Exception as e:
                    # should pass (added to enable testing)
                    raise e


        else:
            for item in results:
                name, value, variance, num_cases, name2 = item
                if not samplelist or (samplelist and name in samplelist):
                    trait.data[name] = webqtlCaseData(*item)

    return trait

        # raise NotImplementedError()


def get_resource_id(dataset, trait_name):
    return 1


def retrieve_trait_info(trait, dataset, get_qtl_info=False):
    assert dataset, "Dataset doesn't exist"

    the_url = None
    # some code should be added  added here

    try:
        response = requests.get(the_url).content
        trait_info = json.loads(response)
    except:  # ZS: I'm assuming the trait is viewable if the try fails for some reason; it should never reach this point unless the user has privileges, since that's dealt with in create_trait
        if dataset.type == 'Publish':
            query = """
                    SELECT
                            PublishXRef.Id, InbredSet.InbredSetCode, Publication.PubMed_ID,
                            CAST(Phenotype.Pre_publication_description AS BINARY),
                            CAST(Phenotype.Post_publication_description AS BINARY),
                            CAST(Phenotype.Original_description AS BINARY),
                            CAST(Phenotype.Pre_publication_abbreviation AS BINARY),
                            CAST(Phenotype.Post_publication_abbreviation AS BINARY), PublishXRef.mean,
                            Phenotype.Lab_code, Phenotype.Submitter, Phenotype.Owner, Phenotype.Authorized_Users,
                            CAST(Publication.Authors AS BINARY), CAST(Publication.Title AS BINARY), CAST(Publication.Abstract AS BINARY),
                            CAST(Publication.Journal AS BINARY), Publication.Volume, Publication.Pages,
                            Publication.Month, Publication.Year, PublishXRef.Sequence,
                            Phenotype.Units, PublishXRef.comments
                    FROM
                            PublishXRef, Publication, Phenotype, PublishFreeze, InbredSet
                    WHERE
                            PublishXRef.Id = %s AND
                            Phenotype.Id = PublishXRef.PhenotypeId AND
                            Publication.Id = PublishXRef.PublicationId AND
                            PublishXRef.InbredSetId = PublishFreeze.InbredSetId AND
                            PublishXRef.InbredSetId = InbredSet.Id AND
                            PublishFreeze.Id = %s
                    """ % (trait.name, dataset.id)

            trait_info = g.db.execute(query).fetchone()

        # XZ, 05/08/2009: Xiaodong add this block to use ProbeSet.Id to find the probeset instead of just using ProbeSet.Name
        # XZ, 05/08/2009: to avoid the problem of same probeset name from different platforms.
        elif dataset.type == 'ProbeSet':
            display_fields_string = ', ProbeSet.'.join(dataset.display_fields)
            display_fields_string = 'ProbeSet.' + display_fields_string
            query = """
                    SELECT %s
                    FROM ProbeSet, ProbeSetFreeze, ProbeSetXRef
                    WHERE
                            ProbeSetXRef.ProbeSetFreezeId = ProbeSetFreeze.Id AND
                            ProbeSetXRef.ProbeSetId = ProbeSet.Id AND
                            ProbeSetFreeze.Name = '%s' AND
                            ProbeSet.Name = '%s'
                    """ % (escape(display_fields_string),
                           escape(dataset.name),
                           escape(str(trait.name)))

            trait_info = g.db.execute(query).fetchone()
        # XZ, 05/08/2009: We also should use Geno.Id to find marker instead of just using Geno.Name
        # to avoid the problem of same marker name from different species.
        elif dataset.type == 'Geno':
            display_fields_string = ',Geno.'.join(dataset.display_fields)
            display_fields_string = 'Geno.' + display_fields_string
            query = """
                    SELECT %s
                    FROM Geno, GenoFreeze, GenoXRef
                    WHERE
                            GenoXRef.GenoFreezeId = GenoFreeze.Id AND
                            GenoXRef.GenoId = Geno.Id AND
                            GenoFreeze.Name = '%s' AND
                            Geno.Name = '%s'
                    """ % (escape(display_fields_string),
                           escape(dataset.name),
                           escape(trait.name))

            trait_info = g.db.execute(query).fetchone()
        else:  # Temp type
            query = """SELECT %s FROM %s WHERE Name = %s"""

            trait_info = g.db.execute(query,
                                      ','.join(dataset.display_fields),
                                      dataset.type, trait.name).fetchone()

    if trait_info:
        trait.haveinfo = True
        for i, field in enumerate(dataset.display_fields):
            holder = trait_info[i]
            if isinstance(holder, bytes):
                holder = holder.decode("utf-8", errors="ignore")
            setattr(trait, field, holder)

        if dataset.type == 'Publish':
            if trait.group_code:
                trait.display_name = trait.group_code + "_" + str(trait.name)

            trait.confidential = 0
            if trait.pre_publication_description and not trait.pubmed_id:
                trait.confidential = 1

            description = trait.post_publication_description

            # If the dataset is confidential and the user has access to confidential
            # phenotype traits, then display the pre-publication description instead
            # of the post-publication description
            trait.description_display = ""
            if not trait.pubmed_id:
                trait.abbreviation = trait.pre_publication_abbreviation
                trait.description_display = trait.pre_publication_description
            else:
                trait.abbreviation = trait.post_publication_abbreviation
                if description:
                    trait.description_display = description.strip()

            if not trait.year.isdigit():
                trait.pubmed_text = "N/A"
            else:
                trait.pubmed_text = trait.year

            if trait.pubmed_id:
                trait.pubmed_link = webqtlConfig.PUBMEDLINK_URL % trait.pubmed_id

        if dataset.type == 'ProbeSet' and dataset.group:
            description_string = trait.description
            target_string = trait.probe_target_description

            if str(description_string or "") != "" and description_string != 'None':
                description_display = description_string
            else:
                description_display = trait.symbol

            if (str(description_display or "") != "" and
                description_display != 'N/A' and
                    str(target_string or "") != "" and target_string != 'None'):
                description_display = description_display + '; ' + target_string.strip()

            # Save it for the jinja2 template
            trait.description_display = description_display

            trait.location_repr = 'N/A'
            if trait.chr and trait.mb:
                trait.location_repr = 'Chr%s: %.6f' % (
                    trait.chr, float(trait.mb))

        elif dataset.type == "Geno":
            trait.location_repr = 'N/A'
            if trait.chr and trait.mb:
                trait.location_repr = 'Chr%s: %.6f' % (
                    trait.chr, float(trait.mb))

        if get_qtl_info:
            # LRS and its location
            trait.LRS_score_repr = "N/A"
            trait.LRS_location_repr = "N/A"
            trait.locus = trait.locus_chr = trait.locus_mb = trait.lrs = trait.pvalue = trait.additive = ""
            if dataset.type == 'ProbeSet' and not trait.cellid:
                trait.mean = ""
                query = """
                        SELECT
                                ProbeSetXRef.Locus, ProbeSetXRef.LRS, ProbeSetXRef.pValue, ProbeSetXRef.mean, ProbeSetXRef.additive
                        FROM
                                ProbeSetXRef, ProbeSet
                        WHERE
                                ProbeSetXRef.ProbeSetId = ProbeSet.Id AND
                                ProbeSet.Name = "{}" AND
                                ProbeSetXRef.ProbeSetFreezeId ={}
                        """.format(trait.name, dataset.id)

                trait_qtl = g.db.execute(query).fetchone()
                if trait_qtl:
                    trait.locus, trait.lrs, trait.pvalue, trait.mean, trait.additive = trait_qtl
                    if trait.locus:
                        query = """
                            select Geno.Chr, Geno.Mb from Geno, Species
                            where Species.Name = '{}' and
                            Geno.Name = '{}' and
                            Geno.SpeciesId = Species.Id
                            """.format(dataset.group.species, trait.locus)

                        result = g.db.execute(query).fetchone()
                        if result:
                            trait.locus_chr = result[0]
                            trait.locus_mb = result[1]
                        else:
                            trait.locus = trait.locus_chr = trait.locus_mb = trait.additive = ""
                    else:
                        trait.locus = trait.locus_chr = trait.locus_mb = trait.additive = ""

            if dataset.type == 'Publish':
                query = """
                        SELECT
                                PublishXRef.Locus, PublishXRef.LRS, PublishXRef.additive
                        FROM
                                PublishXRef, PublishFreeze
                        WHERE
                                PublishXRef.Id = %s AND
                                PublishXRef.InbredSetId = PublishFreeze.InbredSetId AND
                                PublishFreeze.Id =%s
                """ % (trait.name, dataset.id)

                trait_qtl = g.db.execute(query).fetchone()
                if trait_qtl:
                    trait.locus, trait.lrs, trait.additive = trait_qtl
                    if trait.locus:
                        query = """
                            select Geno.Chr, Geno.Mb from Geno, Species
                            where Species.Name = '{}' and
                            Geno.Name = '{}' and
                            Geno.SpeciesId = Species.Id
                            """.format(dataset.group.species, trait.locus)

                        result = g.db.execute(query).fetchone()
                        if result:
                            trait.locus_chr = result[0]
                            trait.locus_mb = result[1]
                        else:
                            trait.locus = trait.locus_chr = trait.locus_mb = trait.additive = ""
                    else:
                        trait.locus = trait.locus_chr = trait.locus_mb = trait.additive = ""
                else:
                    trait.locus = trait.lrs = trait.additive = ""
            if (dataset.type == 'Publish' or dataset.type == "ProbeSet") and str(trait.locus_chr or "") != "" and str(trait.locus_mb or "") != "":
                trait.LRS_location_repr = LRS_location_repr = 'Chr%s: %.6f' % (
                    trait.locus_chr, float(trait.locus_mb))
                if str(trait.lrs or "") != "":
                    trait.LRS_score_repr = LRS_score_repr = '%3.1f' % trait.lrs
    else:
        raise KeyError(repr(trait.name) +
                       ' information is not found in the database.')
    return trait
