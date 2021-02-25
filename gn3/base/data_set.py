from redis import Redis

r = Redis()

DS_NAME_MAP = {}


def create_dataset(dataset_name, dataset_type=None, get_samplelist=True, group_name=None):
    return "hello"


class DatasetType:
	def  __init__(self,redis_instance):
		pass

# Do the intensive work at  startup one time only
Dataset_Getter = DatasetType(r)
