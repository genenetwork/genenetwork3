
import json
import requests
from redis import Redis

r = Redis()

# move  this to configuration file
GN2_BASE_URL = "https://genenetwork.org/"

DS_NAME_MAP = {}


def create_dataset(dataset_name, dataset_type=None, get_samplelist=True, group_name=None):
    return "hello"


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

            return self.datasets.get(name, None)


            # Do the intensive work at  startup one time only
Dataset_Getter = DatasetType(r)
