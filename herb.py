from saana_lib import optimizeHerb
from bson import ObjectId
import pdb

patient_id = ObjectId("5cb581403945895a51202ae2")
optimizeHerb.optimizeHerb(patient_id)
